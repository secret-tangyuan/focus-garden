#!/usr/bin/env python3
"""渲染生产 nginx 配置 + 安全响应头片段。

- 从构建产物 index.html 里取出所有「内联可执行脚本」，逐个算 sha256 哈希，
  写进 CSP 的 script-src（不用 unsafe-inline）。
- 模板里的占位符全部来自 deploy/env/prod.env（该文件不入库，仓库里只有 .example），
  脚本本身不写死任何域名、路径或证书位置 —— 公开仓不泄露部署细节。

用法：python3 scripts/render_prod_conf.py <dist目录> <输出nginx配置> <输出头片段> [env文件]
"""

import base64
import hashlib
import os
import re
import sys

dist = sys.argv[1] if len(sys.argv) > 1 else ".output/public"
out_conf = sys.argv[2] if len(sys.argv) > 2 else "_focus-prod.conf"
out_snippet = sys.argv[3] if len(sys.argv) > 3 else "_focus-headers.conf"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_DIR = os.path.join(ROOT, "deploy", "env")

env_path = sys.argv[4] if len(sys.argv) > 4 else os.path.join(ENV_DIR, "prod.env")
if not os.path.exists(env_path):
    env_path = os.path.join(ENV_DIR, "prod.env.example")
    print("提示：找不到 prod.env，改用样例文件渲染（地址为占位符）")


def load_env(path):
    """读 KEY=VALUE 格式的配置（# 开头为注释）"""
    env = {}
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


ENV = load_env(env_path)

REQUIRED = [
    "FOCUS_HOST",
    "SITE_ROOT",
    "BACKEND_ORIGIN",
    "IDENTITY_BASE_URL",
    "IDENTITY_API_LOGIN",
    "IDENTITY_API_SESSION",
    "IDENTITY_API_LOGOUT",
    "IDENTITY_API_RENEW",
    "IDENTITY_PREFIX",
    "SSL_CERT",
    "SSL_KEY",
]

missing = [key for key in REQUIRED if not ENV.get(key)]
if missing:
    raise SystemExit(f"配置缺少以下项：{', '.join(missing)}（来源：{env_path}）")

PROD = {
    "__FOCUS_HOST__": ENV["FOCUS_HOST"],
    "__SITE_ROOT__": ENV["SITE_ROOT"],
    "__BACKEND_ORIGIN__": ENV["BACKEND_ORIGIN"],
    "__IDENTITY_BASE_URL__": ENV["IDENTITY_BASE_URL"],
    "__IDENTITY_API_LOGIN__": ENV["IDENTITY_API_LOGIN"],
    "__IDENTITY_API_SESSION__": ENV["IDENTITY_API_SESSION"],
    "__IDENTITY_API_LOGOUT__": ENV["IDENTITY_API_LOGOUT"],
    "__IDENTITY_API_RENEW__": ENV["IDENTITY_API_RENEW"],
    "__IDENTITY_PREFIX__": ENV["IDENTITY_PREFIX"],
    "__SSL_CERT__": ENV["SSL_CERT"],
    "__SSL_KEY__": ENV["SSL_KEY"],
}


def inline_script_hashes():
    """index.html 里所有内联脚本（没有 src、没有 type）的 sha256 哈希。"""
    path = os.path.join(dist, "index.html")
    if not os.path.exists(path):
        return []

    html = open(path, encoding="utf-8").read()
    hashes = []

    for match in re.finditer(r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", html, re.S):
        attrs = match.group("attrs")
        body = match.group("body")
        if "src=" in attrs or 'type="' in attrs:
            continue
        digest = base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode()
        hashes.append("'sha256-%s'" % digest)

    return hashes


def render(text: str, extra: dict) -> str:
    for key, value in {**PROD, **extra}.items():
        text = text.replace(key, value)
    return text


hashes = inline_script_hashes()
hashes_text = (" ".join(hashes)) if hashes else "'unsafe-inline'"
print("内联脚本哈希:", hashes_text)

template = open(os.path.join(ROOT, "deploy/nginx/prod.conf.template"), encoding="utf-8").read()
snippet_tpl = open(os.path.join(ROOT, "deploy/nginx/focus-headers.conf"), encoding="utf-8").read()

open(out_conf, "w", encoding="utf-8").write(render(template, {}))
open(out_snippet, "w", encoding="utf-8").write(render(snippet_tpl, {"__CSP_SCRIPT_HASHES__": hashes_text}))
print("已写出:", out_conf, out_snippet)

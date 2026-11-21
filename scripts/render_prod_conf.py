#!/usr/bin/env python3
"""渲染生产 nginx 配置 + 安全响应头片段。

- 从构建产物 index.html 里取出所有「内联可执行脚本」，逐个算 sha256 哈希，
  写进 CSP 的 script-src（不用 unsafe-inline）。
- 模板里的占位符来自 deploy/env/prod.env。

用法：python3 scripts/render_prod_conf.py <dist目录> <输出nginx配置> <输出头片段>
"""
import base64
import hashlib
import os
import re
import sys

dist = sys.argv[1] if len(sys.argv) > 1 else ".output/public"
out_conf = sys.argv[2] if len(sys.argv) > 2 else "_focus-prod.conf"
out_snippet = sys.argv[3] if len(sys.argv) > 3 else "_focus-headers.conf"

PROD = {
    "__FOCUS_HOST__": "focus.secret-tangyuan.com",
    "__SITE_ROOT__": "/var/www/focus-garden/dist",
    "__BACKEND_ORIGIN__": "http://127.0.0.1:8080",
    "__IDENTITY_API_LOGIN__": "/auth/login",
    "__IDENTITY_API_SESSION__": "/auth/session",
    "__IDENTITY_API_LOGOUT__": "/auth/logout",
    "__IDENTITY_API_RENEW__": "/auth/renew",
    "__IDENTITY_PREFIX__": "/auth",
    "__IDENTITY_BASE_URL__": "https://auth.secret-tangyuan.com",
    "__SSL_CERT__": "/etc/letsencrypt/live/secret-tangyuan.com-wildcard/fullchain.pem",
    "__SSL_KEY__": "/etc/letsencrypt/live/secret-tangyuan.com-wildcard/privkey.pem",
}


def inline_script_hashes() -> list[str]:
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


root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template = open(os.path.join(root, "deploy/nginx/prod.conf.template"), encoding="utf-8").read()
snippet_tpl = open(os.path.join(root, "deploy/nginx/focus-headers.conf"), encoding="utf-8").read()

hashes = inline_script_hashes()
hashes_text = (" ".join(hashes)) if hashes else "'unsafe-inline'"
print("内联脚本哈希:", hashes_text)

open(out_conf, "w", encoding="utf-8").write(render(template, {}))
open(out_snippet, "w", encoding="utf-8").write(render(snippet_tpl, {"__CSP_SCRIPT_HASHES__": hashes_text}))
print("已写出:", out_conf, out_snippet)

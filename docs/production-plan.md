# 专注学习站 · 上生产计划

底座：FocusTide（MIT）改造。目标域名：**focus.secret-tangyuan.com**。

## 0. 现在到哪了

| 项 | 状态 |
|---|---|
| 功能与本地验收 | ✅ 本地 26/26（`scripts/verify_ui.py`） |
| GitHub 公开仓 | ⬜ 待建（`secret-tangyuan/focus-garden`，public） |
| 域名解析 | ⬜ 待建（Cloudflare A 记录 → ECS） |
| 身份中心登记本站 | ✅ 代码已改（`SITES` 增加 focus 站），⬜ 待上生产 |
| 服务器 nginx + 目录 | ⬜ 待做（模板已备：`deploy/nginx/prod.conf.template`） |
| 构建与发布脚本 | ⬜ 待做（照 auth-center 的套路：备份 → 原子切 → 重启 → 验收） |

## 1. 公开仓库（先做，风险最低）

1. `git rm --cached deploy/env/local.env`，仓库只留 `*.env.example`
2. 验收脚本里的测试账号口令改成读环境变量（`FOCUS_TEST_USER` / `FOCUS_TEST_PASSWORD`），仓库里不留任何真实凭据
3. `LICENSE`（上游 MIT）与 `NOTICE.md`（改造说明 + 上游作者署名）保持完整
4. 建仓 `secret-tangyuan/focus-garden`，**public**，默认分支 `main`
5. 远端保留 `upstream` = Hanziness/FocusTide，方便日后同步上游

## 2. 身份中心（auth-center）上生产

1. 代码已改：`app/config.py` 的 `SITES` 增加
   - `focus.secret-tangyuan.com`（专注学习，凭证型）
   - 本地 `focus.secret-tangyuan.test`（仅本地）
2. 部署：备份 → 覆盖 `app/` → `systemctl restart auth-center` → 验收 `/auth/zone`、登录回跳
3. 部署后在管理面板「站点权限」里给本站建一条规则（凭证型默认允许；要用「保护型」就单独设）
4. 回滚点：`/var/backups/web-deploy/<TS>-focus-site/`

## 3. DNS 与证书

1. Cloudflare 加 `focus.secret-tangyuan.com` → A 记录指向 ECS（47.108.28.117），**先灰云**跑通再开橙云
2. 证书：certbot 或 Cloudflare Origin 证书，二选一；模板里 `__SSL_CERT__` / `__SSL_KEY__` 从配置读

## 4. 服务器部署

1. 目录：`/var/www/focus-garden/dist`（静态产物），nginx 配置 `/etc/nginx/sites-available/focus-garden.conf`
2. 构建：在本地/WSL 出静态包（`npm run generate`，`NUXT_PUBLIC_AUTH_BASE_URL=https://auth.secret-tangyuan.com`）→ 传到服务器 `dist.next` → 原子切换 `dist`
3. `nginx -t && systemctl reload nginx`
4. 回滚点：切换前把当前 `dist` 备份到 `/var/backups/web-deploy/<TS>-focus-garden/`

## 5. 登录 API 的隐藏（只放行必要路径）

- nginx 只精确放行三条：**登录 / 会话 / 退出**，其余 `/auth/*` 一律 `404`（模板已写好）
- 前端不暴露后端路径前缀：前缀写在 `deploy/env/prod.env` 的 `AUTH_PROXY_PREFIX`，不入库
- 身份中心后端本身只监听 `127.0.0.1:8080`，不直接对外
- CSP：`default-src 'self'`，`connect-src 'self'`（只回本站），`frame-ancestors 'none'`
- 登录失败节流由身份中心负责（按用户 + IP）

## 6. 验收清单（上线后逐条过）

- [ ] 首页 200，首屏能进「进入全屏专注」
- [ ] 入口页右上角「打开设置」「登录」可点
- [ ] 精简版登录能登进去，顶栏显示用户名
- [ ] `/auth/session` 返回已登录；`/auth/xxx`（未放行路径）返回 404
- [ ] 退出全屏会被拦、失焦会暂停、回到全屏自动继续
- [ ] 完成一段专注会种树、记录进「记录」页
- [ ] 手机宽度下布局不塌
- [ ] CSP 生效且控制台无报错

## 7. 回滚

- 静态站：把备份目录里的 `dist` 换回来 + `nginx -t && reload`
- 身份中心：把 `app/` 换回备份 + `systemctl restart auth-center`
- DNS：删 A 记录或改回旧值

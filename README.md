# 秘密小汤圆 · 专注学习（focus-garden）

强制全屏的专注学习计时器：**倒计时 + 种树 + 专注/登录记录**。

> 本项目基于 **FocusTide**（MIT，原作者 Imre Gera）改造，植物美术移植自 **FocusGrove**
> （MIT，作者 Hamin Yovan Antony）。三方署名与许可说明见 `NOTICE.md`。

## 功能

| 功能 | 说明 |
|---|---|
| 强制全屏 | 进入专注即请求全屏；计时途中退出全屏会被遮罩拦住，点「回到全屏」自动继续（可选择退出即暂停） |
| 失焦暂停 | 切窗口 / 切标签页（失去焦点）自动暂停计时，并提示「已暂停计时」 |
| 秒级计时 | 计时显示到秒（mm:ss），随时能看到还剩多少时间 |
| 面板打扰提醒 | 专注进行中，点「设置」「我的森林」「登录」会先在按钮旁弹小窗确认：**点击可能会干扰注意力，建议不要点击**；不在专注中则直接打开 |
| 精简版登录 | 入口页右上角就能登录：只有用户名 + 密码的小窗，贴在按钮旁，不遮挡整页；注册 / 忘记密码在完整登录页 |
| 倒计时 | 专注 15/25/45/60/90 分钟、休息 5/10/15 分钟一键切换；沿用 FocusTide 的番茄钟节奏与音效 |
| 种树 | 每完成一段专注种下一棵树；树种轮换（阔叶 / 针叶 / 樱花），树会随之后的专注次数逐级长大 |
| 专注记录 | 最近 7 天柱状图、每次专注的时长与完成情况 |
| 登录记录 | 每次进入专注模式都留一条登录记录（时间） |
| 界面 | 纯色背景 + 格子，主色 `#bbddff`；关于页并列署名秘密小汤圆、Imre Gera、Hamin Yovan Antony |

## 身份服务（可选）

站点可以接入统一身份，实现「精简版登录」（用户名 + 密码的小窗，贴在按钮旁）。
**接入是可选的**：不配置身份服务时登录入口自动隐藏，其余功能照常。

所有地址与端点都通过环境变量注入，仓库里不出现任何真实地址与接口细节：

| 环境变量 | 用途 |
|---|---|
| `IDENTITY_BASE_URL` | 完整登录页（注册 / 找回密码）的入口 |
| `IDENTITY_API_LOGIN` | 登录端点 |
| `IDENTITY_API_SESSION` | 会话查询端点 |
| `IDENTITY_API_LOGOUT` | 退出端点 |
| `IDENTITY_PREFIX` | nginx 里除上述三条外一律 404 的前缀 |

## 本地开发（WSL 测试环境）

    # 同步 → 构建 → 发布到本地测试目录 → 重载 nginx
    bash scripts/build_wsl_test_env.sh

入口：见 `deploy/env/local.env` 里的 `FOCUS_BASE_URL`

地址只有一个来源：`deploy/env/local.env`（或 `prod.env`），改地址只改这个文件，仓库里只留 `*.env.example`。

## 验收脚本（真实浏览器）

    FOCUS_TEST_USER=<账号> FOCUS_TEST_PASSWORD=<口令> python3 scripts/verify_ui.py

覆盖 58 项：进入页、时长滑块、时分秒显示、沉浸模式与边缘唤出、灵动岛通知分级
（专注中只保留关键通知，其余延后补发）、独立窗口点击外部关闭、种树与花园、
登录/退出与云端同步、三方署名与源码跳转。

验收截图输出到本地 `shots/`（已加入 .gitignore，不入库）。

## 目录

    components/focus/     强制全屏门、全屏守卫、快捷倒计时
    components/garden/    森林面板、树的 SVG、种树提示
    stores/garden.ts      树与统计
    stores/history.ts     专注记录 / 登录记录
    stores/focusMode.ts   全屏运行时状态
    deploy/               地址配置与 nginx 模板
    scripts/              构建脚本与 UI 验收脚本

## 许可证

本站原创部分采用 Apache-2.0；FocusTide 与 FocusGrove 的 MIT 许可和署名完整保留，
见 `LICENSE`、`NOTICE.md` 与 `licenses/`。

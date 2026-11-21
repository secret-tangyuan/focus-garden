# 秘密小汤圆 · 专注学习（focus-garden）

强制全屏的专注学习计时器：**倒计时 + 种树 + 专注/登录记录**。

> 本项目基于开源项目 **FocusTide**（MIT License）改造。
> 上游：https://github.com/Hanziness/FocusTide · 原作者 Imre Gera
> 原项目的 MIT 许可证完整保留在仓库根目录 `LICENSE`，改造说明见 `NOTICE.md`。

## 功能

| 功能 | 说明 |
|---|---|
| 强制全屏 | 进入专注即请求全屏；计时途中退出全屏会被遮罩拦住，点「回到全屏」自动继续（可选择退出即暂停） |
| 失焦暂停 | 切窗口 / 切标签页（失去焦点）自动暂停计时，并提示「已暂停计时」 |
| 秒级计时 | 计时显示到秒（mm:ss），随时能看到还剩多少时间 |
| 面板打扰提醒 | 点「设置」或「我的森林」先弹出确认：**点击可能会干扰注意力，建议不要点击**，需二次确认才打开 |
| 倒计时 | 专注 15/25/45/60/90 分钟、休息 5/10/15 分钟一键切换；沿用 FocusTide 的番茄钟节奏与音效 |
| 种树 | 每完成一段专注种下一棵树；树种轮换（阔叶 / 针叶 / 樱花），树会随之后的专注次数逐级长大 |
| 专注记录 | 最近 7 天柱状图、每次专注的时长与完成情况 |
| 登录记录 | 每次进入专注模式都留一条登录记录（时间） |
| 界面 | 纯色背景 + 格子，主色 `#bbddff`；关于页为双作者（左：秘密小汤圆，右：FocusTide 原作者 Imre Gera）；数据存在浏览器 localStorage |

## 本地开发（WSL 测试环境）

    # 同步 → 构建 → 发布到 /srv/stage → 重载 nginx
    bash /srv/src/focus-garden/scripts/build_wsl_test_env.sh

入口：http://focus.secret-tangyuan.test/

地址只有一个来源：`deploy/env/local.env`（`FOCUS_BASE_URL` / `FOCUS_HOST`），改地址只改这个文件。

## 验收脚本（真实浏览器）

    python3 scripts/verify_ui.py

覆盖 20 项：进入页、快捷倒计时、秒级计时、种树提示、森林面板、登录/专注记录、
退出全屏拦截 + 回到全屏自动继续、失焦自动暂停、打开面板前的提醒、设置页文案完整性、关于页双作者。

## 目录

    components/focus/     强制全屏门、全屏守卫、快捷倒计时
    components/garden/    森林面板、树的 SVG、种树提示
    stores/garden.ts      树与统计
    stores/history.ts     专注记录 / 登录记录
    stores/focusMode.ts   全屏运行时状态
    deploy/               地址配置与 nginx 模板
    scripts/              构建脚本与 UI 验收脚本

## 许可证

上游 FocusTide 为 MIT；本改造同样以 MIT 发布，见 `LICENSE` 与 `NOTICE.md`。

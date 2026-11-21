# NOTICE

本项目（秘密小汤圆 · 专注学习 / focus-garden）基于以下开源项目改造：

- **FocusTide** — https://github.com/Hanziness/FocusTide
  - Copyright (c) Imre Gera
  - 许可证：MIT License（完整文本见 `LICENSE`）
  - 原作者说明：本项目为「现代、简洁、浏览器里的番茄钟」

## 改造内容

1. 新增「专注模式」：强制全屏、退出全屏拦截与自动暂停（`stores/focusMode.ts`、`components/focus/`）
2. 新增「种树」：完成一段专注种一棵树，树随专注次数长大（`stores/garden.ts`、`components/garden/`）
3. 新增「专注记录 / 登录记录」面板与最近 7 天统计（`stores/history.ts`）
4. 新增快捷倒计时（专注 / 休息时长一键切换）（`components/focus/quickPresets.vue`）
5. 视觉：纯色背景 + 格子，主色 `#bbddff`，去掉 Google Fonts 外链，改用系统字体
6. 默认语言改为简体中文，移除首次运行的引导教程，站点标题改为「秘密小汤圆 · 专注学习」

MIT 许可证允许上述使用、复制、修改、合并、发布、再分发与销售，条件是保留版权声明与许可声明。

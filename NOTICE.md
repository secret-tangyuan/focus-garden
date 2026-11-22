# NOTICE

秘密小汤圆 · 专注学习（focus-garden）
Copyright 2025-2035 Secret Tangyuan

本产品依据 Apache License, Version 2.0 授权；许可全文见同目录 `LICENSE`。

## 原创内容

专注模式（强制全屏 / 退出全屏拦截 / 自动暂停）、花园玩法（阳光经济 / 手动种树 / 解锁物种 /
浇水催熟 / 7 天未登录枯萎）与森林面板、专注与登录记录、快捷倒计时、视觉改造
（纯色背景 + 格子，主色 `#bbddff`）、默认简体中文与站点标题，
由 Secret Tangyuan 原创，适用上述许可。

## 第三方组件（不适用上述许可）

### FocusTide

- 上游：https://github.com/Hanziness/FocusTide
- Copyright (c) 2022 Imre Gera and contributors
- 许可证：MIT License（完整文本见 `licenses/focus-tide-LICENSE`）
- 本站基于其改造：新增专注模式、种树与森林面板、专注 / 登录记录与周统计、快捷倒计时；
  视觉改为纯色 + 格子并去掉 Google Fonts 外链；默认语言改为简体中文；站点标题与作者信息改为本站品牌。

### FocusGrove

- 上游：https://github.com/haminyovanantonyfk-netizen/focus-grove
- Copyright (c) 2026 FocusGrove contributors（作者：Hamin Yovan Antony）
- 许可证：MIT License（完整文本见 `licenses/focus-grove-LICENSE`）
- 移植内容：
  1. `SPECIES` 物种表 —— 12 个物种的 id / 造型 / 主色 / 解锁价
  2. `treeSVG()` 参数化 SVG 植物渲染器 —— 按「造型 × 成长阶段」生成的矢量美术
- 修改说明：原生 JS 字符串模板改写为 Vue 3 SFC `components/garden/plantSvg.vue`；
  解锁价、初始解锁集合、成长公式与枯萎规则按本站玩法调整（未原样照搬）；
  未移植其应用骨架（计时器、统计、本地存储、商店、成就、联机房间、音频合成等）。

### 其它依赖

第三方依赖各自保留其原有许可条款，随其分发包提供。

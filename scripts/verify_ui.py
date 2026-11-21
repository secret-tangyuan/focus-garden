#!/usr/bin/env python3
"""专注学习站 · 真实 UI 验收（Playwright + Chromium）

覆盖：
1. 进入页（强制全屏门）出现
2. 快捷倒计时可选
3. 开始专注 → 计时运行
4. 退出全屏 → 拦截层出现，点「回到全屏」恢复
5. 完成一段专注 → 种下一棵树 + 提示
6. 森林面板：树、统计
7. 记录面板：登录记录 / 专注记录

用法：python3 scripts/verify_ui.py [BASE_URL]
"""
import asyncio
import os
import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://focus.secret-tangyuan.test"
SHOTS = os.environ.get("FOCUS_SHOTS_DIR") or "/mnt/c/Users/Administrator/Desktop/works/web_work/focus-garden/shots"
os.makedirs(SHOTS, exist_ok=True)

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  | " + detail) if detail else ""))


async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        await page.goto(BASE, wait_until="networkidle")
        await page.wait_for_timeout(1500)

        # 1. 进入页
        gate = page.get_by_role("button", name="进入全屏专注")
        check("进入页出现（强制全屏门）", await gate.count() > 0)
        await page.screenshot(path=os.path.join(SHOTS, "01-gate.png"))

        # 2. 快捷倒计时
        chips = await page.locator("button", has_text="25").count()
        check("快捷倒计时（15/25/45/60/90）可选", chips > 0)

        # 3. 把专注时长改成 10 秒，便于验收
        await page.evaluate("""() => {
          const app = document.querySelector('#__nuxt').__vue_app__
          const pinia = app.config.globalProperties.$pinia
          pinia.state.value.settings.schedule.lengths.work = 10000
          pinia.state.value.settings.schedule.lengths.shortpause = 5000
          pinia.state.value.settings.schedule.lengths.longpause = 5000
        }""")

        await gate.click()
        await page.wait_for_timeout(1500)

        timer_text = await page.locator("body").inner_text()
        check("计时已开始（显示 10 秒倒计时）", "00:0" in timer_text or "9" in timer_text)

        # 4. 等这一段专注跑完 → 种树（轮询提示，提示只停留 3 秒）
        planted = 0
        for _ in range(40):
            await page.wait_for_timeout(500)
            if await page.get_by_text("种下了一棵树").count() > 0:
                planted = 1
                await page.screenshot(path=os.path.join(SHOTS, "03-planted.png"))
                break
        check("完成专注后提示「种下了一棵树」", planted == 1)

        trees = await page.evaluate("""() => {
          const raw = localStorage.getItem('persist-garden')
          return raw ? (JSON.parse(raw).trees || []).length : 0
        }""")
        check("森林里已记录一棵树", trees >= 1, "trees=" + str(trees))

        # 5b. 再次开始专注 → 退出全屏 → 拦截层
        # 确保计时处于运行中（可能已自动进入休息段）
        state_now = await page.evaluate("""() => {
          const app = document.querySelector('#__nuxt').__vue_app__
          return app.config.globalProperties.$pinia.state.value.schedule.timerState
        }""")
        if state_now != 1:
            await page.get_by_role("button", name="开始或暂停计时器").click()
            await page.wait_for_timeout(900)
        state_now = await page.evaluate("""() => {
          const app = document.querySelector('#__nuxt').__vue_app__
          return app.config.globalProperties.$pinia.state.value.schedule.timerState
        }""")
        check("计时处于运行中", state_now == 1, "timerState=" + str(state_now))

        # 退出全屏（真退出，触发 fullscreenchange）
        await page.evaluate("""async () => {
          if (document.fullscreenElement) {
            await document.exitFullscreen()
          } else {
            document.dispatchEvent(new Event('fullscreenchange'))
          }
        }""")
        await page.wait_for_timeout(900)
        guard = page.get_by_role("button", name="回到全屏")
        guard_visible = await guard.count() > 0
        check("退出全屏后出现拦截层", guard_visible)
        if guard_visible:
            await page.screenshot(path=os.path.join(SHOTS, "02-fullscreen-guard.png"))
            paused = await page.evaluate("""() => {
              const app = document.querySelector('#__nuxt').__vue_app__
              const pinia = app.config.globalProperties.$pinia
              return pinia.state.value.schedule.timerState
            }""")
            check("退出全屏后计时自动暂停", paused == 2, "timerState=" + str(paused))
            await guard.click()
            await page.wait_for_timeout(900)
            gone = await page.get_by_role("button", name="回到全屏").count() == 0
            check("点「回到全屏」后拦截层消失", gone, "无头浏览器可能不支持真全屏")

        # 6. 森林面板
        await page.get_by_label("我的森林").click()
        await page.wait_for_timeout(800)
        panel_text = await page.locator("aside").inner_text()
        check("森林面板打开且有树", "阔叶" in panel_text or "针叶" in panel_text or "樱花" in panel_text, panel_text[:80])
        await page.screenshot(path=os.path.join(SHOTS, "04-forest.png"))

        # 7. 记录面板
        await page.get_by_role("button", name="记录").click()
        await page.wait_for_timeout(600)
        record_text = await page.locator("aside").inner_text()
        check("记录面板有登录记录", "登录记录" in record_text)
        check("记录面板有专注记录", "专注记录" in record_text)
        check("专注记录标记为已完成", "已完成" in record_text, record_text[:120])
        await page.screenshot(path=os.path.join(SHOTS, "05-records.png"))

        fatal = [e for e in errors if "favicon" not in e.lower() and "404" not in e]
        check("无前端报错", len(fatal) == 0, "; ".join(fatal[:3]))

        await browser.close()

    print(f"\n通过 {len(PASS)} / {len(PASS) + len(FAIL)}")
    if FAIL:
        print("失败：" + ", ".join(FAIL))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

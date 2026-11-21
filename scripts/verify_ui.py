#!/usr/bin/env python3
"""专注学习站 · 真实 UI 验收（Playwright + Chromium）

覆盖：进入页 / 快捷倒计时 / 秒级计时 / 计时 / 退出全屏拦截 + 自动暂停 /
      失焦自动暂停 / 种树 / 森林面板 / 登录与专注记录 /
      打开面板前的提醒 / 设置页文案完整性

用法：python3 scripts/verify_ui.py [BASE_URL]
"""
import asyncio
import os
import re
import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://focus.secret-tangyuan.test"
SHOTS = os.environ.get("FOCUS_SHOTS_DIR") or "/mnt/c/Users/Administrator/Desktop/works/web_work/focus-garden/shots"
os.makedirs(SHOTS, exist_ok=True)

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(("  PASS  " if ok else "  FAIL  ") + name + (("  | " + detail) if detail else ""))


def timer_state(page):
    return page.evaluate("""() => {
      const app = document.querySelector('#__nuxt').__vue_app__
      return app.config.globalProperties.$pinia.state.value.schedule.timerState
    }""")


async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--no-sandbox"])
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

        # 4. 秒级显示
        body_text = await page.locator("body").inner_text()
        display_text = re.sub(r"\s+", "", await page.locator(".timer-display").first.inner_text())
        check("计时显示到秒（mm:ss）", re.fullmatch(r"\d{4}", display_text) is not None, display_text)

        # 5. 等这一段专注跑完 → 种树
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

        # 6. 退出全屏 → 拦截层（计时运行中）
        state_now = await timer_state(page)
        if state_now != 1:
            await page.get_by_role("button", name="开始或暂停计时器").click()
            await page.wait_for_timeout(900)
        await page.evaluate("""async () => {
          if (document.fullscreenElement) { await document.exitFullscreen() }
        }""")
        await page.wait_for_timeout(900)
        guard = page.get_by_role("button", name="回到全屏")
        guard_visible = await guard.count() > 0
        check("退出全屏后出现拦截层", guard_visible)
        if guard_visible:
            await page.screenshot(path=os.path.join(SHOTS, "02-fullscreen-guard.png"))
            await guard.click()
            await page.wait_for_timeout(900)
            check("点「回到全屏」后拦截层消失", await page.get_by_role("button", name="回到全屏").count() == 0)
            check("点「回到全屏」后计时自动继续", await timer_state(page) == 1)

        # 7. 失焦自动暂停
        await page.evaluate("() => { window.dispatchEvent(new Event('blur')) }")
        await page.wait_for_timeout(700)
        check("失去焦点后计时自动暂停", await timer_state(page) == 2)
        check("失焦提示出现", await page.get_by_text("已暂停计时").count() > 0)
        await page.screenshot(path=os.path.join(SHOTS, "06-blur-pause.png"))

        # 8. 打开面板前先询问
        await page.get_by_label("我的森林").click()
        await page.wait_for_timeout(600)
        body_text = await page.locator("body").inner_text()
        check("点「我的森林」先弹出提醒", "点击可能会干扰注意力" in body_text)
        await page.screenshot(path=os.path.join(SHOTS, "07-distract-guard.png"))
        await page.get_by_role("button", name="不了", exact=True).click()
        await page.wait_for_timeout(500)
        check("选「不了」则不打开面板", await page.locator("aside").first.is_visible() is False)

        await page.get_by_label("我的森林").click()
        await page.wait_for_timeout(500)
        await page.get_by_role("button", name="仍然打开").click()
        await page.wait_for_timeout(700)

        # 9. 森林面板
        panel_text = await page.locator("aside").inner_text()
        check("森林面板打开且有树", "阔叶" in panel_text or "针叶" in panel_text or "樱花" in panel_text)
        await page.screenshot(path=os.path.join(SHOTS, "04-forest.png"))

        # 10. 记录面板
        await page.get_by_role("button", name="记录").click()
        await page.wait_for_timeout(600)
        record_text = await page.locator("aside").inner_text()
        check("记录面板有登录记录", "登录记录" in record_text)
        check("记录面板有专注记录", "专注记录" in record_text)
        check("专注记录标记为已完成", "已完成" in record_text)
        await page.screenshot(path=os.path.join(SHOTS, "05-records.png"))

        # 先关掉森林面板，避免遮挡设置按钮
        await page.locator("aside").get_by_label("关闭").click()
        await page.wait_for_timeout(500)

        # 11. 设置页文案完整性（不能出现未匹配的 key）
        await page.get_by_label("设置").click()
        await page.wait_for_timeout(600)
        await page.get_by_role("button", name="仍然打开").click()
        await page.wait_for_timeout(800)
        settings_text = await page.locator("body").inner_text()
        raw_keys = re.findall(r"settings\.values\.[\w.]+|\b_[a-zA-Z]+\b", settings_text)
        check("设置页没有未匹配的翻译键", len(raw_keys) == 0, ", ".join(raw_keys[:3]))
        check("设置页有中文条目（如「段落结束」）", "段落结束" in settings_text)
        await page.screenshot(path=os.path.join(SHOTS, "08-settings.png"))

        # 12. 关于页双作者
        await page.get_by_role("tab", name="关于").click()
        await page.wait_for_timeout(600)
        about_text = await page.locator("body").inner_text()
        check("关于页显示双作者（秘密小汤圆 + FocusTide）",
              "秘密小汤圆" in about_text and "FocusTide" in about_text)
        await page.screenshot(path=os.path.join(SHOTS, "09-about.png"))

        fatal = [e for e in errors if "favicon" not in e.lower() and "404" not in e]
        check("无前端报错", len(fatal) == 0, "; ".join(fatal[:3]))

        await browser.close()

    print(f"\n通过 {len(PASS)} / {len(PASS) + len(FAIL)}")
    if FAIL:
        print("失败：" + ", ".join(FAIL))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

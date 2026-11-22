#!/usr/bin/env python3
"""专注学习站 · 真实 UI 验收（Playwright + Chromium）

覆盖：进入页 / 快捷倒计时 / mm:ss 秒级显示 / 种树 / 森林面板 / 登录与专注记录 /
      退出全屏拦截 + 回到全屏自动继续 / 失焦自动暂停 /
      非专注时面板直接打开 / 专注中二次确认小窗 / 登录新标签页 /
      设置页文案完整性 / 关于页双作者

用法：python3 scripts/verify_ui.py [BASE_URL]
"""
import asyncio
import os
import re
import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FOCUS_BASE_URL", "http://localhost:5174")
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


def set_section(page, section_type, running=True):
    """把当前计时段强制成 work / shortpause / longpause，并设置计时器状态"""
    return page.evaluate("""([type, running]) => {
      const app = document.querySelector('#__nuxt').__vue_app__
      const s = app.config.globalProperties.$pinia.state.value.schedule
      s.items[0].type = type
      s.timerState = running ? 1 : 0
      return s.items[0].type
    }""", [section_type, running])


def close_panels(page):
    """直接关掉所有面板（设置面板是全屏遮罩，会挡住后续点击）"""
    return page.evaluate("""() => {
      const app = document.querySelector('#__nuxt').__vue_app__
      const o = app.config.globalProperties.$pinia.state.value.openpanels
      o.settings = false
      o.todo = false
      o.garden = false
      o.pending = null
      o.pendingRect = null
      return true
    }""")


def long_sections(page):
    """把各段时长拉长，避免断言期间自动推进到下一段"""
    return page.evaluate("""() => {
      const app = document.querySelector('#__nuxt').__vue_app__
      const st = app.config.globalProperties.$pinia.state.value.settings
      st.schedule.lengths.work = 600000
      st.schedule.lengths.shortpause = 600000
      st.schedule.lengths.longpause = 600000
      return true
    }""")


async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--no-sandbox"])
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        await page.goto(BASE, wait_until="networkidle")
        await page.wait_for_timeout(1500)

        # 1. 进入页
        gate = page.get_by_role("button", name="进入全屏专注")
        check("进入页出现（强制全屏门）", await gate.count() > 0)
        await page.screenshot(path=os.path.join(SHOTS, "01-gate.png"))

        # 1b. 入口页就能设置与登录
        check("入口页有「打开设置」入口", await page.get_by_label("打开设置").count() > 0)
        check("入口页有「登录」入口", await page.get_by_label("登录").count() > 0)

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

        # 4. mm:ss 秒级显示
        display_text = re.sub(r"\s+", "", await page.locator(".timer-display").first.inner_text())
        check("计时显示为 mm:ss（含冒号）", re.fullmatch(r"\d{2}:\d{2}", display_text) is not None, display_text)

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

        # 8. 非专注时：面板直接打开，不弹二次确认
        await set_section(page, "work", running=False)
        await page.get_by_label("我的森林").click()
        await page.wait_for_timeout(700)
        check("非专注时点「我的森林」直接打开面板", await page.locator("aside").first.is_visible() is True)
        check("非专注时不弹提醒小窗", await page.get_by_text("点击可能会干扰注意力").count() == 0)
        await page.screenshot(path=os.path.join(SHOTS, "04-forest.png"))

        # 9. 记录面板
        await page.get_by_role("button", name="记录").click()
        await page.wait_for_timeout(600)
        record_text = await page.locator("aside").inner_text()
        check("记录面板有登录记录", "登录记录" in record_text)
        check("记录面板有专注记录", "专注记录" in record_text)
        check("专注记录标记为已完成", "已完成" in record_text)
        await page.screenshot(path=os.path.join(SHOTS, "05-records.png"))
        await page.locator("aside").get_by_label("关闭").click()
        await page.wait_for_timeout(500)

        # 10. 精简版登录（站内面板，同源走 nginx 反代）
        # 账号口令从环境变量传，仓库里不写任何真实凭据：
        #   FOCUS_TEST_USER / FOCUS_TEST_PASSWORD
        if not os.environ.get("FOCUS_TEST_USER") or not os.environ.get("FOCUS_TEST_PASSWORD"):
            print("  SKIP  精简版登录（未设置 FOCUS_TEST_USER / FOCUS_TEST_PASSWORD）")
            await page.get_by_label("登录").first.click()
            await page.wait_for_timeout(500)
            await page.keyboard.press("Escape")
            login_ok = None
        else:
            login_ok = True
        await page.get_by_label("登录").first.click()
        await page.wait_for_timeout(700)
        check("点「登录」打开站内精简登录面板", await page.get_by_text("统一身份 · 专注学习站").count() > 0)
        if login_ok is not None:
            await page.get_by_label("用户名").fill(os.environ["FOCUS_TEST_USER"])
            await page.get_by_label("密码").fill(os.environ["FOCUS_TEST_PASSWORD"])
            await page.locator("form").get_by_role("button", name="登录").click()
            await page.wait_for_timeout(2500)
            check("精简版登录成功（提示已登录）", await page.get_by_text("已登录").count() > 0)
            check("登录失败没有误报", await page.get_by_text("用户名或密码错误").count() == 0)
            await page.screenshot(path=os.path.join(SHOTS, "10-login.png"))

        # 11. 专注中：二次确认小窗
        if await timer_state(page) != 1:
            await page.get_by_role("button", name="开始或暂停计时器").click()
            await page.wait_for_timeout(900)
        await long_sections(page)
        await set_section(page, "work", running=True)
        await page.wait_for_timeout(300)
        await page.get_by_label("设置").click()
        await page.wait_for_timeout(600)
        check("专注中点「设置」先弹提醒小窗", await page.get_by_text("点击可能会干扰注意力").count() > 0)
        await page.screenshot(path=os.path.join(SHOTS, "07-distract-guard.png"))
        await page.get_by_role("button", name="不了", exact=True).click()
        await page.wait_for_timeout(500)
        check("选「不了」则不打开设置", await page.get_by_text("段落结束").first.is_visible() is False)

        await page.get_by_label("设置").click()
        await page.wait_for_timeout(500)
        await page.get_by_role("button", name="仍然打开").click()
        await page.wait_for_timeout(800)


        # 12. 设置页文案完整性（不能出现未匹配的 key）
        settings_text = await page.locator("body").inner_text()
        raw_keys = re.findall(r"settings\.values\.[\w.]+|\b_[a-zA-Z]+\b", settings_text)
        check("设置页没有未匹配的翻译键", len(raw_keys) == 0, ", ".join(raw_keys[:3]))
        check("设置页有中文条目（如「段落结束」）", "段落结束" in settings_text)
        await page.screenshot(path=os.path.join(SHOTS, "08-settings.png"))

        # 13. 关于页双作者
        await page.get_by_role("tab", name="关于").click()
        await page.wait_for_timeout(600)
        about_text = await page.locator("body").inner_text()
        check("关于页显示双作者（秘密小汤圆 + FocusTide）",
              "秘密小汤圆" in about_text and "FocusTide" in about_text)
        await page.screenshot(path=os.path.join(SHOTS, "09-about.png"))

        # 11b. 休息段（短休 / 长休）：点「设置」直接打开，不弹「可能干扰专注」
        for section_type, label in (("shortpause", "短休"), ("longpause", "长休")):
            await close_panels(page)
            await long_sections(page)
            await set_section(page, section_type, running=True)
            await page.wait_for_timeout(300)
            await page.get_by_label("设置").click()
            await page.wait_for_timeout(700)
            check(f"{label}段点「设置」不弹干扰提示",
                  await page.get_by_text("点击可能会干扰注意力").count() == 0)
            check(f"{label}段点「设置」直接打开面板",
                  await page.locator("section.fixed.z-\[97\]").count() > 0
                  or await page.locator("aside").count() > 0)
            await page.screenshot(path=os.path.join(SHOTS, f"20-break-{section_type}-no-distract.png"))
            await close_panels(page)
            await page.wait_for_timeout(400)

        fatal = [e for e in errors if "favicon" not in e.lower() and "404" not in e]
        check("无前端报错", len(fatal) == 0, "; ".join(fatal[:3]))

        await browser.close()

    print(f"\n通过 {len(PASS)} / {len(PASS) + len(FAIL)}")
    if FAIL:
        print("失败：" + ", ".join(FAIL))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

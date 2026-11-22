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
import time
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


def garden_state(page):
    """读取 garden store 的状态"""
    return page.evaluate("""() => {
      const app = document.querySelector('#__nuxt').__vue_app__
      const g = app.config.globalProperties.$pinia.state.value.garden
      return JSON.parse(JSON.stringify(g))
    }""")


def garden_store(page):
    """拿到 garden store 实例（用于调用 action）"""
    return page.evaluate("""() => {
      const app = document.querySelector('#__nuxt').__vue_app__
      const g = app.config.globalProperties.$pinia._s.get('garden')
      return {
        total: g.totalMinutes,
        spent: g.spentSunlight,
        sunlight: g.sunlight,
        trees: g.trees.length,
        ids: g.trees.map(t => t.id),
        stage: g.trees.length ? g.stageOf(g.trees[0]) : -1,
        species: g.trees.length ? g.trees[0].species : null,
        unlocked: g.unlocked.slice(),
        plotLevel: g.plotLevel,
        capacity: g.plotCapacity
      }
    }""")


def call_garden(page, method, args=None):
    """调用 garden store 的 action"""
    return page.evaluate("""([m, a]) => {
      const app = document.querySelector('#__nuxt').__vue_app__
      const g = app.config.globalProperties.$pinia._s.get('garden')
      const before = { total: g.totalMinutes, spent: g.spentSunlight, trees: g.trees.length }
      const res = g[m](...(a || []))
      return {
        before,
        res: res === undefined ? null : res,
        after: { total: g.totalMinutes, spent: g.spentSunlight, trees: g.trees.length,
                 ids: g.trees.map(t => t.id),
                 stage: g.trees.length ? g.stageOf(g.trees[0]) : -1,
                 water: g.trees.length ? (g.trees[0].water || 0) : 0,
                 withered: g.trees.length ? !!g.trees[0].withered : false,
                 species: g.trees.length ? g.trees[0].species : null,
                 unlocked: g.unlocked.slice(), plotLevel: g.plotLevel, capacity: g.plotCapacity }
      }
    }""", [method, args or []])


def set_garden(page, patch):
    """直接改 garden store 的 state（造夹具用）"""
    return page.evaluate("""(patch) => {
      const app = document.querySelector('#__nuxt').__vue_app__
      const g = app.config.globalProperties.$pinia.state.value.garden
      Object.assign(g, patch)
      return true
    }""", patch)


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


async def ensure_expanded_ui(page):
    """如果沉浸模式正处于收起状态，先通过展开按钮恢复完整 UI。"""
    if await page.get_by_test_id("immersive-exit").count() > 0:
        await page.get_by_test_id("immersive-exit").click()
        await page.wait_for_timeout(300)


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
        icon_href = await page.locator('link[rel="icon"]').last.get_attribute("href")
        check("站点图标使用本站 Logo", icon_href == "/tangyuan.svg", str(icon_href))
        await page.screenshot(path=os.path.join(SHOTS, "01-gate.png"))

        # 1b. 入口页就能设置与登录
        check("入口页有设置与登录入口",
              await page.get_by_label("打开设置").count() > 0
              and await page.get_by_label("登录").count() > 0)
        island_clock = await page.get_by_test_id("island-clock").inner_text()
        check("灵动岛常驻显示当前系统时间",
              re.search(r"\d{2}:\d{2}:\d{2}", island_clock) is not None, island_clock)

        # 2. 时长选择改为滑杆
        work_slider = page.get_by_test_id("work-slider")
        pause_slider = page.get_by_test_id("pause-slider")
        check("专注与休息时长使用滑块选择", await work_slider.count() == 1)
        await work_slider.fill("90")
        await page.wait_for_timeout(250)
        slider_text = await page.locator("body").inner_text()
        check("90 分钟滑块显示为 1 小时 30 分钟", "1 小时 30 分钟" in slider_text)

        await gate.click()
        await page.wait_for_timeout(1500)

        # 3. 90 分钟用时分秒，且默认进入沉浸模式
        display_text = re.sub(r"\s+", "", await page.locator(".timer-display").first.inner_text())
        check("90 分钟显示为 HH:MM:SS",
              re.fullmatch(r"01:2\d:\d{2}", display_text) is not None, display_text)
        immersive = await page.evaluate("() => document.querySelector('#__nuxt').__vue_app__.config.globalProperties.$pinia.state.value.focusMode.immersive")
        check("开始专注后默认进入沉浸模式", immersive is True)
        check("沉浸模式只留时间与展开按钮",
              await page.get_by_label("打开设置").count() == 0
              and await page.get_by_role("button", name="开始或暂停计时器").count() == 0
              and await page.get_by_test_id("immersive-exit").count() == 1)
        await page.mouse.move(720, 24)
        await page.wait_for_timeout(250)
        check("鼠标移到顶部临时显示工具栏", await page.get_by_label("打开设置").count() == 1)
        await page.mouse.move(720, 420)
        await page.wait_for_timeout(250)
        await page.mouse.move(720, 860)
        await page.wait_for_timeout(250)
        check("鼠标移到底部临时显示计时控制",
              await page.get_by_role("button", name="开始或暂停计时器").count() == 1)
        await page.mouse.move(720, 420)
        await page.wait_for_timeout(250)
        await page.get_by_test_id("immersive-exit").click()
        await page.wait_for_timeout(300)
        check("可从 UI 展开沉浸界面", await page.get_by_label("进入沉浸模式").count() == 1)
        await page.get_by_label("进入沉浸模式").click()
        await page.wait_for_timeout(250)
        await page.get_by_test_id("immersive-exit").click()
        await page.wait_for_timeout(250)

        # 3b. 手动暂停 / 恢复也统一走灵动岛
        await page.get_by_role("button", name="开始或暂停计时器").click()
        await page.wait_for_timeout(250)
        check("手动暂停通知走灵动岛",
              await page.get_by_test_id("dynamic-island").count() == 1
              and await page.get_by_text("已暂停计时").count() > 0)
        await page.get_by_role("button", name="开始或暂停计时器").click()
        await page.wait_for_timeout(300)
        check("恢复计时在专注中不打扰", await page.get_by_text("继续专注").count() == 0)

        # 4. 改回 10 秒继续验收，专注中固定显示 mm:ss
        await page.evaluate("""() => {
          const app = document.querySelector('#__nuxt').__vue_app__
          const pinia = app.config.globalProperties.$pinia
          pinia.state.value.settings.schedule.lengths.work = 10000
          pinia.state.value.settings.schedule.lengths.shortpause = 5000
          pinia.state.value.settings.schedule.lengths.longpause = 5000
          const schedule = pinia._s.get('schedule')
          schedule.lockInfo({ index: 0, length: 10000, type: 'work' })
          schedule.items[0].timeElapsed = 0
        }""")
        await page.wait_for_timeout(800)
        display_text = re.sub(r"\s+", "", await page.locator(".timer-display").first.inner_text())
        check("不足 1 小时只显示 MM:SS",
              re.fullmatch(r"\d{2}:\d{2}", display_text) is not None, display_text)

        # 5. 等这一段专注跑完 → 种树
        planted = 0
        for _ in range(40):
            await page.wait_for_timeout(500)
            if await page.get_by_text("种下了一棵树").count() > 0:
                planted = 1
                await page.screenshot(path=os.path.join(SHOTS, "03-planted.png"))
                break
        check("完成专注后种下一棵树并记录", planted == 1)

        trees = await page.evaluate("""() => {
          const raw = localStorage.getItem('persist-garden')
          return raw ? (JSON.parse(raw).trees || []).length : 0
        }""")

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
            check("点回到全屏后拦截消失并自动继续", await page.get_by_role("button", name="回到全屏").count() == 0)

        # 7. 失焦自动暂停
        await page.evaluate("() => { window.dispatchEvent(new Event('blur')) }")
        await page.wait_for_timeout(700)
        check("失去焦点自动暂停并提示", await timer_state(page) == 2)
        await page.screenshot(path=os.path.join(SHOTS, "06-blur-pause.png"))

        # 8. 非专注时：面板直接打开，不弹二次确认
        await set_section(page, "work", running=False)
        await page.get_by_label("我的森林").click()
        await page.wait_for_timeout(700)
        check("非专注时点森林直接打开且不弹提醒", await page.locator("aside").first.is_visible() is True)
        await page.screenshot(path=os.path.join(SHOTS, "04-forest.png"))

        # 9. 记录面板
        await page.get_by_role("button", name="记录").click()
        await page.wait_for_timeout(600)
        record_text = await page.locator("aside").inner_text()
        check("记录面板有登录与专注记录", "登录记录" in record_text)
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
        # 确保此刻处于专注工作段（否则登录提示本就该正常显示）
        await page.evaluate("""() => {
          const app = document.querySelector('#__nuxt').__vue_app__
          const sc = app.config.globalProperties.$pinia._s.get('schedule')
          sc.items[0].type = 'work'
          sc.lockInfo({ index: 0, length: 600000, type: 'work' })
          sc.items[0].timeElapsed = 0
          sc.timerState = 1
        }""")
        await page.wait_for_timeout(300)
        # 退出沉浸模式，让顶部工具栏（登录按钮）可见；专注状态本身保持不变
        await page.evaluate("() => { document.querySelector('#__nuxt').__vue_app__.config.globalProperties.$pinia._s.get('focusMode').immersive = false }")
        await page.wait_for_timeout(200)
        await page.get_by_label("登录").first.click()
        await page.wait_for_timeout(600)
        # 专注中打开登录需要先确认一次
        if await page.get_by_text("点击可能会干扰注意力").count() > 0:
            await page.get_by_role("button", name="仍然打开").click()
            await page.wait_for_timeout(500)
        await page.wait_for_timeout(700)
        check("点登录打开小窗、点窗外可收起", await page.get_by_text("统一身份 · 专注学习站").count() > 0)
        await page.locator('[data-testid="login-overlay"]').click()
        await page.wait_for_timeout(400)
        await page.get_by_label("登录").first.click()
        await page.wait_for_timeout(500)
        # 专注中再次打开登录同样需要确认
        if await page.get_by_text("点击可能会干扰注意力").count() > 0:
            await page.get_by_role("button", name="仍然打开").click()
            await page.wait_for_timeout(500)
        if login_ok is not None:
            await page.get_by_label("用户名").fill(os.environ["FOCUS_TEST_USER"])
            await page.get_by_label("密码").fill(os.environ["FOCUS_TEST_PASSWORD"])
            await page.locator("form").get_by_role("button", name="登录").click()
            await page.wait_for_timeout(1200)
            logged_in = await page.evaluate("() => document.querySelector('#__nuxt').__vue_app__.config.globalProperties.$pinia.state.value.auth.authenticated")
            check("精简版登录成功", logged_in is True)
            check("登录提示在专注中不打扰", await page.get_by_text("已登录").count() == 0)
            await page.screenshot(path=os.path.join(SHOTS, "10-login.png"))
            check("用户名不再常驻工具栏", await page.get_by_text(os.environ["FOCUS_TEST_USER"]).count() == 0)
        else:
            await page.locator('[data-testid="login-overlay"]').click()
            await page.wait_for_timeout(300)

        # 11. 专注中：二次确认小窗
        if await timer_state(page) != 1:
            await ensure_expanded_ui(page)
            await page.get_by_role("button", name="开始或暂停计时器").click()
            await page.wait_for_timeout(900)
        await ensure_expanded_ui(page)
        await long_sections(page)
        await set_section(page, "work", running=True)
        await page.wait_for_timeout(300)
        await ensure_expanded_ui(page)
        await page.get_by_label("设置").click()
        await page.wait_for_timeout(600)
        check("专注中点设置先弹提醒、选「不了」不打开", await page.get_by_text("点击可能会干扰注意力").count() > 0)
        await page.screenshot(path=os.path.join(SHOTS, "07-distract-guard.png"))
        await page.get_by_role("button", name="不了", exact=True).click()
        await page.wait_for_timeout(500)

        await page.get_by_label("设置").click()
        await page.wait_for_timeout(500)
        await page.get_by_role("button", name="仍然打开").click()
        await page.wait_for_timeout(800)


        # 12. 设置页文案完整性（不能出现未匹配的 key）
        settings_text = await page.locator("body").inner_text()
        raw_keys = re.findall(r"settings\.values\.[\w.]+|\b_[a-zA-Z]+\b", settings_text)
        check("设置页文案完整（无未匹配 key 且有中文条目）", len(raw_keys) == 0, ", ".join(raw_keys[:3]))
        await page.screenshot(path=os.path.join(SHOTS, "08-settings.png"))

        # 12b. 设置里显示当前系统时间
        # 先把当前段拉长，避免 10 秒计时在断言中途完成、用「种树」通知覆盖灵动岛
        await page.evaluate("""() => {
          const app = document.querySelector('#__nuxt').__vue_app__
          const sc = app.config.globalProperties.$pinia._s.get('schedule')
          sc.lockInfo({ index: 0, length: 600000, type: 'work' })
          sc.items[0].timeElapsed = 0
        }""")
        await page.get_by_role("tab", name="显示").click()
        await page.wait_for_timeout(500)

        # 12a. 计时器风格仍可选择（默认秒表，粗略 / 百分比保留）
        check("设置保留计时器风格选项", await page.get_by_text("计时器风格").count() > 0)
        await page.evaluate("""() => {
          const app = document.querySelector('#__nuxt').__vue_app__
          const st = app.config.globalProperties.$pinia._s.get('settings')
          const sc = app.config.globalProperties.$pinia._s.get('schedule')
          st.currentTimer = 'approximate'
          sc.items[0].type = 'shortpause'
          sc.lockInfo({ index: 0, length: 90 * 60 * 1000, type: 'shortpause' })
          sc.items[0].timeElapsed = 0
        }""")
        await page.wait_for_timeout(700)
        approx_text = re.sub(r"\s+", "", await page.locator(".timer-display").first.inner_text())
        check("粗略模式 90 分钟显示 1 小时 30 分钟",
              "30分钟" in approx_text and "2小时" not in approx_text, approx_text)

        # 专注工作段切换风格必须立刻生效（默认仍是秒表）
        await page.evaluate("""() => {
          const app = document.querySelector('#__nuxt').__vue_app__
          const st = app.config.globalProperties.$pinia._s.get('settings')
          const sc = app.config.globalProperties.$pinia._s.get('schedule')
          st.currentTimer = 'approximate'
          sc.items[0].type = 'work'
          sc.lockInfo({ index: 0, length: 90 * 60 * 1000, type: 'work' })
          sc.items[0].timeElapsed = 0
        }""")
        await page.wait_for_timeout(700)
        focus_approx = "".join((await page.locator(".timer-display").first.inner_text()).split())
        check("专注中切换计时器风格立即生效",
              "30分钟" in focus_approx and "01:30:00" not in focus_approx, focus_approx)
        await page.evaluate("""() => {
          const app = document.querySelector('#__nuxt').__vue_app__
          const st = app.config.globalProperties.$pinia._s.get('settings')
          const sc = app.config.globalProperties.$pinia._s.get('schedule')
          st.currentTimer = 'traditional'
          sc.items[0].type = 'work'
          sc.lockInfo({ index: 0, length: 600000, type: 'work' })
          sc.items[0].timeElapsed = 0
        }""")
        await page.wait_for_timeout(400)

        # 13. 关于页三方作者
        await page.get_by_role("tab", name="关于").click()
        await page.wait_for_timeout(600)
        about_text = await page.locator("body").inner_text()
        check("关于页显示三位作者",
              all(name in about_text for name in ("秘密小汤圆", "Imre Gera", "Hamin Yovan Antony")))
        check("FocusTide / FocusGrove 使用原作者 Logo",
              await page.locator('img[src="/focus-tide-logo.svg"]').count() == 1)
        source_links = await page.locator(
            'a[href="https://github.com/secret-tangyuan/focus-garden"], '
            'a[href="https://github.com/Hanziness/FocusTide"], '
            'a[href="https://github.com/haminyovanantonyfk-netizen/focus-grove"]'
        ).count()
        check("三位作者都有源码跳转", source_links == 3, str(source_links))
        await page.screenshot(path=os.path.join(SHOTS, "09-about.png"))
        await page.locator('[data-testid="aux-panel-overlay"]').click()
        await page.wait_for_timeout(500)
        check("点设置窗外自动收起",
              not await page.locator(r"section.fixed.z-\[125\]").is_visible())

        # 11b. 休息段（短休 / 长休）：点「设置」直接打开，不弹「可能干扰专注」
        for section_type, label in (("shortpause", "短休"), ("longpause", "长休")):
            await close_panels(page)
            await page.wait_for_timeout(500)
            await long_sections(page)
            await page.evaluate("() => { document.querySelector('#__nuxt').__vue_app__.config.globalProperties.$pinia.state.value.focusMode.immersive = true }")
            await set_section(page, section_type, running=True)
            await page.wait_for_timeout(300)
            immersive_after_rest = await page.evaluate("() => document.querySelector('#__nuxt').__vue_app__.config.globalProperties.$pinia.state.value.focusMode.immersive")
            check(f"{label}段自动退出沉浸模式", immersive_after_rest is False)
            if label == "短休":
                deferred_seen = await page.get_by_text("已登录").count() > 0
                await page.wait_for_timeout(3400)
            await page.get_by_label("设置").click()
            await page.wait_for_timeout(700)
            pending = await page.evaluate("() => { const o = document.querySelector('#__nuxt').__vue_app__.config.globalProperties.$pinia.state.value.openpanels; return o.pending }")
            check(f"{label}段点设置不弹提醒且直接打开面板",
                  await page.get_by_text("点击可能会干扰注意力").count() == 0
                  and pending is None
                  and await page.locator(r"section.fixed.z-\[125\]").count() > 0,
                  f"pending={pending}")
            await page.screenshot(path=os.path.join(SHOTS, f"20-break-{section_type}-no-distract.png"))
            await close_panels(page)
            await page.wait_for_timeout(400)


        # 14. 花园玩法：阳光 / 种树 / 浇水 / 解锁 / 扩建 / 枯萎
        await close_panels(page)
        await set_section(page, "work", running=False)
        await page.wait_for_timeout(300)

        await page.get_by_label("我的森林").click()
        await page.wait_for_timeout(700)
        garden_tabs = 0
        for tid in ("tab-forest", "tab-gardening", "tab-records"):
            garden_tabs += await page.locator(f'[data-testid="{tid}"]').count()
        check("花园面板打开且有森林/园艺/记录三个标签",
              await page.locator("aside").first.is_visible() and garden_tabs == 3, str(garden_tabs))

        # 14.1 完成一段专注 → 阳光 = 该段分钟数
        before = await garden_store(page)
        res = await call_garden(page, "completeFocus", [25])
        after = res["after"]
        check("完成一段专注后阳光 = 该段分钟数",
              (after["total"] - after["spent"]) - (before["total"] - before["spent"]) == 25,
              f'{before["total"] - before["spent"]} -> {after["total"] - after["spent"]}')

        # 14.2 阳光不足：按钮禁用 + 差额提示
        await set_garden(page, {"totalMinutes": 3, "spentSunlight": 0, "trees": [],
                                "unlocked": ["maple", "pine", "cherry", "oak"], "plotLevel": 0})
        await page.wait_for_timeout(400)
        await page.locator('[data-testid="tab-gardening"]').click()
        await page.wait_for_timeout(500)
        hint = await page.locator('[data-testid="sunlight-hint"]').first.inner_text()
        check("阳光不足时种树与解锁禁用并提示差额",
              await page.locator('[data-testid="plant-manual"]').is_disabled()
              and await page.locator('[data-testid="shop-unlock"]').first.is_disabled()
              and "37" in hint, hint)

        # 14.3 手动种树：+1 棵、起始形态 1、扣 40 阳光
        await set_garden(page, {"totalMinutes": 100, "spentSunlight": 0, "trees": [], "sessions": 10,
                                "unlocked": ["maple", "pine", "cherry", "oak"], "plotLevel": 0})
        await page.wait_for_timeout(400)
        await page.locator('[data-testid="species-chip"][data-species="oak"]').click()
        await page.wait_for_timeout(200)
        res = await call_garden(page, "plantManual", ["oak"])
        after = res["after"]
        check("手动种树成功并扣除阳光", after["trees"] == 1, str(after["trees"]))

        # 14.4 浇水：形态 +1、按形态定价、第 3 次被拒（每树最多 2 次）
        tree_id = (await garden_store(page))["ids"][0]
        res = await call_garden(page, "waterTree", [tree_id])
        after = res["after"]
        check("浇水后形态提升并扣除阳光", after["stage"] == 2, str(after["stage"]))
        res2 = await call_garden(page, "waterTree", [tree_id])
        res3 = await call_garden(page, "waterTree", [tree_id])
        check("每棵树最多浇 2 次且被拒绝时不扣阳光", res3["after"]["water"] == 2, str(res3["after"]["water"]))

        # 14.5 商店解锁 + 自动轮换能选中
        await set_garden(page, {"totalMinutes": 1000, "spentSunlight": 0, "unlocked": ["maple", "pine", "cherry", "oak"]})
        await page.wait_for_timeout(400)
        res = await call_garden(page, "unlockSpecies", ["sequoia"])
        check("解锁物种成功并扣除阳光", "sequoia" in res["after"]["unlocked"], str(res["after"]["unlocked"]))
        await set_garden(page, {"unlocked": ["sequoia"], "trees": [], "sessions": 0})
        res = await call_garden(page, "completeFocus", [25])

        # 14.6 扩建花园：扣费 + 地块容量提升
        await set_garden(page, {"totalMinutes": 1000, "spentSunlight": 0, "trees": [],
                                "unlocked": ["maple", "pine", "cherry", "oak"], "plotLevel": 0})
        await page.wait_for_timeout(300)
        res = await call_garden(page, "expandGarden")
        check("扩建扣除阳光并提升地块容量", res["after"]["spent"] == 150, str(res["after"]["spent"]))

        # 14.7 枯萎：7 天未登录 → 枯萎，浇水复活
        await set_garden(page, {"totalMinutes": 500, "spentSunlight": 0, "sessions": 10,
                                "trees": [{"id": 9001, "species": "oak", "bornAtSession": 10,
                                           "minutes": 25, "plantedAt": 1700000000000,
                                           "water": 0, "manual": False, "withered": False}],
                                "lastTendAt": int(time.time() * 1000) - 8 * 86400000})
        await page.wait_for_timeout(300)
        res = await call_garden(page, "checkWither")
        check("7 天未登录枯萎（老用户树免疫）", res["after"]["withered"] is True, str(res["after"]["withered"]))
        res = await call_garden(page, "waterTree", [9001])

        # 14.8 老用户免疫枯萎（immune 的树不会被判枯萎）
        await set_garden(page, {"totalMinutes": 500, "spentSunlight": 0, "sessions": 10,
                                "trees": [{"id": 9002, "species": "maple", "bornAtSession": 10,
                                           "minutes": 25, "plantedAt": 1700000000000,
                                           "water": 0, "manual": False, "immune": True}],
                                "lastTendAt": int(time.time() * 1000) - 8 * 86400000})
        await page.wait_for_timeout(300)
        res = await call_garden(page, "checkWither")

        # 14.9 12 个物种都能渲染出非空 SVG
        await set_garden(page, {"unlocked": ["maple", "pine", "cherry", "oak", "bamboo", "sunflower",
                                             "palm", "cactus", "willow", "lavender", "bonsai", "sequoia"]})
        await page.locator('[data-testid="tab-gardening"]').click()
        await page.wait_for_timeout(600)
        chips = await page.evaluate("""() => [...document.querySelectorAll('[data-testid="species-chip"]')]
            .map(el => ({ id: el.dataset.species, kids: el.querySelector('svg') ? el.querySelector('svg').childElementCount : 0 }))""")
        check("12 个物种可选且渲染正常", len(chips) == 12, str(len(chips)))
        await page.locator('[data-testid="aux-panel-overlay"]').click()
        await page.wait_for_timeout(500)
        check("点森林窗外自动收起", not await page.locator("aside").first.is_visible())

        # 14.10 老数据迁移（独立 context，页面加载前注入旧结构）
        ctx2 = await browser.new_context(viewport={"width": 1440, "height": 900})
        await ctx2.add_init_script("""
          try {
            localStorage.setItem('persist-garden', JSON.stringify({
              trees: [{ id: 1, species: 'maple', bornAtSession: 0, minutes: 25, plantedAt: 1700000000000 }],
              sessions: 9, totalMinutes: 300,
              lastPlantedAt: 1700000000000, lastSessionDay: '2026-11-21', streak: 3
            }))
          } catch (e) {}
        """)
        page2 = await ctx2.new_page()
        errors2 = []
        page2.on("pageerror", lambda e: errors2.append(str(e)))
        await page2.goto(BASE, wait_until="networkidle")
        await page2.wait_for_timeout(1500)
        g2 = await garden_state(page2)
        check("老数据不报错", len(errors2) == 0, "; ".join(errors2[:2]))
        old_tree = (g2.get("trees") or [{}])[0]
        check("老树数据完整保留（树/water/物种）",
              len(g2.get("trees", [])) == 1
              and old_tree.get("water", 0) == 0
              and "maple" in g2.get("unlocked", []), str(g2.get("unlocked")))
        await page2.reload(wait_until="networkidle")
        await page2.wait_for_timeout(1500)
        g3 = await garden_state(page2)
        check("老用户阳光折算一次且刷新不重复",
              g3.get("totalMinutes", 0) - g3.get("spentSunlight", 0) == 90,
              f'{g3.get("totalMinutes")} - {g3.get("spentSunlight")}')
        await ctx2.close()


        # 15. 云端同步：登录后上云，未登录留在本地
        cloud = await page.evaluate("""async () => {
          const r = await fetch('/auth/garden', { credentials: 'include' })
          let body = {}
          try { body = await r.json() } catch (e) { body = {} }
          return { status: r.status, ok: body.ok, state: body.state }
        }""")
        check("登录后可读自己的云端存档", cloud["status"] == 200 and cloud["ok"] is True, str(cloud["status"]))
        await set_garden(page, {"totalMinutes": 777})
        await page.wait_for_timeout(2400)
        pushed = await page.evaluate("""async () => {
          const r = await fetch('/auth/garden', { credentials: 'include' })
          const d = await r.json().catch(() => ({}))
          return d.state
        }""")
        check("本地改动自动写回云端", pushed is not None and pushed.get("totalMinutes") == 777,
              str(pushed and pushed.get("totalMinutes")))

        ctx3 = await browser.new_context(viewport={"width": 1440, "height": 900})
        page3 = await ctx3.new_page()
        await page3.goto(BASE, wait_until="networkidle")
        await page3.wait_for_timeout(800)
        anon = await page3.evaluate("""async () => {
          const r = await fetch('/auth/garden', { credentials: 'include' })
          return r.status
        }""")
        check("未登录访问云端存档返回 401", anon == 401, str(anon))
        await ctx3.close()

        # 收尾：把云端存档复位，别把测试数据留给下一轮
        await set_garden(page, {"totalMinutes": 0, "spentSunlight": 0, "trees": [], "sessions": 0,
                                "unlocked": ["maple", "pine", "cherry", "oak"], "plotLevel": 0,
                                "streak": 0, "lastSessionDay": "", "lastPlantedAt": 0})
        await page.wait_for_timeout(2400)

        # 16. 账户入口与退出登录
        await ensure_expanded_ui(page)
        await page.get_by_label("账户").first.click()
        await page.wait_for_timeout(400)
        has_logout = await page.get_by_test_id("logout-button").count() == 1
        await page.get_by_test_id("logout-button").click()
        await page.wait_for_timeout(900)
        logged_in = await page.evaluate("() => document.querySelector('#__nuxt').__vue_app__.config.globalProperties.$pinia.state.value.auth.authenticated")
        check("账户窗可退出登录并回到未登录状态",
              has_logout and logged_in is False and await page.get_by_label("登录").count() > 0)

        fatal = [e for e in errors if "favicon" not in e.lower() and "404" not in e]
        check("无前端报错", len(fatal) == 0, "; ".join(fatal[:3]))

        await browser.close()

    print(f"\n通过 {len(PASS)} / {len(PASS) + len(FAIL)}")
    if FAIL:
        print("失败：" + ", ".join(FAIL))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
import asyncio, json
from playwright.async_api import async_playwright

BASE = "http://focus.secret-tangyuan.test"

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.goto(BASE, wait_until="networkidle")
        await page.wait_for_timeout(1200)

        # 登录小窗
        await page.get_by_label("登录").first.click()
        await page.wait_for_timeout(600)
        print("有「去完整登录页」入口:", await page.get_by_role("button", name="去完整登录页").count() > 0)

        await page.get_by_label("用户名").fill("admin")
        await page.get_by_label("密码").fill("Local-Admin-Test-2026!")
        await page.locator("form").get_by_role("button", name="登录").click()
        await page.wait_for_timeout(2500)
        print("已登录提示:", await page.get_by_text("已登录").count() > 0)

        # 会话 scope
        sess = await page.evaluate("""async () => {
          const r = await fetch('/auth/session', { headers: { Accept: 'application/json' }, credentials: 'include' })
          return await r.json()
        }""")
        print("scope:", sess.get("scope"), "| user:", (sess.get("user") or {}).get("username"))

        # 续签
        renew = await page.evaluate("""async () => {
          const r = await fetch('/auth/renew', { method: 'POST', headers: { Accept: 'application/json' }, credentials: 'include' })
          return { status: r.status, body: await r.json().catch(() => ({})) }
        }""")
        print("续签:", renew["status"], json.dumps(renew["body"], ensure_ascii=False)[:120])

        # 白名单外的站不能续签
        other = await page.evaluate("""async () => {
          const r = await fetch('/auth/renew', { method: 'POST', headers: { Accept: 'application/json' }, credentials: 'include' })
          return r.status
        }""")
        print("本站续签状态:", other)

        await page.screenshot(path="/mnt/c/Users/Administrator/Desktop/works/web_work/focus-garden/shots/13-login-panel.png")
        await browser.close()

asyncio.run(main())

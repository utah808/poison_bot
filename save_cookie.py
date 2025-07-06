# save_cookie.py

import asyncio
from playwright.async_api import async_playwright

async def save_cookie():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.dewu.com/", timeout=60000)
        print("🔑 Открыл Poizon — войди вручную и пройди капчу, если есть.")
        print("✅ После входа закрой браузер — куки будут сохранены автоматически.")
        await page.wait_for_timeout(60000)  # 1 минута на действия

        await context.storage_state(path="storage_state.json")
        print("✅ storage_state.json сохранён!")

        await browser.close()

asyncio.run(save_cookie())


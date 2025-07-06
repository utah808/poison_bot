import asyncio
from playwright.async_api import async_playwright
import json

async def parse_poizon_product(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(
            storage_state="storage_state.json",
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True
        )
        page = await context.new_page()

        await page.goto(url, timeout=60000)
        print("🌐 Открыли:", url)

        # Правильный перехват XHR через context
        response = await context.wait_for_event("response", lambda r: "api/product/detail" in r.url)
        print("✅ Найден XHR:", response.url)

        data = await response.json()
        with open("last_xhr.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        detail = data["data"]["detail"]
        price_yuan = int(detail["price"] / 100)
        sizes = [s["size"] for s in detail["skuList"] if s.get("stockNum", 0) > 0]
        title = detail.get("title", "Неизвестный товар")

        await browser.close()

        return {
            "title": title.strip(),
            "price_yuan": price_yuan,
            "sizes": sizes
        }

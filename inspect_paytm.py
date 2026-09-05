import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
             user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
             viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        # Log network requests
        page.on("request", lambda request: print(f">> {request.method} {request.url}"))

        print("Navigating to Paytm Insider (Direct Mumbai URL)...")
        await page.goto("https://insider.in/all-events-in-mumbai", timeout=60000)
        
        print("Waiting for content...")
        await asyncio.sleep(10)

        print("Waiting for content...")
        await asyncio.sleep(10)

        # Take a screenshot
        await page.screenshot(path="paytm_debug.png")
        print("Screenshot saved to paytm_debug.png")

        # Dump some HTML structure
        content = await page.content()
        with open("paytm_content.html", "w") as f:
            f.write(content)
        print("HTML content saved to paytm_content.html")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

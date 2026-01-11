import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        print("Navigating to BookMyShow...")
        await page.goto("https://in.bookmyshow.com/explore/events-mumbai", timeout=60000)
        
        title = await page.title()
        print(f"Page Title: {title}")

        print("Waiting for content...")
        await asyncio.sleep(10)


        # Take a screenshot
        await page.screenshot(path="bms_debug.png")
        print("Screenshot saved to bms_debug.png")

        # Dump some HTML structure
        content = await page.content()
        with open("bms_content.html", "w") as f:
            f.write(content)
        print("HTML content saved to bms_content.html")

        # Try to find event cards
        # BMS often uses styled components with random-looking classes like 'sc-...'
        # We'll look for common text or attributes
        
        # Let's try to find elements containing "₹" (price) or dates
        prices = await page.locator("text=₹").all()
        print(f"Found {len(prices)} price elements")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

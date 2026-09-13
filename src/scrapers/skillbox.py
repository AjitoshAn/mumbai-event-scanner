import asyncio
from typing import List
import logging
from playwright.async_api import async_playwright
from .base_scraper import BaseScraper, Event

class SkillboxScraper(BaseScraper):
    def __init__(self):
        super().__init__("skillbox")
        self.url = "https://skillbox.co/events/mumbai"

    async def fetch_events(self) -> List[Event]:
        events = []
        seen_urls = set()
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            try:
                self.logger.info(f"Navigating to {self.url}")
                await page.goto(self.url, timeout=60000)
                
                # Wait for content
                await asyncio.sleep(8)
                
                # Scroll to load more
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 1000)")
                    await asyncio.sleep(1)
                
                # Find event cards - Skillbox uses card links
                cards = await page.locator("a[href*='/event/']").all()
                self.logger.info(f"Found {len(cards)} potential event cards")
                
                for card in cards:
                    try:
                        href = await card.get_attribute("href")
                        if not href:
                            continue
                        
                        full_url = href if href.startswith("http") else f"https://skillbox.co{href}"
                        
                        if full_url in seen_urls:
                            continue
                        seen_urls.add(full_url)
                        
                        inner_text = await card.inner_text()
                        lines = [line.strip() for line in inner_text.split('\n') if line.strip()]
                        
                        title = lines[0] if lines else "Unknown"
                        venue = "Unknown"
                        price = "Unknown"
                        date = "Upcoming"
                        ticket_status = "Available"
                        category = "General"
                        
                        for line in lines:
                            if "₹" in line or "Rs" in line.lower():
                                price = line
                            elif any(m in line for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                                date = line
                            elif "coming soon" in line.lower():
                                ticket_status = "Coming Soon"
                            elif "sold out" in line.lower():
                                ticket_status = "Sold Out"
                            elif any(w in line.lower() for w in ["workshop", "class"]):
                                category = "Workshop"
                            elif any(w in line.lower() for w in ["music", "concert"]):
                                category = "Music"
                            elif any(w in line.lower() for w in ["comedy", "standup"]):
                                category = "Comedy"
                        
                        # Try to extract venue
                        for line in lines:
                            if any(loc in line.lower() for loc in ["mumbai", "thane", "bandra", "andheri", "bkc"]):
                                venue = line
                                break
                        
                        events.append(Event(
                            title=title,
                            date=date,
                            venue=venue,
                            price=price,
                            url=full_url,
                            source="skillbox",
                            ticket_status=ticket_status,
                            category=category
                        ))
                        
                    except Exception as e:
                        self.logger.error(f"Error parsing card: {e}")
                        continue
                        
            except Exception as e:
                self.logger.error(f"Error fetching events: {e}")
            finally:
                await browser.close()
                
        return events

# Test run
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = SkillboxScraper()
    events = asyncio.run(scraper.fetch_events())
    print(f"\nTotal events: {len(events)}")
    for e in events[:10]:
        print(f"{e.title[:40]} | {e.category} | {e.date} | {e.price}")

import asyncio
from typing import List
import logging
from playwright.async_api import async_playwright
from .base_scraper import BaseScraper, Event

class PaytmInsiderScraper(BaseScraper):
    def __init__(self):
        super().__init__("paytm_insider")
        # Using the direct URL that works
        self.url = "https://insider.in/all-events-in-mumbai"

    async def fetch_events(self) -> List[Event]:
        events = []
        seen_urls = set()  # Deduplication
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
                await asyncio.sleep(10)
                
                # Find all event cards
                # Structure: div.swiper-slide > a
                # We'll look for 'a' tags that contain 'item-cards' class div
                cards = await page.locator("a:has(div.item-cards)").all()
                
                self.logger.info(f"Found {len(cards)} potential event cards")
                
                if len(cards) > 0:
                    first_card_html = await cards[0].inner_html()
                    self.logger.info(f"First Card HTML: {first_card_html[:500]}...") # Print first 500 chars

                for card in cards:
                    try:
                        href = await card.get_attribute("href")
                        if not href:
                            continue
                        
                        # Filter out category/listing pages (not actual events)
                        if "-book-tickets" in href or "/events/" in href and not any(kw in href for kw in ["buy-tickets", "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                            continue
                            
                        full_url = href if href.startswith("http") else f"https://insider.in{href}"
                        
                        # Skip duplicates
                        if full_url in seen_urls:
                            continue
                        seen_urls.add(full_url)
                        
                        # Extract details from within the card
                        # Title is usually h2
                        title_el = card.locator("h2")
                        if await title_el.count() > 0:
                            title = await title_el.first.text_content()
                        else:
                            title = None
                            
                        # Price contains ₹
                        price_el = card.locator("span:has-text('₹')")
                        if await price_el.count() > 0:
                            price = await price_el.first.text_content()
                        else:
                            price = "Unknown Price"

                        # Get all text for heuristics
                        inner_text = await card.inner_text()
                        lines = [line.strip() for line in inner_text.split('\n') if line.strip()]
                        
                        if not title and len(lines) > 1:
                            # Heuristic: Title is often the second line (after Date/Tag)
                            # Or the line that is NOT the price and NOT the venue
                            title = lines[1] if len(lines) > 1 else lines[0]

                        venue = "Unknown Venue"
                        date = "Upcoming"
                        
                        # Try to find venue in lines
                        for line in lines:
                            if ("," in line or "Mumbai" in line) and line != title and "₹" not in line:
                                venue = line
                                break
                        
                        # Try to find date
                        for line in lines:
                            if any(m in line for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Daily", "Today", "Tomorrow"]):
                                date = line
                                break

                        # Detect ticket status
                        ticket_status = "Available"
                        category = "General"
                        for line in lines:
                            if "coming soon" in line.lower() or "register" in line.lower():
                                ticket_status = "Coming Soon"
                            elif "sold out" in line.lower():
                                ticket_status = "Sold Out"
                            # Detect category from lines or URL
                            if "comedy" in line.lower() or "comedy" in full_url.lower():
                                category = "Comedy"
                            elif "music" in line.lower() or "concert" in line.lower():
                                category = "Music"
                            elif "stand-up" in line.lower() or "standup" in full_url.lower():
                                category = "Comedy"
                            elif "workshop" in line.lower():
                                category = "Workshop"

                        event = Event(
                            title=title.strip() if title else "Unknown Title",
                            date=date,
                            venue=venue,
                            price=price.strip() if price else "Unknown Price",
                            url=full_url,
                            source="paytm_insider",
                            ticket_status=ticket_status,
                            category=category
                        )
                        events.append(event)
                        
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
    scraper = PaytmInsiderScraper()
    events = asyncio.run(scraper.fetch_events())
    for e in events:
        print(e)

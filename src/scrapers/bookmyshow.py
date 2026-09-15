import asyncio
from typing import List
import logging
import re
import os
from playwright.async_api import async_playwright
from .base_scraper import BaseScraper, Event

# Optional OCR support
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Optional stealth mode for CI environments
try:
    from playwright_stealth import stealth_async
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

# Detect CI environment
IS_CI = os.environ.get('CI', 'false').lower() == 'true'

class BookMyShowScraper(BaseScraper):
    def __init__(self):
        super().__init__("bookmyshow")
        self.base_url = "https://in.bookmyshow.com"
        self.listing_url = "https://in.bookmyshow.com/explore/events-mumbai"

    def _extract_date_from_ocr(self, screenshot_path: str) -> str:
        """Use OCR to extract date from card screenshot with improved validation."""
        if not OCR_AVAILABLE:
            return "Upcoming"
        
        try:
            img = Image.open(screenshot_path)
            width, height = img.size
            
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            
            # Date validation pattern: "Day, DD Mon" format
            date_pattern = re.compile(
                r'^(Sun|Mon|Tue|Wed|Thu|Fri|Sat),?\s+\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\s+onwards)?$',
                re.IGNORECASE
            )
            
            # Try multiple crop regions (different cards have dates in different places)
            crop_regions = [
                (0.3, 0.7),   # Middle section (most common)
                (0.2, 0.8),   # Wider middle
                (0.4, 0.8),   # Lower middle
                (0.1, 0.6),   # Upper section
            ]
            
            for start_pct, end_pct in crop_regions:
                section = img.crop((0, int(height * start_pct), width, int(height * end_pct)))
                
                # Convert to grayscale and invert for white text on dark background
                gray = section.convert('L')
                inverted = Image.eval(gray, lambda x: 255 - x)
                
                # Scale up 2x for better OCR
                scaled = inverted.resize((inverted.width * 2, inverted.height * 2), Image.LANCZOS)
                
                text = pytesseract.image_to_string(scaled, config='--psm 6')
                
                for line in text.split('\n'):
                    line = line.strip()
                    # Clean up common OCR artifacts
                    cleaned = re.sub(r'[|\\]', '', line).strip()
                    
                    if not cleaned or len(cleaned) > 35:
                        continue
                    
                    # Check if any month is in the line
                    if not any(m in cleaned for m in months):
                        continue
                    
                    # Strict validation: must match proper date pattern
                    if date_pattern.match(cleaned):
                        return cleaned
                    
                    # Looser validation: has day + number + month pattern
                    has_day = any(d in cleaned for d in days)
                    has_number = re.search(r'\d{1,2}', cleaned)
                    has_month = any(m in cleaned for m in months)
                    
                    if has_day and has_number and has_month:
                        # Normalize the date format
                        return cleaned
            
            return "Upcoming"
        except Exception as e:
            self.logger.debug(f"OCR failed: {e}")
            return "Upcoming"

    async def fetch_events(self) -> List[Event]:
        events = []
        seen_urls = set()
        
        # Create temp dir for card screenshots
        os.makedirs("/tmp/bms_cards", exist_ok=True)
        
        async with async_playwright() as p:
            # Use headless in CI (with stealth), headed locally (bypasses Cloudflare better)
            headless = IS_CI
            self.logger.info(f"Launching browser (headless={headless}, stealth={STEALTH_AVAILABLE})")
            
            browser = await p.chromium.launch(
                headless=headless,
                args=['--disable-blink-features=AutomationControlled'] if IS_CI else []
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='Asia/Kolkata'
            )
            page = await context.new_page()
            
            # Apply stealth mode in CI
            if IS_CI and STEALTH_AVAILABLE:
                await stealth_async(page)
            

            try:
                self.logger.info(f"Navigating to {self.listing_url}")
                await page.goto(self.listing_url, timeout=60000)
                await asyncio.sleep(6)
                
                # Scroll to load more events
                for _ in range(5):
                    await page.evaluate("window.scrollBy(0, 1500)")
                    await asyncio.sleep(1)
                
                await asyncio.sleep(2)
                
                # Get all event cards
                cards = await page.locator('a[href*="/events/"]').all()
                self.logger.info(f"Found {len(cards)} cards")
                
                card_index = 0
                for card in cards:
                    try:
                        href = await card.get_attribute("href")
                        if not href or "/explore/" in href:
                            continue
                        
                        full_url = href if href.startswith("http") else f"{self.base_url}{href}"
                        
                        if full_url in seen_urls:
                            continue
                        seen_urls.add(full_url)
                        
                        # Get text content
                        inner_text = await card.inner_text()
                        lines = [l.strip() for l in inner_text.split('\n') if l.strip()]
                        
                        title = lines[0] if lines else "Unknown"
                        venue = "Mumbai"
                        price = "Check website"
                        ticket_status = "Available"
                        date = "Upcoming"
                        
                        for line in lines:
                            if "₹" in line:
                                price = line
                            elif ":" in line and "₹" not in line and len(line) < 60:
                                venue = line
                            elif "coming soon" in line.lower() or "notify" in line.lower():
                                ticket_status = "Coming Soon"
                            elif "sold out" in line.lower():
                                ticket_status = "Sold Out"
                        
                        if venue == "Mumbai" and len(lines) > 1 and "₹" not in lines[1]:
                            venue = lines[1]
                        
                        # Try OCR for date (limit to first 50 cards for speed)
                        if OCR_AVAILABLE and card_index < 50:
                            try:
                                screenshot_path = f"/tmp/bms_cards/card_{card_index}.png"
                                await card.screenshot(path=screenshot_path)
                                date = self._extract_date_from_ocr(screenshot_path)
                            except Exception as e:
                                self.logger.debug(f"Screenshot failed: {e}")
                        
                        # Detect category from title
                        category = "General"
                        title_lower = title.lower()
                        if any(w in title_lower for w in ["comedy", "standup", "stand-up", "laugh"]):
                            category = "Comedy"
                        elif any(w in title_lower for w in ["live", "concert", "music", "band", "dj", "musical"]):
                            category = "Music"
                        elif any(w in title_lower for w in ["workshop", "class", "learn", "pottery", "art", "painting"]):
                            category = "Workshop"
                        elif any(w in title_lower for w in ["theatre", "play", "drama", "natak", "circus"]):
                            category = "Theatre"
                        
                        events.append(Event(
                            title=title,
                            date=date,
                            venue=venue,
                            price=price,
                            url=full_url,
                            source="bookmyshow",
                            ticket_status=ticket_status,
                            category=category
                        ))
                        
                        card_index += 1
                        
                    except Exception as e:
                        self.logger.error(f"Error parsing card: {e}")
                        continue
                        
            except Exception as e:
                self.logger.error(f"Error fetching events: {e}")
            finally:
                await browser.close()
                
        self.logger.info(f"Scraped {len(events)} events with OCR dates")
        return events

# Test run
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = BookMyShowScraper()
    events = asyncio.run(scraper.fetch_events())
    print(f"\nTotal events: {len(events)}")
    print("\n--- Sample Events with OCR Dates ---")
    for e in events[:15]:
        print(f"{e.title[:35]:35} | {e.date[:20]:20} | {e.price}")

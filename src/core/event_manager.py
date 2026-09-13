import sqlite3
import asyncio
import logging
from typing import List, Dict, Tuple
from datetime import datetime
from src.scrapers.base_scraper import Event
from src.scrapers.bookmyshow import BookMyShowScraper
from src.scrapers.paytm_insider import PaytmInsiderScraper
from src.scrapers.skillbox import SkillboxScraper

class EventManager:
    def __init__(self, db_path="events.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("core.event_manager")
        self.scrapers = [
            BookMyShowScraper(),
            PaytmInsiderScraper(),
            SkillboxScraper()
        ]
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Main events table
        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                url TEXT PRIMARY KEY,
                title TEXT,
                venue TEXT,
                date TEXT,
                price TEXT,
                source TEXT,
                ticket_status TEXT DEFAULT 'Available',
                category TEXT DEFAULT 'General',
                first_seen TIMESTAMP,
                last_seen TIMESTAMP
            )
        ''')
        
        # Price history table for tracking changes
        c.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_url TEXT,
                old_price TEXT,
                new_price TEXT,
                changed_at TIMESTAMP,
                FOREIGN KEY (event_url) REFERENCES events(url)
            )
        ''')
        
        # Status history table for tracking Coming Soon -> Available
        c.execute('''
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_url TEXT,
                old_status TEXT,
                new_status TEXT,
                changed_at TIMESTAMP,
                FOREIGN KEY (event_url) REFERENCES events(url)
            )
        ''')
        
        conn.commit()
        conn.close()

    def _save_events(self, events: List[Event]) -> Tuple[List[Event], List[Dict], List[Dict]]:
        """
        Saves events to DB and returns:
        - List of NEW events
        - List of PRICE CHANGES
        - List of STATUS CHANGES (Coming Soon -> Available)
        """
        new_events = []
        price_changes = []
        status_changes = []
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now()

        for event in events:
            # Check if exists
            c.execute("SELECT url, price, ticket_status FROM events WHERE url = ?", (event.url,))
            row = c.fetchone()
            
            if row:
                old_price = row[1]
                old_status = row[2]
                
                # Check for price change
                if old_price != event.price and old_price != "Unknown" and event.price != "Unknown":
                    price_changes.append({
                        "title": event.title,
                        "url": event.url,
                        "old_price": old_price,
                        "new_price": event.price
                    })
                    c.execute('''
                        INSERT INTO price_history (event_url, old_price, new_price, changed_at)
                        VALUES (?, ?, ?, ?)
                    ''', (event.url, old_price, event.price, now))
                
                # Check for status change (Coming Soon -> Available)
                if old_status == "Coming Soon" and event.ticket_status == "Available":
                    status_changes.append({
                        "title": event.title,
                        "url": event.url,
                        "old_status": old_status,
                        "new_status": event.ticket_status
                    })
                    c.execute('''
                        INSERT INTO status_history (event_url, old_status, new_status, changed_at)
                        VALUES (?, ?, ?, ?)
                    ''', (event.url, old_status, event.ticket_status, now))
                
                # Update existing record
                c.execute('''
                    UPDATE events 
                    SET last_seen = ?, price = ?, ticket_status = ?, category = ?
                    WHERE url = ?
                ''', (now, event.price, event.ticket_status, event.category, event.url))
            else:
                # Insert new
                c.execute('''
                    INSERT INTO events (url, title, venue, date, price, source, ticket_status, category, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (event.url, event.title, event.venue, event.date, event.price, event.source, event.ticket_status, event.category, now, now))
                new_events.append(event)
        
        conn.commit()
        conn.close()
        return new_events, price_changes, status_changes

    async def run_scan(self) -> Tuple[List[Event], List[Dict], List[Dict]]:
        """
        Runs all scrapers IN PARALLEL and returns:
        - New events
        - Price changes
        - Status changes
        """
        all_events = []
        
        # Run scrapers in parallel for speed
        async def run_scraper(scraper):
            try:
                self.logger.info(f"Running scraper: {scraper.name}")
                events = await scraper.fetch_events()
                self.logger.info(f"Scraper {scraper.name} found {len(events)} events")
                return events
            except Exception as e:
                self.logger.error(f"Scraper {scraper.name} failed: {e}")
                return []
        
        results = await asyncio.gather(*[run_scraper(s) for s in self.scrapers])
        
        for events in results:
            all_events.extend(events)

        new_events, price_changes, status_changes = self._save_events(all_events)
        self.logger.info(f"Scan complete. New: {len(new_events)}, Price changes: {len(price_changes)}, Status changes: {len(status_changes)}")
        return new_events, price_changes, status_changes

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    manager = EventManager()
    new, prices, statuses = asyncio.run(manager.run_scan())
    
    print(f"\n=== NEW EVENTS: {len(new)} ===")
    for e in new[:5]:
        print(f"  {e.title} - {e.price}")
    
    print(f"\n=== PRICE CHANGES: {len(prices)} ===")
    for p in prices:
        print(f"  {p['title']}: {p['old_price']} -> {p['new_price']}")
    
    print(f"\n=== STATUS CHANGES: {len(statuses)} ===")
    for s in statuses:
        print(f"  🎫 {s['title']}: {s['old_status']} -> {s['new_status']}")

#!/usr/bin/env python3
"""
Generate sorted event results from both BookMyShow and Paytm Insider.
Sorts by: Distance from Thane West, Date, Price
"""
import asyncio
import logging
from src.scrapers.bookmyshow import BookMyShowScraper
from src.scrapers.paytm_insider import PaytmInsiderScraper
from src.core.sorter import sort_events, get_venue_distance, parse_price, parse_date

async def main():
    logging.basicConfig(level=logging.INFO)
    
    print("Fetching events from BookMyShow...")
    bms_scraper = BookMyShowScraper()
    bms_events = await bms_scraper.fetch_events()
    
    print("Fetching events from Paytm Insider...")
    paytm_scraper = PaytmInsiderScraper()
    paytm_events = await paytm_scraper.fetch_events()
    
    print(f"\n{'='*80}")
    print("BOOKMYSHOW EVENTS (Sorted by Distance, Date, Price)")
    print(f"{'='*80}")
    print(f"Total: {len(bms_events)} events")
    print()
    
    sorted_bms = sort_events(bms_events)
    print(f"{'#':<3} {'Title':<40} {'Category':<10} {'Venue':<25} {'Dist':<6} {'Date':<15} {'Price':<12} {'Status':<10}")
    print("-"*130)
    
    for i, e in enumerate(sorted_bms, 1):
        dist = get_venue_distance(e.venue)
        title = e.title[:38] + ".." if len(e.title) > 40 else e.title
        venue = e.venue[:23] + ".." if len(e.venue) > 25 else e.venue
        date = e.date[:13] + ".." if len(e.date) > 15 else e.date
        price = e.price[:10] + ".." if len(e.price) > 12 else e.price
        print(f"{i:<3} {title:<40} {e.category:<10} {venue:<25} {dist:>4.1f}km {date:<15} {price:<12} {e.ticket_status:<10}")
    
    print(f"\n{'='*80}")
    print("PAYTM INSIDER / DISTRICT EVENTS (Sorted by Distance, Date, Price)")
    print(f"{'='*80}")
    print(f"Total: {len(paytm_events)} events")
    print()
    
    sorted_paytm = sort_events(paytm_events)
    print(f"{'#':<3} {'Title':<40} {'Category':<10} {'Venue':<25} {'Dist':<6} {'Date':<15} {'Price':<12} {'Status':<10}")
    print("-"*130)
    
    for i, e in enumerate(sorted_paytm, 1):
        dist = get_venue_distance(e.venue)
        title = e.title[:38] + ".." if len(e.title) > 40 else e.title
        venue = e.venue[:23] + ".." if len(e.venue) > 25 else e.venue
        date = e.date[:13] + ".." if len(e.date) > 15 else e.date
        price = e.price[:10] + ".." if len(e.price) > 12 else e.price
        print(f"{i:<3} {title:<40} {e.category:<10} {venue:<25} {dist:>4.1f}km {date:<15} {price:<12} {e.ticket_status:<10}")

if __name__ == "__main__":
    asyncio.run(main())

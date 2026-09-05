import re
from typing import List
from datetime import datetime
from src.scrapers.base_scraper import Event

# Approximate coordinates of key Mumbai venues for distance sorting
# Origin: Anand Nagar, Sai Nagar, Thane West (19.2183, 72.9781)
USER_LOCATION = (19.2183, 72.9781)

# Venue coordinates (approximate, for major venues)
VENUE_COORDS = {
    "thane": (19.2183, 72.9781),
    "mulund": (19.1726, 72.9566),
    "bhandup": (19.1498, 72.9370),
    "ghatkopar": (19.0860, 72.9075),
    "andheri": (19.1136, 72.8697),
    "bandra": (19.0596, 72.8295),
    "worli": (19.0176, 72.8151),
    "lower parel": (18.9957, 72.8295),
    "bkc": (19.0658, 72.8679),
    "mahalaxmi": (18.9822, 72.8128),
    "santacruz": (19.0830, 72.8413),
    "malad": (19.1872, 72.8484),
    "borivali": (19.2307, 72.8567),
    "versova": (19.1318, 72.8172),
    "vile parle": (19.1007, 72.8421),
    "dadar": (19.0238, 72.8426),
    "navi mumbai": (19.0330, 73.0297),
    "mumbai": (19.0760, 72.8777),  # Default Mumbai center
}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km."""
    from math import radians, cos, sin, asin, sqrt
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * 6371 * asin(sqrt(a))

def get_venue_distance(venue: str) -> float:
    """Get approximate distance of venue from user location."""
    venue_lower = venue.lower()
    for key, coords in VENUE_COORDS.items():
        if key in venue_lower:
            return haversine_distance(USER_LOCATION[0], USER_LOCATION[1], coords[0], coords[1])
    return 50.0  # Default 50km for unknown venues

def parse_price(price: str) -> int:
    """Extract numeric price from string."""
    match = re.search(r'(\d+)', price.replace(",", ""))
    return int(match.group(1)) if match else 999999

def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime for sorting."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    if date_str == "Upcoming" or date_str == "Daily":
        return datetime(2099, 12, 31)  # Far future
    
    for i, m in enumerate(months):
        if m in date_str:
            try:
                # Extract day
                day_match = re.search(r'(\d{1,2})', date_str)
                day = int(day_match.group(1)) if day_match else 1
                month = i + 1
                year = 2026  # Current year
                return datetime(year, month, day)
            except:
                pass
    
    return datetime(2099, 12, 31)

def sort_events(events: List[Event]) -> List[Event]:
    """Sort events by distance, then date, then price."""
    return sorted(events, key=lambda e: (
        get_venue_distance(e.venue),
        parse_date(e.date),
        parse_price(e.price)
    ))

if __name__ == "__main__":
    # Test
    test_events = [
        Event("Test1", "10 Jan", "Thane", "₹500", "", "bms", "Available", "Music"),
        Event("Test2", "15 Feb", "Bandra", "₹300", "", "bms", "Available", "Comedy"),
        Event("Test3", "5 Jan", "Mulund", "₹1000", "", "bms", "Available", "Workshop"),
    ]
    
    sorted_events = sort_events(test_events)
    for e in sorted_events:
        print(f"{e.title} | {e.venue} | {get_venue_distance(e.venue):.1f}km | {e.date} | {e.price}")

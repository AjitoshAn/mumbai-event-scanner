#!/usr/bin/env python3
"""
Generate the Indian Maximalist Dashboard with sorted events.
"""
import sqlite3
import json
import re
from math import radians, cos, sin, asin, sqrt

# User location: Anand Nagar, Sai Nagar, Thane West
USER_LOC = (19.2183, 72.9781)

# Venue coordinates
VENUE_COORDS = {
    "thane": (19.2183, 72.9781),
    "dombivli": (19.2183, 73.0867),
    "kalyan": (19.2437, 73.1355),
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
    "goregaon": (19.1663, 72.8526),
    "versova": (19.1318, 72.8172),
    "vile parle": (19.1007, 72.8421),
    "dadar": (19.0238, 72.8426),
    "matunga": (19.0279, 72.8565),
    "navi mumbai": (19.0330, 73.0297),
    "sanpada": (19.0660, 73.0150),
    "mumbai": (19.0760, 72.8777),
    "jaipur": (26.9124, 75.7873),  # Out of city
    "delhi": (28.6139, 77.2090),   # Out of city
    "noida": (28.5355, 77.3910),   # Out of city
}

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * 6371 * asin(sqrt(a))

def get_distance(venue):
    venue_lower = venue.lower()
    for key, coords in VENUE_COORDS.items():
        if key in venue_lower:
            return haversine(USER_LOC[0], USER_LOC[1], coords[0], coords[1])
    return 50.0  # Default 50km for unknown

def parse_price(price):
    match = re.search(r'(\d+)', price.replace(",", ""))
    return int(match.group(1)) if match else 999999

def parse_date_for_sort(date_str):
    months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
              "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
    date_lower = date_str.lower()
    for m, num in months.items():
        if m in date_lower:
            day_match = re.search(r'(\d{1,2})', date_str)
            day = int(day_match.group(1)) if day_match else 1
            return num * 100 + day
    return 9999  # Far future for "Upcoming"

def main():
    conn = sqlite3.connect('events.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM events')
    rows = c.fetchall()
    conn.close()
    
    events = []
    for r in rows:
        dist = get_distance(r['venue'])
        events.append({
            "title": r['title'][:60],
            "venue": r['venue'][:40],
            "date": r['date'][:30],
            "price": r['price'],
            "url": r['url'],
            "source": r['source'],
            "category": r['category'] if r['category'] else "General",
            "status": r['ticket_status'],
            "distance": round(dist, 1),
            "_sort_date": parse_date_for_sort(r['date']),
            "_sort_price": parse_price(r['price'])
        })
    
    # Sort by: distance, then date, then price
    events.sort(key=lambda e: (e['distance'], e['_sort_date'], e['_sort_price']))
    
    # Remove sort keys
    for e in events:
        del e['_sort_date']
        del e['_sort_price']
    
    # Read template
    with open('indian_dashboard.html', 'r') as f:
        template = f.read()
    
    # Inject data
    html = template.replace('EVENTS_DATA_PLACEHOLDER', json.dumps(events, indent=2))
    
    # Write output
    with open('dashboard_live.html', 'w') as f:
        f.write(html)
    
    available = len([e for e in events if e['status'] != 'Coming Soon'])
    coming = len([e for e in events if e['status'] == 'Coming Soon'])
    print(f"✅ Generated dashboard_live.html")
    print(f"   Total: {len(events)} events")
    print(f"   Available: {available}")
    print(f"   Coming Soon: {coming}")

if __name__ == "__main__":
    main()

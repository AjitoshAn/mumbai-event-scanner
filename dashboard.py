#!/usr/bin/env python3
"""
Event Scanner - Web Dashboard
A simple Flask web app to view and filter events.
"""
from flask import Flask, render_template_string, request
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_PATH = "events.db"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Event Scanner Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #eee;
        }
        .header {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 1.5rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 {
            font-size: 1.8rem;
            background: linear-gradient(45deg, #00d4ff, #7c3aed);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .filters {
            display: flex;
            gap: 1rem;
            padding: 1rem 2rem;
            flex-wrap: wrap;
            background: rgba(0,0,0,0.2);
        }
        .filters select, .filters input {
            padding: 0.5rem 1rem;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 0.9rem;
        }
        .filters button {
            padding: 0.5rem 1.5rem;
            background: linear-gradient(45deg, #00d4ff, #7c3aed);
            border: none;
            border-radius: 8px;
            color: #fff;
            cursor: pointer;
            font-weight: 600;
        }
        .filters button:hover { opacity: 0.9; }
        .stats {
            display: flex;
            gap: 2rem;
            padding: 1rem 2rem;
            background: rgba(0,0,0,0.1);
        }
        .stat {
            background: rgba(255,255,255,0.05);
            padding: 1rem 1.5rem;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .stat-value { font-size: 1.8rem; font-weight: 700; color: #00d4ff; }
        .stat-label { font-size: 0.8rem; color: #888; text-transform: uppercase; }
        .events {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
            padding: 2rem;
        }
        .event-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 1.5rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .event-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .event-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #fff;
        }
        .event-venue { color: #888; font-size: 0.9rem; margin-bottom: 0.5rem; }
        .event-meta {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }
        .event-tag {
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .tag-price {
            background: linear-gradient(45deg, #00d4ff, #7c3aed);
            color: #fff;
        }
        .tag-category {
            background: rgba(255,255,255,0.1);
            color: #aaa;
        }
        .tag-source {
            background: rgba(255,193,7,0.2);
            color: #ffc107;
        }
        .tag-status {
            background: rgba(0,255,0,0.1);
            color: #0f0;
        }
        .tag-coming-soon {
            background: rgba(255,165,0,0.2);
            color: #ffa500;
        }
        .event-link {
            display: inline-block;
            margin-top: 1rem;
            color: #00d4ff;
            text-decoration: none;
            font-size: 0.85rem;
        }
        .event-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎫 Event Scanner Dashboard</h1>
    </div>
    
    <form class="filters" method="GET">
        <select name="source">
            <option value="">All Sources</option>
            <option value="bookmyshow" {{ 'selected' if source == 'bookmyshow' else '' }}>BookMyShow</option>
            <option value="paytm_insider" {{ 'selected' if source == 'paytm_insider' else '' }}>Paytm Insider</option>
            <option value="skillbox" {{ 'selected' if source == 'skillbox' else '' }}>Skillbox</option>
        </select>
        <select name="category">
            <option value="">All Categories</option>
            <option value="Music" {{ 'selected' if category == 'Music' else '' }}>Music</option>
            <option value="Comedy" {{ 'selected' if category == 'Comedy' else '' }}>Comedy</option>
            <option value="Workshop" {{ 'selected' if category == 'Workshop' else '' }}>Workshop</option>
            <option value="Theatre" {{ 'selected' if category == 'Theatre' else '' }}>Theatre</option>
        </select>
        <input type="text" name="search" placeholder="Search..." value="{{ search or '' }}">
        <button type="submit">Filter</button>
    </form>
    
    <div class="stats">
        <div class="stat">
            <div class="stat-value">{{ total_events }}</div>
            <div class="stat-label">Total Events</div>
        </div>
        <div class="stat">
            <div class="stat-value">{{ new_today }}</div>
            <div class="stat-label">New Today</div>
        </div>
    </div>
    
    <div class="events">
        {% for event in events %}
        <div class="event-card">
            <div class="event-title">{{ event.title[:60] }}</div>
            <div class="event-venue">📍 {{ event.venue[:40] }}</div>
            <div class="event-venue">📅 {{ event.date }}</div>
            <div class="event-meta">
                <span class="event-tag tag-price">{{ event.price }}</span>
                <span class="event-tag tag-category">{{ event.category }}</span>
                <span class="event-tag tag-source">{{ event.source }}</span>
                {% if event.ticket_status == 'Coming Soon' %}
                <span class="event-tag tag-coming-soon">Coming Soon</span>
                {% elif event.ticket_status == 'Available' %}
                <span class="event-tag tag-status">Available</span>
                {% endif %}
            </div>
            <a href="{{ event.url }}" target="_blank" class="event-link">View Details →</a>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

def get_events(source=None, category=None, search=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM events WHERE 1=1"
    params = []
    
    if source:
        query += " AND source = ?"
        params.append(source)
    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (title LIKE ? OR venue LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    query += " ORDER BY first_seen DESC LIMIT 100"
    
    c.execute(query, params)
    events = c.fetchall()
    
    # Get stats
    c.execute("SELECT COUNT(*) FROM events")
    total = c.fetchone()[0]
    
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM events WHERE date(first_seen) = ?", (today,))
    new_today = c.fetchone()[0]
    
    conn.close()
    return events, total, new_today

@app.route("/")
def index():
    source = request.args.get("source", "")
    category = request.args.get("category", "")
    search = request.args.get("search", "")
    
    events, total, new_today = get_events(source, category, search)
    
    return render_template_string(
        HTML_TEMPLATE,
        events=events,
        total_events=total,
        new_today=new_today,
        source=source,
        category=category,
        search=search
    )

if __name__ == "__main__":
    print("🚀 Starting Event Scanner Dashboard on http://localhost:8080")
    app.run(debug=True, port=8080)

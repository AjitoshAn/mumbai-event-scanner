# Mumbai Event Scanner 🎭

Automated event scraper for Mumbai events with OCR-based date extraction and a beautiful futuristic dashboard.

## Features

- 🔍 **Multi-source scraping**: BookMyShow, Paytm Insider
- 📅 **OCR Date Extraction**: Uses Tesseract to read dates from event posters
- 📱 **Telegram Notifications**: Get alerts for new events and price changes
- 🎨 **Futuristic Dashboard**: Beautiful glassmorphism UI with search, filters, and sorting
- ⏰ **Automated Scanning**: GitHub Actions workflow runs every 6 hours

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Install Tesseract (macOS)
brew install tesseract

# Run the scanner
python run_scan.py

# Generate dashboard
python generate_dashboard.py
```

### View Dashboard

Open `dashboard_live.html` in your browser.

## GitHub Actions Setup

The scanner can run automatically on GitHub Actions.

### 1. Enable GitHub Actions

Push this repository to GitHub. The workflow is already configured in `.github/workflows/scan-events.yml`.

### 2. Add Secrets (Optional, for Telegram)

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token (from @BotFather) |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |

### 3. Trigger Manually

Go to **Actions → Mumbai Event Scanner → Run workflow**

## Project Structure

```
event_scanner/
├── .github/workflows/
│   └── scan-events.yml      # GitHub Actions workflow
├── src/
│   ├── core/
│   │   ├── event_manager.py # Database & orchestration
│   │   └── sorter.py        # Distance/date/price sorting
│   ├── scrapers/
│   │   ├── base_scraper.py  # Base class
│   │   ├── bookmyshow.py    # BMS scraper with OCR
│   │   ├── paytm_insider.py # Paytm scraper
│   │   └── skillbox.py      # Skillbox scraper
│   └── notifications/
│       └── telegram.py      # Telegram notifier
├── run_scan.py              # Main entry point
├── generate_dashboard.py    # Dashboard generator
├── indian_dashboard.html    # Dashboard template
├── dashboard_live.html      # Generated dashboard
└── events.db                # SQLite database
```

## Dashboard Features

- 🔍 Real-time search
- 📊 Sort by distance, date, or price
- 🎵 Category filters: Music, Comedy, Workshop, Theatre
- 📡 Source filters: BookMyShow, Paytm Insider
- ✨ Animated particle backgrounds
- 💎 Glassmorphism design

## License

MIT

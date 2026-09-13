#!/usr/bin/env python3
"""
Mumbai Event Scanner - GitHub Actions Runner

This script is designed to run in CI environments.
It runs the full scan pipeline and sends notifications.
"""
import asyncio
import logging
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.event_manager import EventManager
from notifications.telegram import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('event_scanner')

async def main():
    logger.info("🚀 Starting Mumbai Event Scanner")
    
    # Initialize
    manager = EventManager()
    
    # Run the scan
    logger.info("📡 Running scrapers...")
    new_events, price_changes, status_changes = await manager.run_scan()
    
    logger.info(f"✅ Scan complete!")
    logger.info(f"   New events: {len(new_events)}")
    logger.info(f"   Price changes: {len(price_changes)}")
    logger.info(f"   Status changes: {len(status_changes)}")
    
    # Send Telegram notifications if configured
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if bot_token and chat_id:
        logger.info("📱 Sending Telegram notifications...")
        notifier = TelegramNotifier(bot_token, chat_id)
        
        # Notify about new events
        if new_events:
            for event in new_events[:10]:  # Limit to 10
                await notifier.send_new_event_notification(event)
        
        # Notify about price changes
        for change in price_changes[:5]:
            await notifier.send_price_change_notification(
                change['title'],
                change['old_price'],
                change['new_price'],
                change['url']
            )
        
        # Notify about status changes (Coming Soon -> Available)
        for change in status_changes[:5]:
            await notifier.send_status_change_notification(
                change['title'],
                change['old_status'],
                change['new_status'],
                change['url']
            )
        
        # Send summary
        await notifier.send_summary(
            total_events=len(new_events) + len(price_changes) + len(status_changes),
            new_events=len(new_events),
            price_changes=len(price_changes)
        )
        
        logger.info("✅ Notifications sent!")
    else:
        logger.info("⚠️ Telegram not configured, skipping notifications")
    
    # Print summary
    print("\n" + "="*50)
    print("📊 SCAN SUMMARY")
    print("="*50)
    print(f"New Events: {len(new_events)}")
    print(f"Price Changes: {len(price_changes)}")
    print(f"Status Changes: {len(status_changes)}")
    
    if new_events:
        print("\n🆕 NEW EVENTS:")
        for e in new_events[:5]:
            print(f"  • {e.title[:50]} | {e.date} | {e.price}")
    
    print("="*50 + "\n")
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

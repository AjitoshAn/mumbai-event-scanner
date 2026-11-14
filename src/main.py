#!/usr/bin/env python3
"""
Event Scanner - Main Entry Point
Scans event platforms and sends alerts for new events, price drops, and ticket availability.
"""
import asyncio
import logging
import argparse
from src.core.event_manager import EventManager
from src.notifications.notifier import Notifier
from src.notifications.telegram import TelegramNotifier

async def main():
    parser = argparse.ArgumentParser(description="Event Scanner - Mumbai/Pune Event Alerts")
    parser.add_argument("--loop", action="store_true", help="Run in continuous monitoring mode")
    parser.add_argument("--interval", type=int, default=300, help="Scan interval in seconds (default: 300)")
    parser.add_argument("--no-telegram", action="store_true", help="Disable Telegram notifications")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    args = parser.parse_args()

    log_level = logging.WARNING if args.quiet else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("main")

    manager = EventManager()
    desktop_notifier = Notifier()
    telegram_notifier = TelegramNotifier() if not args.no_telegram else None

    logger.info("🚀 Starting Event Scanner...")
    print("=" * 60)
    print("  EVENT SCANNER - Mumbai/Pune Live Events")
    print("=" * 60)

    scan_count = 0
    while True:
        scan_count += 1
        try:
            logger.info(f"Starting scan #{scan_count}...")
            
            # Run scan and get results
            new_events, price_changes, status_changes = await manager.run_scan()
            
            # === NEW EVENTS ===
            if new_events:
                count = len(new_events)
                logger.info(f"🆕 Found {count} new events!")
                
                # Desktop notification
                desktop_notifier.play_sound()
                desktop_notifier.send_notification(
                    "New Events Found!", 
                    f"Found {count} new events in Mumbai/Pune."
                )
                
                # Telegram notification
                if telegram_notifier and telegram_notifier.enabled:
                    await telegram_notifier.send_new_events_alert(new_events)
                
                # Console output
                print(f"\n🆕 NEW EVENTS ({count}):")
                for e in new_events[:10]:
                    print(f"  • {e.title[:45]} | {e.price}")
                if count > 10:
                    print(f"  ...and {count - 10} more")
            
            # === PRICE CHANGES ===
            if price_changes:
                count = len(price_changes)
                logger.info(f"💰 Found {count} price changes!")
                
                desktop_notifier.send_notification(
                    "Price Change Detected!",
                    f"{count} events have price changes."
                )
                
                if telegram_notifier and telegram_notifier.enabled:
                    await telegram_notifier.send_price_alert(price_changes)
                
                print(f"\n💰 PRICE CHANGES ({count}):")
                for p in price_changes:
                    print(f"  • {p['title'][:35]}: {p['old_price']} → {p['new_price']}")
            
            # === STATUS CHANGES (Coming Soon -> Available) ===
            if status_changes:
                count = len(status_changes)
                logger.info(f"🔥 {count} events now have tickets available!")
                
                desktop_notifier.play_sound()
                desktop_notifier.send_notification(
                    "🔥 Tickets Now Available!",
                    f"{count} events just opened for booking!"
                )
                
                if telegram_notifier and telegram_notifier.enabled:
                    await telegram_notifier.send_status_alert(status_changes)
                
                print(f"\n🔥 TICKETS NOW AVAILABLE ({count}):")
                for s in status_changes:
                    print(f"  • {s['title'][:45]}")
            
            # Summary
            if not new_events and not price_changes and not status_changes:
                print(f"\n✅ Scan #{scan_count} complete. No changes detected.")
            else:
                print(f"\n✅ Scan #{scan_count} complete.")

        except Exception as e:
            logger.error(f"Error in scan loop: {e}")
            print(f"\n❌ Error: {e}")

        if not args.loop:
            break
            
        print(f"\n⏰ Next scan in {args.interval} seconds...")
        await asyncio.sleep(args.interval)

if __name__ == "__main__":
    asyncio.run(main())

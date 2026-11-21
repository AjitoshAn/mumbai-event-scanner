import os
import logging
import aiohttp
from typing import List, Optional

class TelegramNotifier:
    """
    Sends notifications to Telegram.
    
    Setup:
    1. Create a bot with @BotFather on Telegram
    2. Get your chat ID by messaging @userinfobot
    3. Set environment variables:
       - TELEGRAM_BOT_TOKEN
       - TELEGRAM_CHAT_ID
    """
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.logger = logging.getLogger("notifications.telegram")
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        
        if not self.bot_token or not self.chat_id:
            self.logger.warning("Telegram credentials not set. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars.")
            self.enabled = False
        else:
            self.enabled = True
            self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    async def send_message(self, message: str) -> bool:
        """Send a message to Telegram."""
        if not self.enabled:
            self.logger.debug("Telegram not configured, skipping")
            return False
        
        try:
            import ssl
            import certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                payload = {
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                async with session.post(self.api_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info("Telegram message sent successfully")
                        return True
                    else:
                        self.logger.error(f"Telegram API error: {await response.text()}")
                        return False
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False

    async def send_new_events_alert(self, events: List) -> bool:
        """Send formatted alert for new events."""
        if not events:
            return False
        
        message = f"🎫 <b>{len(events)} New Events Found!</b>\n\n"
        
        for e in events[:10]:  # Limit to 10 to avoid message length limits
            message += f"• <b>{e.title[:40]}</b>\n"
            message += f"  📍 {e.venue[:30]}\n"
            message += f"  💰 {e.price}\n"
            message += f"  🔗 {e.url}\n\n"
        
        if len(events) > 10:
            message += f"...and {len(events) - 10} more events"
        
        return await self.send_message(message)

    async def send_price_alert(self, price_changes: List) -> bool:
        """Send alert for price changes."""
        if not price_changes:
            return False
        
        message = f"💰 <b>{len(price_changes)} Price Changes Detected!</b>\n\n"
        
        for p in price_changes[:10]:
            message += f"• <b>{p['title'][:35]}</b>\n"
            message += f"  {p['old_price']} → {p['new_price']}\n\n"
        
        return await self.send_message(message)

    async def send_status_alert(self, status_changes: List) -> bool:
        """Send alert for Coming Soon -> Available tickets."""
        if not status_changes:
            return False
        
        message = f"🔥 <b>Tickets Now Available!</b>\n\n"
        
        for s in status_changes:
            message += f"• <b>{s['title'][:40]}</b>\n"
            message += f"  🔗 {s['url']}\n\n"
        
        return await self.send_message(message)

    # Individual notification methods for run_scan.py compatibility
    async def send_new_event_notification(self, event) -> bool:
        """Send notification for a single new event."""
        message = f"🎫 <b>New Event!</b>\n\n"
        message += f"<b>{event.title}</b>\n"
        message += f"📍 {event.venue}\n"
        message += f"📅 {event.date}\n"
        message += f"💰 {event.price}\n"
        message += f"🔗 {event.url}"
        return await self.send_message(message)

    async def send_price_change_notification(self, title: str, old_price: str, new_price: str, url: str) -> bool:
        """Send notification for a price change."""
        message = f"💰 <b>Price Change!</b>\n\n"
        message += f"<b>{title}</b>\n"
        message += f"{old_price} → {new_price}\n"
        message += f"🔗 {url}"
        return await self.send_message(message)

    async def send_status_change_notification(self, title: str, old_status: str, new_status: str, url: str) -> bool:
        """Send notification for ticket status change."""
        message = f"🔥 <b>Tickets Now Available!</b>\n\n"
        message += f"<b>{title}</b>\n"
        message += f"{old_status} → {new_status}\n"
        message += f"🔗 {url}"
        return await self.send_message(message)

    async def send_summary(self, total_events: int, new_events: int, price_changes: int) -> bool:
        """Send scan summary."""
        message = f"📊 <b>Scan Complete!</b>\n\n"
        message += f"🆕 New events: {new_events}\n"
        message += f"💰 Price changes: {price_changes}\n"
        message += f"📈 Total updates: {total_events}"
        return await self.send_message(message)


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    
    notifier = TelegramNotifier()
    
    if notifier.enabled:
        result = asyncio.run(notifier.send_message("🧪 Event Scanner test message!"))
        print(f"Message sent: {result}")
    else:
        print("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env variables.")


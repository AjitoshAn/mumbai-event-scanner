import os
import logging

class Notifier:
    def __init__(self):
        self.logger = logging.getLogger("notifications.notifier")

    def send_notification(self, title: str, message: str):
        """
        Sends a Mac OS desktop notification.
        """
        try:
            # Escape quotes
            safe_title = title.replace('"', '\\"')
            safe_message = message.replace('"', '\\"')
            
            cmd = f'osascript -e \'display notification "{safe_message}" with title "{safe_title}" sound name "Glass"\''
            os.system(cmd)
            self.logger.info(f"Notification sent: {title} - {message}")
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")

    def play_sound(self):
        """
        Plays a terminal sound.
        """
        try:
            # Mac specific sound
            os.system("afplay /System/Library/Sounds/Glass.aiff")
        except:
            print('\a') # Fallback to bell

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    n = Notifier()
    n.send_notification("Event Scanner", "Test notification")
    n.play_sound()

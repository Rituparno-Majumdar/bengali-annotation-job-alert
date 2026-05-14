import os
import requests
import logging

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not fully set. Notifications will be disabled.")
            
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_job_alert(self, job):
        """
        Sends a job alert to the configured Telegram chat.
        job should be a dictionary with keys: title, company, url, source, description
        """
        if not self.bot_token or not self.chat_id:
            logger.error("Cannot send alert: Telegram credentials missing.")
            return False

        message = (
            f"🚨 <b>New Job Alert: {job.get('source', 'Web')}</b>\n\n"
            f"<b>Title:</b> {job.get('title')}\n"
            f"<b>Company:</b> {job.get('company', 'Unknown')}\n\n"
            f"<a href='{job.get('url')}'>Apply Here</a>"
        )

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }

        try:
            response = requests.post(f"{self.base_url}/sendMessage", json=payload)
            response.raise_for_status()
            logger.info(f"Successfully sent alert for: {job.get('title')}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

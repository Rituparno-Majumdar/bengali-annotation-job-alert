import html
import os
import requests
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def url_safe(url: str) -> str:
    return url.replace('&', '&amp;') if url else '#'


def is_valid_url(url: str) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception:
        return False

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

        raw_url = job.get('url', '')
        if is_valid_url(raw_url):
            apply_button = f'<a href="{url_safe(raw_url)}">Apply Here</a>'
        else:
            apply_button = "⚠️ Link unavailable — search the title on the source site."

        message = (
            f"🚨 <b>New Job Alert: {html.escape(job.get('source', 'Web'))}</b>\n\n"
            f"<b>Title:</b> {html.escape(job.get('title') or 'N/A')}\n"
            f"<b>Company:</b> {html.escape(job.get('company', 'Unknown'))}\n\n"
            f"{apply_button}"
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

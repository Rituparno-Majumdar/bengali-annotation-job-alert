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
            logger.warning("Telegram credentials not set. Notifications disabled.")

        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def _post(self, payload: dict) -> bool:
        if not self.bot_token or not self.chat_id:
            logger.error("Cannot send: Telegram credentials missing.")
            return False
        try:
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json=payload,
                timeout=15,
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram POST failed: {e}")
            return False

    def send_job_alert(self, job: dict) -> bool:
        raw_url = job.get('url', '')
        apply_line = (
            f'<a href="{url_safe(raw_url)}">Apply Here</a>'
            if is_valid_url(raw_url)
            else "⚠️ Link unavailable — search the title on the source site."
        )
        message = (
            f"🚨 <b>New Job: {html.escape(job.get('source', 'Web'))}</b>\n\n"
            f"<b>Title:</b> {html.escape(job.get('title') or 'N/A')}\n"
            f"<b>Company:</b> {html.escape(job.get('company', 'Unknown'))}\n\n"
            f"{apply_line}"
        )
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        success = self._post(payload)
        if success:
            logger.info(f"Alert sent: {job.get('title')}")
        return success

    def send_heartbeat(self, source_summary: list, total_new: int, error_count: int = 0, total_sources: int = 0) -> None:
        """Send a run summary so silence = a real problem."""
        if not self.bot_token or not self.chat_id:
            return
        lines = "\n".join(f"  • {s}" for s in source_summary)
        healthy = total_sources - error_count
        health_line = f"<b>Sources healthy:</b> {healthy}/{total_sources}\n\n" if total_sources else ""
        message = (
            f"✅ <b>Job Alert Run Complete</b>\n\n"
            f"<b>New alerts sent:</b> {total_new}\n"
            f"{health_line}"
            f"<b>Per source:</b>\n{lines}"
        )
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        success = self._post(payload)
        if success:
            logger.info("Heartbeat sent.")
        else:
            logger.error("Heartbeat send failed.")

import os
from dotenv import load_dotenv
from notifier import TelegramNotifier

def test_alert():
    load_dotenv()
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env file.")
        return

    notifier = TelegramNotifier()
    
    # Create a mock job to test
    test_job = {
        "title": "Bengali AI Annotator (Test Alert)",
        "company": "DataAnnotation Tech",
        "url": "https://www.dataannotation.tech",
        "source": "Test Script",
        "description": "This is a test notification to verify the Telegram bot is working."
    }
    
    print("Sending test notification...")
    success = notifier.send_job_alert(test_job)
    
    if success:
        print("Success! Check your Telegram messages. You should see a new alert from your bot.")
    else:
        print("Failed to send notification. Please check the logs.")

if __name__ == "__main__":
    test_alert()

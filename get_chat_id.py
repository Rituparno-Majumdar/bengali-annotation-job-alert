import os
import requests
from dotenv import load_dotenv

def get_chat_id():
    load_dotenv()
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env file.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        print("Checking for messages to the bot...")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data.get("ok"):
            results = data.get("result", [])
            if not results:
                print("\nNo messages found.")
                print("ACTION REQUIRED: Please go to Telegram and send a message (like 'hello') to your bot @Bengaliannotationtracker_bot")
                print("Then run this script again.")
            else:
                # Get the latest message
                latest = results[-1]
                if "message" in latest:
                    chat_id = latest["message"]["chat"]["id"]
                    first_name = latest["message"]["chat"].get("first_name", "User")
                    print(f"\nSuccess! Found a message from {first_name}.")
                    print(f"Your Chat ID is: {chat_id}")
                    print(f"\nPlease add this line to your .env file:")
                    print(f"TELEGRAM_CHAT_ID={chat_id}")
                else:
                    print("\nFound updates but no direct messages. Try sending a normal text message to the bot.")
        else:
            print(f"\nError from Telegram API: {data.get('description')}")
            
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Telegram API: {e}")

if __name__ == "__main__":
    get_chat_id()

# Bengali Data Annotation Job Tracker

An automated script that searches for Bengali data annotation jobs and sends real-time alerts to your Telegram.

## Setup Instructions

### 1. Get a Telegram Bot Token
1. Open the Telegram app and search for `@BotFather`.
2. Send the message `/newbot` to BotFather.
3. Choose a name for your bot (e.g., `Bengali Job Tracker`).
4. Choose a username for your bot (must end in `bot`, e.g., `BengaliTrackerBot`).
5. BotFather will reply with a message containing your **Bot Token** (it looks like `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`). Copy this token.

### 2. Get Your Telegram Chat ID
1. In Telegram, search for `@userinfobot` and start a chat with it.
2. It will reply with your `Id` (e.g., `987654321`). Copy this ID.
3. Start a chat with your newly created bot and send it a test message like "Hello". (This is required so the bot is allowed to message you).

### 3. Configure the Project
1. In this directory (`/Users/pari/Documents/ANTIGRAVITY/jobsearch/dataannotation`), create a new file named `.env`.
2. Add your credentials to the `.env` file like this:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
SERPAPI_KEY=optional_serpapi_key_here
```

### 4. Run the Tracker
You can run the script manually to check for jobs:
```bash
source venv/bin/activate
python main.py
```

### 5. Automate It
To have this run automatically every hour, you can set up a crontab.
1. Open terminal and run `crontab -e`
2. Add the following line to run it every hour:
`0 * * * * cd /Users/pari/Documents/ANTIGRAVITY/jobsearch/dataannotation && source venv/bin/activate && python main.py`

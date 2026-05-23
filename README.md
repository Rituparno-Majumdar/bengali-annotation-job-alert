# Bengali Annotation Job Alert

![Scraper](https://github.com/Rituparno-Majumdar/bengali-annotation-job-alert/actions/workflows/scraper.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

Automated job monitor for Bengali AI data annotation and NLP/LLM training roles. Scrapes LinkedIn, Remotive, and RSS feeds every 6 hours, deduplicates results, and delivers instant Telegram alerts for new postings.

---

## Why This Exists

Bengali is a high-demand, low-resource language in NLP and LLM training pipelines. Relevant annotation roles appear infrequently and are scattered across multiple platforms. Manual checking is unreliable. This tool monitors all sources continuously and delivers alerts the moment a matching role is posted.

---

## How It Works

```
LinkedIn (5 queries)  ──┐
Remotive API           ──┼──► Scraper ──► Dedup (seen_jobs.json) ──► Telegram Alert
RSS / Atom feeds       ──┘
          ▲
    GitHub Actions (every 6h)
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| Scraping | BeautifulSoup4, Requests, lxml |
| Job sources | LinkedIn (web), Remotive (API), RSS/Atom |
| Notifications | Telegram Bot API |
| Automation | GitHub Actions (cron: every 6 hours) |
| State tracking | `seen_jobs.json` (committed, auto-updated by CI) |

---

## Sources Monitored

- **LinkedIn** — 5 search queries: `bengali data annotation`, `bengali linguist`, `bengali NLP`, `bengali language expert`, `bengali AI trainer`
- **Remotive** — API query for `bengali` across remote tech roles
- **RSS/Atom feeds** — Configurable feed list for job boards

---

## Setup

### 1. Prerequisites

- Python 3.11+
- A Telegram bot token (create via [@BotFather](https://t.me/BotFather))
- Your Telegram chat ID (run `python get_chat_id.py` after bot setup)

### 2. Environment Variables

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
SERPAPI_KEY=optional_serpapi_key
```

### 3. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run Manually

```bash
python main.py
```

### 5. Schedule Locally (cron)

```cron
0 * * * * cd /path/to/project && source venv/bin/activate && python main.py
```

### 6. Run on GitHub Actions

Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` as repository secrets under **Settings > Secrets and variables > Actions**. The workflow in `.github/workflows/scraper.yml` handles the rest — it runs every 6 hours and auto-commits updates to `seen_jobs.json`.

---

## Project Structure

```
bengali-annotation-job-alert/
├── main.py               # Orchestrator: loads state, runs scrapers, dispatches alerts
├── scraper.py            # LinkedIn, Remotive, and RSS scrapers with dedup logic
├── notifier.py           # Telegram Bot notifier
├── get_chat_id.py        # Utility to retrieve your Telegram chat ID
├── test_notification.py  # Smoke test for Telegram connection
├── seen_jobs.json        # Persisted job IDs (auto-updated by GitHub Actions)
├── requirements.txt
└── .github/workflows/
    └── scraper.yml       # Scheduled CI workflow
```

---

## Author

Built by **Rituparno Majumdar** as part of a Bengali NLP and AI annotation portfolio.
- GitHub: [@Rituparno-Majumdar](https://github.com/Rituparno-Majumdar)
- Domain focus: Bengali language data annotation, LLM training data, NLP tooling

---

## License

MIT

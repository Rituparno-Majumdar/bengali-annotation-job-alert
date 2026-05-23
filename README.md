# Bengali Annotation Job Alert

![Scraper](https://github.com/Rituparno-Majumdar/bengali-annotation-job-alert/actions/workflows/scraper.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

Automated job monitor for Bengali AI data annotation and NLP/LLM training roles. Monitors 11 sources — vendor ATS boards, job aggregators, and RSS feeds — every 6 hours, deduplicates results, and delivers instant Telegram alerts for new postings.

---

## Why This Exists

Bengali is a high-demand, low-resource language in NLP and LLM training pipelines. Relevant annotation roles appear infrequently and are scattered across multiple platforms. Manual checking is unreliable. This tool monitors all sources continuously and delivers alerts the moment a matching role is posted.

---

## How It Works

```
Vendor ATS boards      ──┐
  (RWS, Appen, Scale,    │
   Innodata, Remotasks)  │
Indeed + Google Jobs   ──┼──► Scraper ──► Dedup (seen_jobs.json) ──► Telegram Alert
General job APIs       ──┤
  (Remotive, RemoteOK,   │
   Arbeitnow, WWR RSS)   │
LinkedIn (best-effort) ──┘
          ▲
    GitHub Actions (every 6h) + Telegram heartbeat after each run
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| Scraping | BeautifulSoup4, Requests, lxml, python-jobspy |
| Job sources | Greenhouse API, Lever API, Indeed, Google Jobs, Remotive, RemoteOK, Arbeitnow, WeWorkRemotely RSS, LinkedIn |
| Notifications | Telegram Bot API |
| Automation | GitHub Actions (cron: every 6 hours) |
| State tracking | `seen_jobs.json` (committed, auto-updated by CI) |

---

## Sources Monitored

**Vendor ATS boards** (highest signal — direct from annotation companies):
- **RWS TrainAI** (Lever) — AI data specialist and linguistic auditor roles
- **Appen** (Lever) — language data collection and annotation gigs
- **Scale AI** (Greenhouse) — data labeling and AI training roles
- **Innodata** (Lever) — NLP and data annotation positions
- **Remotasks / Telus Digital AI** (Greenhouse) — AI training task roles

**Job aggregators** (broad coverage, no API key required):
- **Indeed + Google Jobs** (via python-jobspy) — aggregates from Outlier, Alignerr, Sigma AI, YPAI, and thousands of other sources; 4 search queries: `bengali annotation`, `bangla linguist AI training`, `bengali NLP data labeling`, `indic language annotation`
- **Remotive** — remote tech job API; queries: `annotation`, `linguist`, `bengali`
- **RemoteOK** — remote job API with tag-based filtering
- **Arbeitnow** — European remote job board API

**RSS feeds:**
- **WeWorkRemotely** — "All Other Remote Jobs" category feed

**Best-effort:**
- **LinkedIn** — 5 search queries; may be blocked on CI runners, included as supplementary coverage

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
├── scraper.py            # All scrapers: vendor ATS, job aggregators, RSS, LinkedIn
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

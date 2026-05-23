import os
import json
import logging
import time
from dotenv import load_dotenv

load_dotenv()

from scraper import get_all_scrapers
from notifier import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tracker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SEEN_JOBS_FILE = "seen_jobs.json"


def load_seen_jobs():
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def save_seen_job(job_id, seen_jobs):
    seen_jobs.append(job_id)
    with open(SEEN_JOBS_FILE, 'w') as f:
        json.dump(seen_jobs, f, indent=2)


def main():
    logger.info("Starting Bengali Annotation Job Alert...")

    seen_jobs = load_seen_jobs()
    notifier = TelegramNotifier()
    scrapers = get_all_scrapers()

    new_jobs_found = 0
    source_summary = []

    for scraper in scrapers:
        scraper_name = scraper.__class__.__name__
        source_label = getattr(scraper, 'source_name', None) \
            or getattr(scraper, 'company_name', None) \
            or scraper_name
        logger.info(f"Running: {scraper_name} ({source_label})")

        try:
            jobs = scraper.fetch_jobs()
        except Exception as e:
            logger.error(f"Scraper {scraper_name} crashed: {e}")
            source_summary.append(f"{source_label}: ERROR")
            continue

        source_new = 0
        for job in jobs:
            job_id = job.get('id')
            if not job_id:
                continue
            if job_id not in seen_jobs:
                logger.info(f"New job: {job.get('title')} @ {job.get('company')}")
                success = notifier.send_job_alert(job)
                if success:
                    save_seen_job(job_id, seen_jobs)
                    new_jobs_found += 1
                    source_new += 1
                    time.sleep(1)
                else:
                    logger.error(f"Failed to notify for: {job_id}")
            else:
                logger.debug(f"Already seen: {job_id}")

        source_summary.append(f"{source_label}: {source_new} new")

    logger.info(f"Finished. Total new alerts: {new_jobs_found}")

    error_count = sum(1 for s in source_summary if s.endswith(": ERROR"))
    notifier.send_heartbeat(source_summary, new_jobs_found, error_count, len(scrapers))


if __name__ == "__main__":
    main()

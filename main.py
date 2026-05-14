import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from scraper import get_all_scrapers
from notifier import TelegramNotifier

# Configure logging
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
        json.dump(seen_jobs, f)

def main():
    logger.info("Starting Bengali Data Annotation Job Tracker...")
    
    seen_jobs = load_seen_jobs()
    notifier = TelegramNotifier()
    scrapers = get_all_scrapers()
    
    new_jobs_found = 0
    
    for scraper in scrapers:
        logger.info(f"Running scraper: {scraper.__class__.__name__}")
        jobs = scraper.fetch_jobs()
        
        for job in jobs:
            job_id = job.get('id')
            if not job_id:
                continue
                
            if job_id not in seen_jobs:
                logger.info(f"New job found: {job.get('title')}")
                
                # Send notification
                success = notifier.send_job_alert(job)
                
                if success:
                    save_seen_job(job_id, seen_jobs)
                    new_jobs_found += 1
                else:
                    logger.error(f"Failed to notify for job: {job_id}")
            else:
                logger.debug(f"Job already seen: {job_id}")
                
    logger.info(f"Finished check. Sent {new_jobs_found} new alerts.")

if __name__ == "__main__":
    main()

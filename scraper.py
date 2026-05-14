import requests
from bs4 import BeautifulSoup
import re
import os
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, keywords=None):
        # Default keywords to look for if none provided
        self.keywords = keywords or ["bengali", "data annotation", "ai training", "prompt engineer", "bengali linguist"]

    def fetch_jobs(self):
        """Must return a list of dictionaries with keys: id, title, company, url, source, description"""
        raise NotImplementedError

    def matches_keywords(self, text):
        if not text:
            return False
        text = text.lower()
        # Look for at least 'bengali' and ('data annotation' or similar)
        # Actually, let's just make sure "bengali" is in the text for these specific searches
        return "bengali" in text

class RSSScraper(BaseScraper):
    def __init__(self, feed_url, source_name, keywords=None):
        super().__init__(keywords)
        self.feed_url = feed_url
        self.source_name = source_name

    def fetch_jobs(self):
        jobs = []
        try:
            response = requests.get(self.feed_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'xml') # 'xml' parser for RSS/Atom
            
            items = soup.find_all(['item', 'entry'])
            for item in items:
                title = item.title.text if item.title else ""
                description = item.description.text if item.description else (item.content.text if item.content else "")
                
                # Get URL
                url = ""
                link_tag = item.find('link')
                if link_tag:
                    if link_tag.text:
                        url = link_tag.text
                    elif link_tag.get('href'):
                        url = link_tag.get('href')

                # Unique ID (usually guid or url)
                job_id = item.guid.text if item.guid else url
                
                # Simple keyword matching
                if self.matches_keywords(title) or self.matches_keywords(description):
                    jobs.append({
                        "id": job_id,
                        "title": title.strip(),
                        "company": "See listing", # RSS often doesn't separate company clearly
                        "url": url.strip(),
                        "source": self.source_name,
                        "description": description.strip()
                    })
            logger.info(f"Fetched {len(jobs)} matching jobs from {self.source_name}")
        except Exception as e:
            logger.error(f"Error fetching RSS from {self.source_name}: {e}")
        return jobs

class RemotiveScraper(BaseScraper):
    def __init__(self, keywords=None):
        super().__init__(keywords)
    
    def fetch_jobs(self):
        jobs = []
        url = "https://remotive.com/api/remote-jobs"
        params = {"search": "bengali"}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for job in data.get("jobs", []):
                title = job.get("title", "")
                description = job.get("description", "")
                
                # Check our keyword logic just to be safe
                if self.matches_keywords(title) or self.matches_keywords(description):
                    # Clean up the HTML description so it's readable
                    clean_desc = ""
                    if description:
                        clean_desc = BeautifulSoup(description, "html.parser").get_text(separator=' ', strip=True)[:500]
                        
                    jobs.append({
                        "id": str(job.get("id", job.get("url"))),
                        "title": title,
                        "company": job.get("company_name", "Unknown"),
                        "url": job.get("url", "No link found"),
                        "source": "Remotive",
                        "description": clean_desc
                    })
            logger.info(f"Fetched {len(jobs)} matching jobs from Remotive")
        except Exception as e:
            logger.error(f"Error fetching from Remotive: {e}")
        return jobs

class LinkedInScraper(BaseScraper):
    def __init__(self, keywords=None):
        super().__init__(keywords)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }
        
    def fetch_jobs(self):
        jobs = []
        # Search LinkedIn's public jobs portal for remote positions
        url = "https://www.linkedin.com/jobs/search?keywords=bengali%20data%20annotation&location=Remote"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            cards = soup.find_all('div', class_='base-card')
            for card in cards:
                title_elem = card.find('h3', class_='base-search-card__title')
                company_elem = card.find('h4', class_='base-search-card__subtitle')
                link_elem = card.find('a', class_='base-card__full-link')
                
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                company = company_elem.text.strip() if company_elem else "Unknown"
                url = link_elem['href'].split('?')[0] if link_elem else "No link found" # Clean tracking params
                
                # Check keywords since LinkedIn's own search might return loosely related jobs
                if self.matches_keywords(title):
                    job_id = url.split('-')[-1] if '-' in url else url
                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": company,
                        "url": url,
                        "source": "LinkedIn",
                        "description": "View LinkedIn for full description."
                    })
            logger.info(f"Fetched {len(jobs)} matching jobs from LinkedIn")
        except Exception as e:
            logger.error(f"Error fetching from LinkedIn: {e}")
            
        return jobs

def get_all_scrapers():
    """
    Configure and return a list of all active scrapers.
    """
    scrapers = [
        # RemoteOK and WeWorkRemotely are just examples. 
        # In practice, you might generate custom RSS feeds from Indeed using services like RSS.app
        RSSScraper("https://weworkremotely.com/categories/remote-data-programming-jobs.rss", "WeWorkRemotely"),
        RemotiveScraper(),
        LinkedInScraper()
    ]
    return scrapers

import os
import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

# --- Keyword matching ---

_SPECIFIC_LANGUAGE = ["bengali", "bangla", "bn-in", "bn-bd"]
_UMBRELLA_LANGUAGE = ["indic", "indian language", "south asian language", "multilingual annotation"]
_ROLE_TOKENS = [
    "annotat", "label", "linguist", "transcri",
    "ai train", "llm", "rlhf", "prompt", "language data", "translat",
]


class BaseScraper:
    def fetch_jobs(self):
        """Return list of dicts: id, title, company, url, source, description."""
        raise NotImplementedError

    def matches_keywords(self, title, description=""):
        text = f"{title or ''} {description or ''}".lower()
        if any(t in text for t in _SPECIFIC_LANGUAGE):
            return True
        if any(u in text for u in _UMBRELLA_LANGUAGE):
            if any(r in text for r in _ROLE_TOKENS):
                return True
        return False

    def _get(self, url, **kwargs):
        """GET with one retry on failure."""
        for attempt in range(2):
            try:
                resp = requests.get(url, timeout=15, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                if attempt == 0:
                    time.sleep(3)
                else:
                    raise


class RSSScraper(BaseScraper):
    def __init__(self, feed_url, source_name):
        self.feed_url = feed_url
        self.source_name = source_name

    def fetch_jobs(self):
        jobs = []
        try:
            resp = self._get(self.feed_url)
            soup = BeautifulSoup(resp.content, 'xml')
            for item in soup.find_all(['item', 'entry']):
                title = item.title.text if item.title else ""
                description = ""
                if item.description:
                    description = item.description.text
                elif item.content:
                    description = item.content.text

                url = ""
                link_tag = item.find('link')
                if link_tag:
                    url = (link_tag.text or link_tag.get('href', '')).strip()

                job_id = (item.guid.text if item.guid else url)
                if not job_id:
                    continue

                if self.matches_keywords(title, description):
                    jobs.append({
                        "id": job_id,
                        "title": title.strip(),
                        "company": "See listing",
                        "url": url,
                        "source": self.source_name,
                        "description": description[:300].strip(),
                    })
        except Exception as e:
            logger.error(f"RSS error ({self.source_name}): {e}")
        logger.info(f"RSS {self.source_name}: {len(jobs)} matching jobs")
        return jobs


class RemotiveScraper(BaseScraper):
    def fetch_jobs(self):
        jobs = []
        seen_ids = set()
        try:
            for term in ("annotation", "linguist", "bengali"):
                resp = self._get(
                    "https://remotive.com/api/remote-jobs",
                    params={"search": term}
                )
                for job in resp.json().get("jobs", []):
                    title = job.get("title", "")
                    desc_raw = job.get("description", "") or ""
                    desc = BeautifulSoup(desc_raw, "html.parser").get_text(separator=' ', strip=True)[:400] if desc_raw else ""
                    if self.matches_keywords(title, desc):
                        job_id = f"remotive:{job.get('id', job.get('url'))}"
                        if job_id in seen_ids:
                            continue
                        seen_ids.add(job_id)
                        jobs.append({
                            "id": job_id,
                            "title": title,
                            "company": job.get("company_name", "Unknown"),
                            "url": job.get("url", ""),
                            "source": "Remotive",
                            "description": desc,
                        })
        except Exception as e:
            logger.error(f"Remotive error: {e}")
        logger.info(f"Remotive: {len(jobs)} matching jobs")
        return jobs


class RemoteOKScraper(BaseScraper):
    def fetch_jobs(self):
        jobs = []
        try:
            resp = self._get(
                "https://remoteok.com/api",
                headers={"User-Agent": "bengali-annotation-job-alert/1.0"}
            )
            data = resp.json()
            for item in data[1:]:  # first element is metadata
                title = item.get("position", "")
                desc_raw = item.get("description", "") or ""
                tags = " ".join(item.get("tags", []))
                desc = BeautifulSoup(desc_raw, "html.parser").get_text(separator=' ', strip=True)[:400] if desc_raw else ""
                if self.matches_keywords(title, f"{desc} {tags}"):
                    job_id = f"remoteok:{item.get('id', item.get('url', ''))}"
                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": item.get("company", "Unknown"),
                        "url": item.get("url", ""),
                        "source": "RemoteOK",
                        "description": desc,
                    })
        except Exception as e:
            logger.error(f"RemoteOK error: {e}")
        logger.info(f"RemoteOK: {len(jobs)} matching jobs")
        return jobs


class ArbeitnowScraper(BaseScraper):
    def fetch_jobs(self):
        jobs = []
        try:
            resp = self._get("https://www.arbeitnow.com/api/job-board-api")
            for item in resp.json().get("data", []):
                if not item.get("remote"):
                    continue
                title = item.get("title", "")
                desc_raw = item.get("description", "") or ""
                tags = " ".join(item.get("tags", []))
                desc = BeautifulSoup(desc_raw, "html.parser").get_text(separator=' ', strip=True)[:400] if desc_raw else ""
                if self.matches_keywords(title, f"{desc} {tags}"):
                    job_id = f"arbeitnow:{item.get('slug', '')}"
                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": item.get("company_name", "Unknown"),
                        "url": item.get("url", ""),
                        "source": "Arbeitnow",
                        "description": desc,
                    })
        except Exception as e:
            logger.error(f"Arbeitnow error: {e}")
        logger.info(f"Arbeitnow: {len(jobs)} matching jobs")
        return jobs


class GreenhouseScraper(BaseScraper):
    """Scrapes a Greenhouse job board for a given company."""
    def __init__(self, board_token, company_name):
        self.board_token = board_token
        self.company_name = company_name

    def fetch_jobs(self):
        jobs = []
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{self.board_token}/jobs"
            resp = self._get(url, params={"content": "true"})
            for job in resp.json().get("jobs", []):
                title = job.get("title", "")
                content_raw = job.get("content", "") or ""
                content = BeautifulSoup(content_raw, "html.parser").get_text(separator=' ', strip=True)[:400]
                location = job.get("location", {}).get("name", "")
                if self.matches_keywords(title, f"{content} {location}"):
                    job_id = f"greenhouse:{self.board_token}:{job.get('id')}"
                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": self.company_name,
                        "url": job.get("absolute_url", ""),
                        "source": f"Greenhouse/{self.company_name}",
                        "description": content,
                    })
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning(f"Greenhouse board not found: {self.board_token}")
            else:
                logger.error(f"Greenhouse error ({self.company_name}): {e}")
        except Exception as e:
            logger.error(f"Greenhouse error ({self.company_name}): {e}")
        logger.info(f"Greenhouse/{self.company_name}: {len(jobs)} matching jobs")
        return jobs


class LeverScraper(BaseScraper):
    """Scrapes a Lever job board for a given company."""
    def __init__(self, company_slug, company_name):
        self.company_slug = company_slug
        self.company_name = company_name

    def fetch_jobs(self):
        jobs = []
        try:
            url = f"https://api.lever.co/v0/postings/{self.company_slug}"
            resp = self._get(url, params={"mode": "json"})
            for posting in resp.json():
                title = posting.get("text", "")
                desc = posting.get("descriptionPlain", "") or ""
                if self.matches_keywords(title, desc):
                    job_id = f"lever:{self.company_slug}:{posting.get('id', '')}"
                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": self.company_name,
                        "url": posting.get("hostedUrl", ""),
                        "source": f"Lever/{self.company_name}",
                        "description": desc[:400],
                    })
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                logger.warning(f"Lever board not found: {self.company_slug}")
            else:
                logger.error(f"Lever error ({self.company_name}): {e}")
        except Exception as e:
            logger.error(f"Lever error ({self.company_name}): {e}")
        logger.info(f"Lever/{self.company_name}: {len(jobs)} matching jobs")
        return jobs


class LinkedInScraper(BaseScraper):
    SEARCH_QUERIES = [
        "bengali data annotation",
        "bengali language specialist",
        "bengali linguist",
        "bengali ai training",
        "bangla annotation",
    ]

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }

    def fetch_jobs(self):
        jobs = []
        seen_ids = set()
        for keywords in self.SEARCH_QUERIES:
            encoded_kw = quote_plus(keywords)
            url = f"https://www.linkedin.com/jobs/search?keywords={encoded_kw}&location=Remote&f_TPR=r604800"
            try:
                time.sleep(random.uniform(2, 4))  # delay before request
                response = requests.get(url, headers=self.headers, timeout=15)
                if response.status_code != 200:
                    logger.warning(f"LinkedIn returned {response.status_code} for '{keywords}' — likely blocked")
                    continue
                soup = BeautifulSoup(response.text, 'html.parser')
                cards = soup.find_all('div', class_='base-card')
                if not cards:
                    logger.warning(f"LinkedIn: 0 cards on 200 for '{keywords}' — may be login-walled")
                    continue
                for card in cards:
                    title_elem = card.find('h3', class_='base-search-card__title')
                    company_elem = card.find('h4', class_='base-search-card__subtitle')
                    link_elem = card.find('a', class_='base-card__full-link')
                    if not title_elem:
                        continue
                    title = title_elem.text.strip()
                    company = company_elem.text.strip() if company_elem else "Unknown"
                    job_url = link_elem['href'].split('?')[0] if link_elem else ""
                    numeric_slug = job_url.split('-')[-1] if '-' in job_url else job_url
                    job_id = f"linkedin:{numeric_slug}"
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    if self.matches_keywords(title):
                        jobs.append({
                            "id": job_id,
                            "title": title,
                            "company": company,
                            "url": job_url,
                            "source": "LinkedIn",
                            "description": "View LinkedIn for full description.",
                        })
            except Exception as e:
                logger.error(f"LinkedIn error for '{keywords}': {e}")
        logger.info(f"LinkedIn: {len(jobs)} matching jobs")
        return jobs


_SERPAPI_QUERIES = [
    "bengali annotation jobs",
    "bangla linguist AI training",
    "bengali NLP data labeling",
    "indic language annotation remote",
]


class SerpApiScraper(BaseScraper):
    """Searches Google Jobs via SerpAPI — covers all sources including companies with no ATS API."""

    def __init__(self):
        self.api_key = os.environ.get("SERPAPI_KEY")

    def fetch_jobs(self):
        if not self.api_key:
            logger.warning("SerpAPI: SERPAPI_KEY not set, skipping.")
            return []

        jobs = []
        seen_ids = set()

        for query in _SERPAPI_QUERIES:
            try:
                resp = self._get(
                    "https://serpapi.com/search.json",
                    params={
                        "engine": "google_jobs",
                        "q": query,
                        "hl": "en",
                        "gl": "us",
                        "chips": "date_posted:week",
                        "api_key": self.api_key,
                    },
                )
                for item in resp.json().get("jobs_results", []):
                    title = item.get("title", "")
                    desc = item.get("description", "") or ""
                    if not self.matches_keywords(title, desc):
                        continue

                    job_id = f"serpapi:{item.get('job_id', '')}"
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)

                    # Best available apply URL from related_links
                    related = item.get("related_links", [])
                    url = related[0].get("link", "") if related else ""

                    jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": item.get("company_name", "Unknown"),
                        "url": url,
                        "source": f"Google Jobs ({item.get('via', 'web')})",
                        "description": desc[:400],
                    })
            except Exception as e:
                logger.error(f"SerpAPI error for query '{query}': {e}")

        logger.info(f"SerpAPI: {len(jobs)} matching jobs")
        return jobs


def get_all_scrapers():
    return [
        # RSS
        RSSScraper("https://weworkremotely.com/categories/all-other-remote-jobs.rss", "WeWorkRemotely"),

        # General remote job APIs
        RemotiveScraper(),
        RemoteOKScraper(),
        ArbeitnowScraper(),

        # Google Jobs aggregator — covers Outlier, Alignerr, Sigma AI, YPAI and all others
        SerpApiScraper(),

        # Vendor Greenhouse boards — verified working slugs
        GreenhouseScraper("remotasks", "Remotasks (Telus Digital AI)"),
        GreenhouseScraper("scaleai", "Scale AI"),

        # Vendor Lever boards — verified working slugs
        LeverScraper("rws", "RWS TrainAI"),
        LeverScraper("appen", "Appen"),
        LeverScraper("innodata", "Innodata"),

        # LinkedIn (best-effort; may be blocked on CI runners)
        LinkedInScraper(),
    ]

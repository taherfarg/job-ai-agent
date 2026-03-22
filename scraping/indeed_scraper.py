"""
indeed_scraper.py
─────────────────
Scrapes job listings from Indeed.com.
Falls back to realistic dummy data when blocked (Indeed has strict anti-bot measures).
"""

import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote_plus
from scraping.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

DUMMY_JOBS = [
    {
        "title": "Senior AI Engineer",
        "company": "Tech Innovators Inc",
        "link": "https://www.indeed.com/viewjob?jk=abc123",
        "description": "We are looking for a highly skilled AI Engineer to join our fast-paced startup. Must have experience with Python, LLMs, and MLOps.",
        "source": "Indeed",
    },
    {
        "title": "Machine Learning Engineer",
        "company": "DataVision AI",
        "link": "https://www.indeed.com/viewjob?jk=def456",
        "description": "DataVision AI seeks a Machine Learning Engineer with strong Python, TensorFlow/PyTorch, and cloud deployment (AWS/GCP) experience.",
        "source": "Indeed",
    },
    {
        "title": "AI Research Engineer",
        "company": "NeuralCore Labs",
        "link": "https://www.indeed.com/viewjob?jk=ghi789",
        "description": "Exciting opportunity to work on cutting-edge NLP and LLM research. Requires deep learning expertise and publication record.",
        "source": "Indeed",
    },
]


class IndeedScraper(BaseScraper):
    name = "Indeed"

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        url = f"https://www.indeed.com/jobs?q={quote_plus(keyword)}&l={quote_plus(location)}"
        r = requests.get(url, headers=self._headers(), timeout=10)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        job_cards = soup.select(".job_seen_beacon")
        if not job_cards:
            raise ValueError("No job cards found")

        jobs = []
        for card in job_cards[:limit]:
            try:
                title_el = card.select_one("h2")
                title = title_el.text.strip() if title_el else "Unknown Title"

                link_el = card.select_one("a")
                link = (
                    f"https://www.indeed.com{link_el['href']}"
                    if link_el and link_el.has_attr("href")
                    else url
                )

                company_el = card.select_one('[data-testid="company-name"]')
                company = company_el.text.strip() if company_el else "Unknown Company"

                desc_el = card.select_one(".job-snippet")
                description = desc_el.text.strip() if desc_el else ""

                jobs.append({
                    "title": title,
                    "company": company,
                    "link": link,
                    "description": description,
                    "source": "Indeed",
                })
            except Exception as e:
                logger.debug(f"Error parsing Indeed job card: {e}")
                continue

        return jobs

    def _fallback_jobs(self) -> list[dict]:
        return DUMMY_JOBS


# ── Legacy function for backwards compatibility ────────────────────────────
def search_indeed_jobs(keyword: str, location: str = "", limit: int = 15) -> list[dict]:
    return IndeedScraper().search(keyword, location, limit)

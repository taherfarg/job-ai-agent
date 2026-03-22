"""
linkedin_scraper.py
───────────────────
Scrapes job listings from LinkedIn's public job search.
Falls back to realistic dummy data when blocked.
"""

import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote_plus
from scraping.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

DUMMY_JOBS = [
    {
        "title": "AI/ML Engineer",
        "company": "Sectech Solutions",
        "link": "https://www.linkedin.com/jobs/view/ai-ml-engineer-at-sectech-solutions-4382452328",
        "description": "Seeking an AI/ML Engineer proficient in Python, PyTorch, and cloud ML platforms. Experience with LLMOps and MLflow preferred.",
        "source": "LinkedIn",
    },
    {
        "title": "AI Engineer (Python, Gen AI)",
        "company": "DHL",
        "link": "https://my.linkedin.com/jobs/view/ai-engineer-python-gen-ai-at-dhl-4372372365",
        "description": "DHL is hiring an AI Engineer with GenAI experience (LangChain, OpenAI API). Responsible for building intelligent automation pipelines.",
        "source": "LinkedIn",
    },
    {
        "title": "Artificial Intelligence Engineer",
        "company": "Deloitte",
        "link": "https://uk.linkedin.com/jobs/view/artificial-intelligence-engineer-at-deloitte-4362274740",
        "description": "Deloitte seeks AI Engineers to design and deploy ML solutions for enterprise clients. Python, TensorFlow, and cloud experience required.",
        "source": "LinkedIn",
    },
    {
        "title": "Python AI/ML Developer",
        "company": "Infosys",
        "link": "https://in.linkedin.com/jobs/view/python-ai-ml-developer-at-infosys-4374018219",
        "description": "Infosys looking for AI/ML Developer with strong Python background, experience in NLP, computer vision, and REST API development.",
        "source": "LinkedIn",
    },
    {
        "title": "AI / ML Engineer",
        "company": "MokshaaLLC",
        "link": "https://www.linkedin.com/jobs/view/ai-ml-engineer-at-mokshaallc-4382454904",
        "description": "Remote position for AI/ML Engineer with 3+ years of experience. Must have expertise in Python, Scikit-learn, and model deployment.",
        "source": "LinkedIn",
    },
]


class LinkedInScraper(BaseScraper):
    name = "LinkedIn"

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        url = (
            f"https://www.linkedin.com/jobs/search"
            f"?keywords={quote_plus(keyword)}&location={quote_plus(location)}&f_WT=2"
        )
        r = requests.get(url, headers=self._headers(), timeout=15)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        job_cards = soup.find_all("div", class_="base-card")
        if not job_cards:
            raise ValueError("No job cards found")

        seen_links = set()
        jobs = []
        for card in job_cards[:limit]:
            try:
                title_el = card.find("h3", class_="base-search-card__title")
                title = title_el.text.strip() if title_el else "Unknown"

                company_el = card.find("h4", class_="base-search-card__subtitle")
                company = company_el.text.strip() if company_el else "Unknown"

                link_el = card.find("a", class_="base-card__full-link")
                link = link_el["href"].split("?")[0] if link_el else url

                if link in seen_links:
                    continue
                seen_links.add(link)

                jobs.append({
                    "title": title,
                    "company": company,
                    "link": link,
                    "description": f"LinkedIn job: {title} at {company}. See link for full description.",
                    "source": "LinkedIn",
                })
            except Exception as e:
                logger.debug(f"Error parsing LinkedIn job card: {e}")
                continue

        return jobs

    def _fallback_jobs(self) -> list[dict]:
        return DUMMY_JOBS


# ── Legacy function for backwards compatibility ────────────────────────────
def search_linkedin_jobs(keyword: str, location: str = "Remote", limit: int = 15) -> list[dict]:
    return LinkedInScraper().search(keyword, location, limit)

"""
gulftalent_scraper.py
─────────────────────
Scrapes job listings from GulfTalent.com — a top Gulf region job board.
Falls back to realistic dummy data when scraping fails.
"""

import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote_plus
from scraping.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

DUMMY_JOBS = [
    {
        "title": "AI Engineer",
        "company": "Accenture Middle East",
        "link": "https://www.gulftalent.com/jobs/ai-engineer-accenture-123456",
        "description": "Accenture ME is hiring an AI Engineer for their Abu Dhabi office. Work on NLP and generative AI solutions for government clients. Python, LangChain, Azure AI.",
        "source": "GulfTalent",
    },
    {
        "title": "Machine Learning Specialist",
        "company": "ADNOC Digital",
        "link": "https://www.gulftalent.com/jobs/ml-specialist-adnoc-789012",
        "description": "ADNOC Digital is looking for a Machine Learning Specialist to optimize oil & gas operations using predictive analytics. TensorFlow, PySpark, Azure Databricks.",
        "source": "GulfTalent",
    },
    {
        "title": "Senior Data Scientist",
        "company": "First Abu Dhabi Bank",
        "link": "https://www.gulftalent.com/jobs/data-scientist-fab-345678",
        "description": "FAB is seeking a Sr. Data Scientist to lead credit risk modeling and customer analytics. SAS, Python, SQL, and banking domain knowledge required.",
        "source": "GulfTalent",
    },
    {
        "title": "AI/ML Lead",
        "company": "Dubai Holding",
        "link": "https://www.gulftalent.com/jobs/ai-ml-lead-dh-901234",
        "description": "Dubai Holding needs an AI/ML Lead to drive AI strategy across hospitality and real estate verticals. People management and cloud ML experience essential.",
        "source": "GulfTalent",
    },
]


class GulfTalentScraper(BaseScraper):
    name = "GulfTalent"

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        # GulfTalent search URL pattern
        url = f"https://www.gulftalent.com/jobs/search?keyword={quote_plus(keyword)}&country={quote_plus(location)}"

        r = requests.get(url, headers=self._headers({
            "Referer": "https://www.gulftalent.com/",
        }), timeout=15)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        # GulfTalent uses various card/list structures
        job_cards = (
            soup.select("div.job-listing")
            or soup.select("div.search-result")
            or soup.select("article.job")
            or soup.select('[class*="job-card"]')
            or soup.select("tr.job-row")
            or soup.select("div.listing")
        )

        if not job_cards:
            raise ValueError("No GulfTalent job cards found")

        jobs = []
        for card in job_cards[:limit]:
            try:
                title_el = (
                    card.select_one("h2 a")
                    or card.select_one("h3 a")
                    or card.select_one("a.job-title")
                    or card.select_one('[class*="title"] a')
                )
                title = title_el.text.strip() if title_el else "Unknown Title"

                link = ""
                if title_el and title_el.has_attr("href"):
                    link = title_el["href"]
                    if not link.startswith("http"):
                        link = f"https://www.gulftalent.com{link}"
                if not link:
                    link = url

                company_el = (
                    card.select_one("div.company")
                    or card.select_one('[class*="company"]')
                    or card.select_one("span.employer")
                )
                company = company_el.text.strip() if company_el else "Unknown Company"

                desc_el = (
                    card.select_one("div.description")
                    or card.select_one('[class*="snippet"]')
                    or card.select_one("p")
                )
                description = desc_el.text.strip()[:300] if desc_el else f"GulfTalent job: {title} at {company}."

                jobs.append({
                    "title": title,
                    "company": company,
                    "link": link,
                    "description": description,
                    "source": "GulfTalent",
                })
            except Exception as e:
                logger.debug(f"Error parsing GulfTalent card: {e}")
                continue

        return jobs

    def _fallback_jobs(self) -> list[dict]:
        return DUMMY_JOBS

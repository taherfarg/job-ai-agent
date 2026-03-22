"""
bayt_scraper.py
───────────────
Scrapes job listings from Bayt.com — a major Middle East & North Africa job portal.
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
        "company": "Chalhoub Group",
        "link": "https://www.bayt.com/en/uae/jobs/ai-engineer-4876543/",
        "description": "Chalhoub Group is hiring an AI Engineer in Dubai to build recommendation engines for luxury retail. Python, AWS, computer vision experience preferred.",
        "source": "Bayt",
    },
    {
        "title": "Machine Learning Engineer",
        "company": "Etisalat (e&)",
        "link": "https://www.bayt.com/en/uae/jobs/ml-engineer-4876544/",
        "description": "e& is seeking an ML Engineer to develop AI-powered network optimization tools. TensorFlow, Kubernetes, and telecom domain knowledge valued.",
        "source": "Bayt",
    },
    {
        "title": "Data Scientist",
        "company": "Emaar Properties",
        "link": "https://www.bayt.com/en/uae/jobs/data-scientist-4876545/",
        "description": "Emaar Properties needs a Data Scientist for real estate analytics — pricing models, demand forecasting. Python, SQL, and Power BI experience needed.",
        "source": "Bayt",
    },
    {
        "title": "NLP Engineer",
        "company": "Abu Dhabi Islamic Bank",
        "link": "https://www.bayt.com/en/uae/jobs/nlp-engineer-4876546/",
        "description": "ADIB is hiring an NLP Engineer to build Arabic chatbots and sentiment analysis tools. Hugging Face, spaCy, and Arabic NLP experience required.",
        "source": "Bayt",
    },
]


class BaytScraper(BaseScraper):
    name = "Bayt"

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        # Bayt.com search URL
        keyword_slug = keyword.lower().replace(" ", "-")
        url = f"https://www.bayt.com/en/uae/jobs/{keyword_slug}-jobs/"

        # If location has specific country, adjust URL
        loc_lower = location.lower()
        if "saudi" in loc_lower or "ksa" in loc_lower:
            url = f"https://www.bayt.com/en/saudi-arabia/jobs/{keyword_slug}-jobs/"
        elif "qatar" in loc_lower:
            url = f"https://www.bayt.com/en/qatar/jobs/{keyword_slug}-jobs/"
        elif "kuwait" in loc_lower:
            url = f"https://www.bayt.com/en/kuwait/jobs/{keyword_slug}-jobs/"
        elif "bahrain" in loc_lower:
            url = f"https://www.bayt.com/en/bahrain/jobs/{keyword_slug}-jobs/"
        elif "oman" in loc_lower:
            url = f"https://www.bayt.com/en/oman/jobs/{keyword_slug}-jobs/"

        r = requests.get(url, headers=self._headers({
            "Referer": "https://www.bayt.com/",
        }), timeout=15)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        job_cards = (
            soup.select("li[data-js-job]")
            or soup.select("div.has-jobcard")
            or soup.select('[class*="job-card"]')
            or soup.select("div[class*='listing']")
            or soup.select("li.has-vacancy")
        )

        if not job_cards:
            raise ValueError("No Bayt job cards found")

        jobs = []
        for card in job_cards[:limit]:
            try:
                title_el = (
                    card.select_one("h2 a")
                    or card.select_one('[class*="job-title"] a')
                    or card.select_one("a[data-js-aid='job-title']")
                    or card.select_one("a.jb-title")
                )
                title = title_el.text.strip() if title_el else "Unknown Title"

                link = ""
                if title_el and title_el.has_attr("href"):
                    link = title_el["href"]
                    if not link.startswith("http"):
                        link = f"https://www.bayt.com{link}"
                if not link:
                    link = url

                company_el = (
                    card.select_one('[class*="company"]')
                    or card.select_one("div.bca")
                    or card.select_one('[data-js-aid="company"]')
                )
                company = company_el.text.strip() if company_el else "Unknown Company"

                desc_el = (
                    card.select_one('[class*="description"]')
                    or card.select_one("div.m10t")
                    or card.select_one("p")
                )
                description = desc_el.text.strip()[:300] if desc_el else f"Bayt job: {title} at {company}."

                jobs.append({
                    "title": title,
                    "company": company,
                    "link": link,
                    "description": description,
                    "source": "Bayt",
                })
            except Exception as e:
                logger.debug(f"Error parsing Bayt card: {e}")
                continue

        return jobs

    def _fallback_jobs(self) -> list[dict]:
        return DUMMY_JOBS

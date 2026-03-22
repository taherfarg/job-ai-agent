"""
glassdoor_scraper.py
────────────────────
Scrapes job listings from Glassdoor.
Falls back to realistic dummy data when blocked (Glassdoor has heavy bot protection).
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
        "company": "Careem",
        "link": "https://www.glassdoor.com/job-listing/ai-engineer-careem-JV_IC2204100_KO0,11_KE12,18.htm",
        "description": "Careem is looking for an AI Engineer to work on recommendation systems and personalization. Python, PyTorch, and cloud experience required.",
        "source": "Glassdoor",
    },
    {
        "title": "Senior Machine Learning Engineer",
        "company": "Noon",
        "link": "https://www.glassdoor.com/job-listing/sr-ml-engineer-noon-JV_IC2204100_KO0,18_KE19,23.htm",
        "description": "Noon seeks a Senior ML Engineer to build scalable models for e-commerce. Experience with NLP, search ranking, and AWS SageMaker is a plus.",
        "source": "Glassdoor",
    },
    {
        "title": "Data Scientist – AI/ML",
        "company": "Emirates NBD",
        "link": "https://www.glassdoor.com/job-listing/data-scientist-emirates-nbd-JV_IC2204100_KO0,14_KE15,27.htm",
        "description": "Join Emirates NBD's Analytics team as a Data Scientist. Work on fraud detection, customer segmentation. Python, SQL, and ML frameworks required.",
        "source": "Glassdoor",
    },
    {
        "title": "Deep Learning Engineer",
        "company": "G42",
        "link": "https://www.glassdoor.com/job-listing/deep-learning-engineer-g42-JV_IC2204100_KO0,22_KE23,26.htm",
        "description": "G42 is hiring a Deep Learning Engineer to work on large-scale LLMs and computer vision systems. GPU optimization and distributed training experience needed.",
        "source": "Glassdoor",
    },
]


class GlassdoorScraper(BaseScraper):
    name = "Glassdoor"

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        url = (
            f"https://www.glassdoor.com/Job/jobs.htm"
            f"?sc.keyword={quote_plus(keyword)}&locT=C&locKeyword={quote_plus(location)}"
        )
        r = requests.get(url, headers=self._headers({
            "Referer": "https://www.glassdoor.com/",
        }), timeout=15)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        # Glassdoor uses various card selectors — try multiple
        job_cards = (
            soup.select('[data-test="jobListing"]')
            or soup.select(".react-job-listing")
            or soup.select("li.jl")
            or soup.select('[class*="JobCard"]')
        )

        if not job_cards:
            raise ValueError("No Glassdoor job cards found")

        jobs = []
        for card in job_cards[:limit]:
            try:
                # Title
                title_el = (
                    card.select_one('[data-test="job-title"]')
                    or card.select_one("a.jobTitle")
                    or card.select_one("a[class*='jobTitle']")
                )
                title = title_el.text.strip() if title_el else "Unknown Title"

                # Link
                link_el = card.select_one("a[href*='/job-listing/']") or title_el
                link = link_el.get("href", "") if link_el else ""
                if link and not link.startswith("http"):
                    link = f"https://www.glassdoor.com{link}"
                if not link:
                    link = url

                # Company
                company_el = (
                    card.select_one('[data-test="employer-short-name"]')
                    or card.select_one("div.employer-name")
                    or card.select_one('[class*="employer"]')
                )
                company = company_el.text.strip() if company_el else "Unknown Company"

                # Description snippet
                desc_el = card.select_one('[class*="description"]') or card.select_one(".description")
                description = desc_el.text.strip()[:300] if desc_el else f"Glassdoor job: {title} at {company}."

                jobs.append({
                    "title": title,
                    "company": company,
                    "link": link,
                    "description": description,
                    "source": "Glassdoor",
                })
            except Exception as e:
                logger.debug(f"Error parsing Glassdoor card: {e}")
                continue

        return jobs

    def _fallback_jobs(self) -> list[dict]:
        return DUMMY_JOBS

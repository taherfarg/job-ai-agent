"""
naukrigulf_scraper.py
─────────────────────
Scrapes job listings from NaukriGulf.com — popular Gulf region job portal.
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
        "title": "AI/ML Engineer",
        "company": "Presight AI",
        "link": "https://www.naukrigulf.com/ai-ml-engineer-jobs-in-abu-dhabi-123456",
        "description": "Presight AI is looking for an AI/ML Engineer to work on large-scale data analytics and AI solutions for the government sector. Python, Spark, Deep Learning.",
        "source": "NaukriGulf",
    },
    {
        "title": "Computer Vision Engineer",
        "company": "Technology Innovation Institute",
        "link": "https://www.naukrigulf.com/cv-engineer-jobs-in-abu-dhabi-789012",
        "description": "TII seeks a Computer Vision Engineer to work on autonomous systems. OpenCV, PyTorch, CUDA, and real-time inference experience required.",
        "source": "NaukriGulf",
    },
    {
        "title": "AI Solutions Architect",
        "company": "Injazat",
        "link": "https://www.naukrigulf.com/ai-architect-jobs-in-uae-345678",
        "description": "Injazat is hiring an AI Solutions Architect for end-to-end ML platform design. Azure ML, MLOps, CI/CD for models. Enterprise solution design experience needed.",
        "source": "NaukriGulf",
    },
    {
        "title": "Python Developer – AI Platform",
        "company": "Mashreq Bank",
        "link": "https://www.naukrigulf.com/python-ai-developer-jobs-in-dubai-901234",
        "description": "Mashreq Bank seeks a Python Developer to build their AI platform. FastAPI, Docker, Kubernetes, and AI model serving (TensorRT, Triton) skills preferred.",
        "source": "NaukriGulf",
    },
]


class NaukrigulfScraper(BaseScraper):
    name = "NaukriGulf"

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        url = (
            f"https://www.naukrigulf.com/search"
            f"?keyword={quote_plus(keyword)}&location={quote_plus(location)}"
        )

        r = requests.get(url, headers=self._headers({
            "Referer": "https://www.naukrigulf.com/",
        }), timeout=15)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        job_cards = (
            soup.select("div.srp-listing")
            or soup.select('[class*="job-card"]')
            or soup.select("article.jobTuple")
            or soup.select("div.list-item")
            or soup.select('[class*="listing"]')
        )

        if not job_cards:
            raise ValueError("No NaukriGulf job cards found")

        jobs = []
        for card in job_cards[:limit]:
            try:
                title_el = (
                    card.select_one("a.desig")
                    or card.select_one("a[class*='title']")
                    or card.select_one("h2 a")
                    or card.select_one("a.job-title")
                )
                title = title_el.text.strip() if title_el else "Unknown Title"

                link = ""
                if title_el and title_el.has_attr("href"):
                    link = title_el["href"]
                    if not link.startswith("http"):
                        link = f"https://www.naukrigulf.com{link}"
                if not link:
                    link = url

                company_el = (
                    card.select_one("a.comp-name")
                    or card.select_one('[class*="company"]')
                    or card.select_one("div.company-name")
                )
                company = company_el.text.strip() if company_el else "Unknown Company"

                desc_el = (
                    card.select_one("div.desc")
                    or card.select_one('[class*="description"]')
                    or card.select_one("span.exp-desc")
                )
                description = desc_el.text.strip()[:300] if desc_el else f"NaukriGulf job: {title} at {company}."

                jobs.append({
                    "title": title,
                    "company": company,
                    "link": link,
                    "description": description,
                    "source": "NaukriGulf",
                })
            except Exception as e:
                logger.debug(f"Error parsing NaukriGulf card: {e}")
                continue

        return jobs

    def _fallback_jobs(self) -> list[dict]:
        return DUMMY_JOBS

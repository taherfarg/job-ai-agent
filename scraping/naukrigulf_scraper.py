"""
naukrigulf_scraper.py
─────────────────────
Scrapes job listings from NaukriGulf.com — popular Gulf region job portal.
Uses Playwright fallback when standard requests are blocked.
"""

import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote_plus
from scraping.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class NaukrigulfScraper(BaseScraper):
    name = "NaukriGulf"

    def _build_search_url(self, keyword: str, location: str) -> str:
        return (
            f"https://www.naukrigulf.com/search"
            f"?keyword={quote_plus(keyword)}&location={quote_plus(location)}"
        )

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        url = self._build_search_url(keyword, location)
        r = requests.get(url, headers=self._headers({
            "Referer": "https://www.naukrigulf.com/",
        }), timeout=15)
        r.raise_for_status()
        return self._parse_html(r.text, url, limit)

    def _parse_playwright_html(self, html: str, url: str, limit: int) -> list[dict]:
        return self._parse_html(html, url, limit)

    def _parse_html(self, html: str, url: str, limit: int) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")

        job_cards = (
            soup.select("div.srp-listing")
            or soup.select('[class*="job-card"]')
            or soup.select("article.jobTuple")
            or soup.select("div.list-item")
            or soup.select('[class*="listing"]')
            or soup.select('[class*="jobCard"]')
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
                    or card.select_one("a")
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

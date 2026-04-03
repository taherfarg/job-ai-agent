"""
bayt_scraper.py
───────────────
Scrapes job listings from Bayt.com — a major Middle East & North Africa job portal.
Uses Playwright fallback when standard requests are blocked.
"""

import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote_plus
from scraping.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class BaytScraper(BaseScraper):
    name = "Bayt"

    def _build_search_url(self, keyword: str, location: str) -> str:
        keyword_slug = keyword.lower().replace(" ", "-")
        loc_lower = location.lower()

        if "saudi" in loc_lower or "ksa" in loc_lower:
            return f"https://www.bayt.com/en/saudi-arabia/jobs/{keyword_slug}-jobs/"
        elif "qatar" in loc_lower:
            return f"https://www.bayt.com/en/qatar/jobs/{keyword_slug}-jobs/"
        elif "kuwait" in loc_lower:
            return f"https://www.bayt.com/en/kuwait/jobs/{keyword_slug}-jobs/"
        elif "bahrain" in loc_lower:
            return f"https://www.bayt.com/en/bahrain/jobs/{keyword_slug}-jobs/"
        elif "oman" in loc_lower:
            return f"https://www.bayt.com/en/oman/jobs/{keyword_slug}-jobs/"
        else:
            return f"https://www.bayt.com/en/uae/jobs/{keyword_slug}-jobs/"

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        url = self._build_search_url(keyword, location)
        r = requests.get(url, headers=self._headers({
            "Referer": "https://www.bayt.com/",
        }), timeout=15)
        r.raise_for_status()
        return self._parse_html(r.text, url, limit)

    def _parse_playwright_html(self, html: str, url: str, limit: int) -> list[dict]:
        return self._parse_html(html, url, limit)

    def _parse_html(self, html: str, url: str, limit: int) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")

        job_cards = (
            soup.select("li[data-js-job]")
            or soup.select("div.has-jobcard")
            or soup.select('[class*="job-card"]')
            or soup.select("div[class*='listing']")
            or soup.select("li.has-vacancy")
            or soup.select('[class*="jobCard"]')
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
                    or card.select_one("a")
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

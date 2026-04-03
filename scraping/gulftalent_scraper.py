"""
gulftalent_scraper.py
─────────────────────
Scrapes job listings from GulfTalent.com — a top Gulf region job board.
Uses Playwright fallback when standard requests are blocked.
"""

import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote_plus
from scraping.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class GulfTalentScraper(BaseScraper):
    name = "GulfTalent"

    def _build_search_url(self, keyword: str, location: str) -> str:
        return f"https://www.gulftalent.com/jobs/search?keyword={quote_plus(keyword)}&country={quote_plus(location)}"

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        url = self._build_search_url(keyword, location)
        r = requests.get(url, headers=self._headers({
            "Referer": "https://www.gulftalent.com/",
        }), timeout=15)
        r.raise_for_status()
        return self._parse_html(r.text, url, limit)

    def _parse_playwright_html(self, html: str, url: str, limit: int) -> list[dict]:
        return self._parse_html(html, url, limit)

    def _parse_html(self, html: str, url: str, limit: int) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")

        job_cards = (
            soup.select("div.job-listing")
            or soup.select("div.search-result")
            or soup.select("article.job")
            or soup.select('[class*="job-card"]')
            or soup.select("tr.job-row")
            or soup.select("div.listing")
            or soup.select('[class*="vacancy"]')
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
                    or card.select_one("a")
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

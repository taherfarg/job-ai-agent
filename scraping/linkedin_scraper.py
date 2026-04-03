"""
linkedin_scraper.py
───────────────────
Scrapes job listings from LinkedIn's public job search.
Uses Playwright fallback when standard requests are blocked.
"""

import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote_plus
from scraping.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    name = "LinkedIn"

    def _build_search_url(self, keyword: str, location: str) -> str:
        return (
            f"https://www.linkedin.com/jobs/search"
            f"?keywords={quote_plus(keyword)}&location={quote_plus(location)}&f_WT=2&f_AL=true"
        )

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        url = self._build_search_url(keyword, location)
        r = requests.get(url, headers=self._headers(), timeout=15)
        r.raise_for_status()
        return self._parse_html(r.text, url, limit)

    def _parse_playwright_html(self, html: str, url: str, limit: int) -> list[dict]:
        return self._parse_html(html, url, limit)

    def _parse_html(self, html: str, url: str, limit: int) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        job_cards = soup.find_all("div", class_="base-card")
        if not job_cards:
            raise ValueError("No LinkedIn job cards found")

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


# ── Legacy function for backwards compatibility ────────────────────────────
def search_linkedin_jobs(keyword: str, location: str = "Remote", limit: int = 15) -> list[dict]:
    return LinkedInScraper().search(keyword, location, limit)

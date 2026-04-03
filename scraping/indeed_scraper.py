"""
indeed_scraper.py
─────────────────
Scrapes job listings from Indeed.com.
Uses Playwright fallback when standard requests are blocked.
"""

import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote_plus
from scraping.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class IndeedScraper(BaseScraper):
    name = "Indeed"

    def _build_search_url(self, keyword: str, location: str) -> str:
        return f"https://www.indeed.com/jobs?q={quote_plus(keyword)}&l={quote_plus(location)}"

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        url = self._build_search_url(keyword, location)
        r = requests.get(url, headers=self._headers(), timeout=10)
        r.raise_for_status()
        return self._parse_html(r.text, url, limit)

    def _parse_playwright_html(self, html: str, url: str, limit: int) -> list[dict]:
        return self._parse_html(html, url, limit)

    def _parse_html(self, html: str, url: str, limit: int) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        job_cards = soup.select(".job_seen_beacon") or soup.select(".jobsearch-ResultsList > li")
        if not job_cards:
            raise ValueError("No Indeed job cards found")

        jobs = []
        for card in job_cards[:limit]:
            try:
                title_el = card.select_one("h2") or card.select_one('[class*="jobTitle"]')
                title = title_el.text.strip() if title_el else "Unknown Title"

                link_el = card.select_one("a[href*='/viewjob']") or card.select_one("a[href*='/rc/clk']") or card.select_one("a")
                link = (
                    f"https://www.indeed.com{link_el['href']}"
                    if link_el and link_el.has_attr("href") and not link_el["href"].startswith("http")
                    else (link_el["href"] if link_el and link_el.has_attr("href") else url)
                )

                company_el = card.select_one('[data-testid="company-name"]') or card.select_one('[class*="company"]')
                company = company_el.text.strip() if company_el else "Unknown Company"

                desc_el = card.select_one(".job-snippet") or card.select_one('[class*="snippet"]')
                description = desc_el.text.strip() if desc_el else f"Indeed job: {title} at {company}."

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


# ── Legacy function for backwards compatibility ────────────────────────────
def search_indeed_jobs(keyword: str, location: str = "", limit: int = 15) -> list[dict]:
    return IndeedScraper().search(keyword, location, limit)

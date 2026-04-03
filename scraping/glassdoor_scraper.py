"""
glassdoor_scraper.py
────────────────────
Scrapes job listings from Glassdoor.
Uses Playwright fallback when standard requests are blocked.
"""

import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import quote_plus
from scraping.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class GlassdoorScraper(BaseScraper):
    name = "Glassdoor"

    def _build_search_url(self, keyword: str, location: str) -> str:
        return (
            f"https://www.glassdoor.com/Job/jobs.htm"
            f"?sc.keyword={quote_plus(keyword)}&locT=C&locKeyword={quote_plus(location)}"
        )

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        url = self._build_search_url(keyword, location)
        r = requests.get(url, headers=self._headers({
            "Referer": "https://www.glassdoor.com/",
        }), timeout=15)
        r.raise_for_status()
        return self._parse_html(r.text, url, limit)

    def _parse_playwright_html(self, html: str, url: str, limit: int) -> list[dict]:
        return self._parse_html(html, url, limit)

    def _parse_html(self, html: str, url: str, limit: int) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")

        job_cards = (
            soup.select('[data-test="jobListing"]')
            or soup.select(".react-job-listing")
            or soup.select("li.jl")
            or soup.select('[class*="JobCard"]')
            or soup.select('[class*="jobCard"]')
        )

        if not job_cards:
            raise ValueError("No Glassdoor job cards found")

        jobs = []
        for card in job_cards[:limit]:
            try:
                title_el = (
                    card.select_one('[data-test="job-title"]')
                    or card.select_one("a.jobTitle")
                    or card.select_one("a[class*='jobTitle']")
                    or card.select_one("a[class*='JobCard_jobTitle']")
                )
                title = title_el.text.strip() if title_el else "Unknown Title"

                link_el = card.select_one("a[href*='/job-listing/']") or card.select_one("a[href*='partner/jobListing']") or title_el
                link = link_el.get("href", "") if link_el else ""
                if link and not link.startswith("http"):
                    link = f"https://www.glassdoor.com{link}"
                if not link:
                    link = url

                company_el = (
                    card.select_one('[data-test="employer-short-name"]')
                    or card.select_one("div.employer-name")
                    or card.select_one('[class*="employer"]')
                    or card.select_one('[class*="EmployerProfile"]')
                )
                company = company_el.text.strip() if company_el else "Unknown Company"

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

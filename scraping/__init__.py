"""
scraping/__init__.py
────────────────────
Scraper registry — provides a single entry-point to scrape all supported platforms.
"""

import logging
from config import SCRAPE_LIMIT

logger = logging.getLogger(__name__)

# ── Registry — import and list all scrapers here ────────────────────────────
from scraping.indeed_scraper import IndeedScraper
from scraping.linkedin_scraper import LinkedInScraper
from scraping.hn_scraper import HNScraper
from scraping.glassdoor_scraper import GlassdoorScraper
from scraping.gulftalent_scraper import GulfTalentScraper
from scraping.bayt_scraper import BaytScraper
from scraping.naukrigulf_scraper import NaukrigulfScraper

ALL_SCRAPERS = [
    IndeedScraper,
    LinkedInScraper,
    HNScraper,
    GlassdoorScraper,
    GulfTalentScraper,
    BaytScraper,
    NaukrigulfScraper,
]


def get_all_scrapers(enabled: list[str] | None = None):
    """
    Return instances of all scrapers, optionally filtered by name.

    Args:
        enabled: List of scraper names to enable (e.g. ["Indeed", "LinkedIn"]).
                 If None, all scrapers are enabled.
    """
    scrapers = [cls() for cls in ALL_SCRAPERS]
    if enabled:
        enabled_lower = [e.lower() for e in enabled]
        scrapers = [s for s in scrapers if s.name.lower() in enabled_lower]
    return scrapers


def scrape_all(
    keyword: str,
    location: str = "",
    limit: int = SCRAPE_LIMIT,
    enabled: list[str] | None = None,
) -> list[dict]:
    """
    Run all (or selected) scrapers and return the aggregated job list.

    Args:
        keyword:  Job search keyword.
        location: Job location filter.
        limit:    Max jobs per scraper.
        enabled:  Optional list of scraper names to enable.

    Returns:
        Combined list of job dicts from all scrapers.
    """
    scrapers = get_all_scrapers(enabled)
    all_jobs: list[dict] = []

    for scraper in scrapers:
        try:
            jobs = scraper.search(keyword, location, limit)
            logger.info(f"[{scraper.name}] returned {len(jobs)} jobs.")
            all_jobs.extend(jobs)
        except Exception as e:
            logger.error(f"[{scraper.name}] scraper crashed: {e}")

    logger.info(f"Total jobs from {len(scrapers)} scrapers: {len(all_jobs)}")
    return all_jobs

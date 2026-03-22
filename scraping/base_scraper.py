"""
base_scraper.py
───────────────
Abstract base class for all job scrapers.
Provides shared retry/backoff logic, common headers, and schema enforcement.
"""

import logging
import time
from abc import ABC, abstractmethod
from config import SCRAPE_LIMIT, SCRAPE_RETRIES

logger = logging.getLogger(__name__)

# Common browser-like headers shared across all scrapers
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

REQUIRED_KEYS = {"title", "company", "link", "description", "source"}


class BaseScraper(ABC):
    """Abstract base for all job scrapers."""

    name: str = "Base"

    def __init__(self, retries: int = SCRAPE_RETRIES, default_limit: int = SCRAPE_LIMIT):
        self.retries = retries
        self.default_limit = default_limit

    # ── Public API ───────────────────────────────────────────────────────
    def search(self, keyword: str, location: str = "", limit: int | None = None) -> list[dict]:
        """
        Search for jobs with automatic retry/backoff.
        Falls back to dummy data if all attempts fail.
        """
        limit = limit or self.default_limit
        logger.info(f"[{self.name}] Searching for '{keyword}' in '{location}' (limit={limit})...")

        for attempt in range(1, self.retries + 1):
            try:
                jobs = self._scrape(keyword, location, limit)
                if not jobs:
                    raise ValueError("No job cards found – page may have changed or blocked request")
                self._validate(jobs)
                logger.info(f"[{self.name}] Found {len(jobs)} jobs.")
                return jobs
            except Exception as e:
                wait = 2 ** attempt
                logger.warning(
                    f"[{self.name}] Attempt {attempt}/{self.retries} failed: {e}. "
                    f"Retrying in {wait}s..."
                )
                time.sleep(wait)

        logger.error(f"[{self.name}] All attempts failed. Returning fallback data.")
        return self._fallback_jobs()

    # ── Subclass hooks ───────────────────────────────────────────────────
    @abstractmethod
    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        """Implement the actual scraping logic. Return list of job dicts."""
        ...

    @abstractmethod
    def _fallback_jobs(self) -> list[dict]:
        """Return hard-coded dummy jobs so the pipeline never breaks."""
        ...

    # ── Helpers ──────────────────────────────────────────────────────────
    def _validate(self, jobs: list[dict]):
        """Ensure every job dict has the required keys."""
        for job in jobs:
            missing = REQUIRED_KEYS - job.keys()
            if missing:
                raise ValueError(f"Job dict missing keys {missing}: {job}")

    def _headers(self, extra: dict | None = None) -> dict:
        """Return default headers merged with any extras."""
        headers = DEFAULT_HEADERS.copy()
        if extra:
            headers.update(extra)
        return headers

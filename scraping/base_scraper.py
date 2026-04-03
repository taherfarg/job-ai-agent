"""
base_scraper.py
───────────────
Abstract base class for all job scrapers.
Provides shared retry/backoff logic, common headers, schema enforcement,
and a Playwright-based HTML fallback for sites that block standard requests.
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
        Returns an empty list if all attempts fail (no more dummy data).
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

        # ── All standard attempts failed – try Playwright as last resort ──
        logger.info(f"[{self.name}] Standard scraping failed. Trying Playwright browser fallback...")
        try:
            jobs = self._scrape_with_playwright(keyword, location, limit)
            if jobs:
                self._validate(jobs)
                logger.info(f"[{self.name}] Playwright fallback found {len(jobs)} jobs.")
                return jobs
        except Exception as e:
            logger.warning(f"[{self.name}] Playwright fallback also failed: {e}")

        logger.error(f"[{self.name}] All attempts failed. Returning empty list (no dummy data).")
        return []

    # ── Subclass hooks ───────────────────────────────────────────────────
    @abstractmethod
    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        """Implement the actual scraping logic. Return list of job dicts."""
        ...

    def _build_search_url(self, keyword: str, location: str) -> str:
        """Override in subclasses to return the search URL for Playwright fallback."""
        return ""

    def _parse_playwright_html(self, html: str, url: str, limit: int) -> list[dict]:
        """
        Override in subclasses to parse the HTML returned by Playwright.
        Defaults to calling _scrape_from_soup if the subclass implements it.
        """
        return []

    # ── Playwright fallback ──────────────────────────────────────────────
    def _scrape_with_playwright(self, keyword: str, location: str, limit: int) -> list[dict]:
        """
        Use a real headless Chromium browser via Playwright to load the page.
        This bypasses Cloudflare, 403 blocks, and JS-rendered content.
        """
        url = self._build_search_url(keyword, location)
        if not url:
            return []

        html = self._get_html_playwright(url)
        if not html:
            return []

        return self._parse_playwright_html(html, url, limit)

    def _get_html_playwright(self, url: str, wait_ms: int = 5000) -> str:
        """
        Launch a headless Chromium browser to fetch the full rendered HTML.
        Returns the page HTML as a string, or empty string on failure.
        """
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=DEFAULT_HEADERS["User-Agent"],
                    viewport={"width": 1280, "height": 800},
                )
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(wait_ms)  # Let JS render

                # Scroll down to trigger lazy loading
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                page.wait_for_timeout(2000)

                html = page.content()
                browser.close()
                return html

        except Exception as e:
            logger.error(f"[{self.name}] Playwright HTML extraction failed: {e}")
            return ""

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

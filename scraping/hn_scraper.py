"""
hn_scraper.py
─────────────
Scrapes Hacker News 'Who is Hiring?' threads via the Algolia HN API.
Always works — no auth, no bot protection, real live data.
"""

import re
import requests
import logging
from datetime import datetime
from scraping.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

HN_ALGOLIA_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"


class HNScraper(BaseScraper):
    name = "HackerNews"

    def _get_current_hiring_thread_id(self) -> str | None:
        """Find the most recent 'Ask HN: Who is hiring?' story ID."""
        try:
            params = {
                "query": "Ask HN: Who is hiring?",
                "tags": "story,ask_hn",
                "hitsPerPage": 5,
            }
            r = requests.get(HN_ALGOLIA_SEARCH_URL, params=params, timeout=10)
            r.raise_for_status()
            hits = r.json().get("hits", [])
            for hit in hits:
                title = hit.get("title", "")
                if "Who is hiring?" in title:
                    logger.info(f"Found HN hiring thread: '{title}' (ID: {hit['objectID']})")
                    return hit["objectID"]
        except Exception as e:
            logger.warning(f"Could not fetch HN thread ID: {e}")
        return None

    def _scrape(self, keyword: str, location: str, limit: int) -> list[dict]:
        thread_id = self._get_current_hiring_thread_id()
        if not thread_id:
            return []  # Will trigger fallback

        params = {
            "query": keyword,
            "tags": f"comment,story_{thread_id}",
            "hitsPerPage": limit,
        }
        r = requests.get(HN_ALGOLIA_SEARCH_URL, params=params, timeout=10)
        r.raise_for_status()
        hits = r.json().get("hits", [])

        jobs = []
        for hit in hits:
            text = hit.get("comment_text", "")
            author = hit.get("author", "Unknown")
            story_id = hit.get("objectID", "")

            first_line = text.split("<p>")[0].replace("<br>", " ").strip()
            first_line = re.sub(r"<[^>]+>", "", first_line)
            if not first_line:
                continue

            clean_text = re.sub(r"<[^>]+>", " ", text)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()[:600]

            jobs.append({
                "title": first_line[:120],
                "company": author,
                "link": f"https://news.ycombinator.com/item?id={story_id}",
                "description": clean_text or first_line,
                "source": "HackerNews",
            })

        return jobs

    def _fallback_jobs(self) -> list[dict]:
        # HN API is highly reliable — return empty on failure
        return []


# ── Legacy function for backwards compatibility ────────────────────────────
def search_hn_jobs(keyword: str, limit: int = 15) -> list[dict]:
    return HNScraper().search(keyword, "", limit)

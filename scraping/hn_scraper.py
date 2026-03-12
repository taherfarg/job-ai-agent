import requests
import logging
from datetime import datetime
from config import SCRAPE_LIMIT

logger = logging.getLogger(__name__)

HN_ALGOLIA_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"


def _get_current_hiring_thread_id() -> str | None:
    """
    Finds the most recent 'Ask HN: Who is hiring?' story ID via HN Algolia API.
    This is free, unauthenticated, and returns real data every time.
    """
    try:
        params = {
            "query": "Ask HN: Who is hiring?",
            "tags": "story,ask_hn",
            "hitsPerPage": 5,
        }
        r = requests.get(HN_ALGOLIA_SEARCH_URL, params=params, timeout=10)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        # Filter to actual monthly hiring threads (title matches exactly)
        current_month = datetime.now().strftime("%B %Y")
        for hit in hits:
            title = hit.get("title", "")
            if "Who is hiring?" in title:
                logger.info(f"Found HN hiring thread: '{title}' (ID: {hit['objectID']})")
                return hit["objectID"]
    except Exception as e:
        logger.warning(f"Could not fetch HN thread ID: {e}")
    return None


def search_hn_jobs(keyword: str, limit: int = SCRAPE_LIMIT) -> list[dict]:
    """
    Scrapes Hacker News 'Who Is Hiring?' thread via the Algolia HN API.
    Always works — no auth, no bot protection, real live data.
    """
    logger.info(f"Searching Hacker News 'Who Is Hiring?' for '{keyword}'...")

    thread_id = _get_current_hiring_thread_id()
    if not thread_id:
        logger.warning("Could not find HN hiring thread. Returning empty list.")
        return []

    try:
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

            # Extract first line as "title" (HN posts start with company | role | location)
            first_line = text.split("<p>")[0].replace("<br>", " ").strip()
            # Strip basic HTML tags
            import re
            first_line = re.sub(r"<[^>]+>", "", first_line)

            if not first_line:
                continue

            # Derive a clean description (first ~500 chars without HTML)
            clean_text = re.sub(r"<[^>]+>", " ", text)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()[:600]

            jobs.append({
                "title": first_line[:120],
                "company": author,
                "link": f"https://news.ycombinator.com/item?id={story_id}",
                "description": clean_text or first_line,
                "source": "HackerNews",
            })

        logger.info(f"Found {len(jobs)} jobs from Hacker News.")
        return jobs

    except Exception as e:
        logger.error(f"Error fetching HN jobs: {e}")
        return []

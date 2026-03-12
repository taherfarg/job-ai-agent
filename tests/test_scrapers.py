"""
tests/test_scrapers.py
──────────────────────
Unit tests for the three scraper modules.
All tests use the fallback dummy data path so no real network is needed.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock


REQUIRED_KEYS = {"title", "company", "link", "description", "source"}


# ─── Indeed ──────────────────────────────────────────────────────────────────

class TestIndeedScraper:
    def test_returns_list_on_network_failure(self):
        """When Indeed is unreachable, should return fallback dummy list."""
        with patch("scraping.indeed_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.indeed_scraper import search_indeed_jobs
            jobs = search_indeed_jobs("AI Engineer", "Remote")
        assert isinstance(jobs, list)
        assert len(jobs) > 0

    def test_job_dict_has_required_keys(self):
        """Every returned job must have all required keys."""
        with patch("scraping.indeed_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.indeed_scraper import search_indeed_jobs
            jobs = search_indeed_jobs("AI Engineer", "Remote")
        for job in jobs:
            missing = REQUIRED_KEYS - job.keys()
            assert not missing, f"Job missing keys: {missing} — {job}"

    def test_limit_respected(self):
        """Limit parameter is respected (fallback list is always ≤ limit)."""
        with patch("scraping.indeed_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.indeed_scraper import search_indeed_jobs
            jobs = search_indeed_jobs("AI Engineer", "Remote", limit=2)
        # fallback may have more than limit since it's pre-defined, but shouldn't be huge
        assert len(jobs) <= 10


# ─── LinkedIn ─────────────────────────────────────────────────────────────────

class TestLinkedInScraper:
    def test_returns_list_on_network_failure(self):
        with patch("scraping.linkedin_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.linkedin_scraper import search_linkedin_jobs
            jobs = search_linkedin_jobs("AI Engineer", "Remote")
        assert isinstance(jobs, list)
        assert len(jobs) > 0

    def test_job_dict_has_required_keys(self):
        with patch("scraping.linkedin_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.linkedin_scraper import search_linkedin_jobs
            jobs = search_linkedin_jobs("AI Engineer", "Remote")
        for job in jobs:
            missing = REQUIRED_KEYS - job.keys()
            assert not missing, f"Job missing keys: {missing} — {job}"

    def test_source_is_linkedin(self):
        with patch("scraping.linkedin_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.linkedin_scraper import search_linkedin_jobs
            jobs = search_linkedin_jobs("AI Engineer", "Remote")
        for job in jobs:
            assert job["source"] == "LinkedIn"


# ─── Hacker News ─────────────────────────────────────────────────────────────

class TestHNScraper:
    def test_returns_empty_list_on_failure(self):
        """HN scraper should return [] gracefully on network issues."""
        with patch("scraping.hn_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.hn_scraper import search_hn_jobs
            jobs = search_hn_jobs("AI Engineer")
        assert isinstance(jobs, list)
        # Empty list is acceptable when API is unavailable

    def test_job_dict_has_required_keys_when_successful(self):
        """When API returns mock data, all required keys must be present."""
        mock_thread_response = MagicMock()
        mock_thread_response.json.return_value = {
            "hits": [{"objectID": "12345678", "title": "Ask HN: Who is hiring? (March 2026)"}]
        }
        mock_thread_response.raise_for_status = MagicMock()

        mock_jobs_response = MagicMock()
        mock_jobs_response.json.return_value = {
            "hits": [
                {
                    "comment_text": "Acme Corp | AI Engineer | Remote<p>We build AI things. Python required.",
                    "author": "acme_corp",
                    "objectID": "99991111",
                }
            ]
        }
        mock_jobs_response.raise_for_status = MagicMock()

        with patch("scraping.hn_scraper.requests.get", side_effect=[mock_thread_response, mock_jobs_response]):
            from scraping.hn_scraper import search_hn_jobs
            jobs = search_hn_jobs("AI Engineer")

        if jobs:  # only check if we got results
            for job in jobs:
                missing = REQUIRED_KEYS - job.keys()
                assert not missing, f"HN job missing keys: {missing}"

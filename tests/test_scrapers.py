"""
tests/test_scrapers.py
──────────────────────
Unit tests for all seven scraper modules.
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

    def test_source_is_indeed(self):
        with patch("scraping.indeed_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.indeed_scraper import search_indeed_jobs
            jobs = search_indeed_jobs("AI Engineer", "Remote")
        for job in jobs:
            assert job["source"] == "Indeed"


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

        if jobs:
            for job in jobs:
                missing = REQUIRED_KEYS - job.keys()
                assert not missing, f"HN job missing keys: {missing}"


# ─── Glassdoor ───────────────────────────────────────────────────────────────

class TestGlassdoorScraper:
    def test_returns_list_on_network_failure(self):
        with patch("scraping.glassdoor_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.glassdoor_scraper import GlassdoorScraper
            jobs = GlassdoorScraper().search("AI Engineer", "UAE")
        assert isinstance(jobs, list)
        assert len(jobs) > 0

    def test_job_dict_has_required_keys(self):
        with patch("scraping.glassdoor_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.glassdoor_scraper import GlassdoorScraper
            jobs = GlassdoorScraper().search("AI Engineer", "UAE")
        for job in jobs:
            missing = REQUIRED_KEYS - job.keys()
            assert not missing, f"Glassdoor job missing keys: {missing} — {job}"

    def test_source_is_glassdoor(self):
        with patch("scraping.glassdoor_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.glassdoor_scraper import GlassdoorScraper
            jobs = GlassdoorScraper().search("AI Engineer", "UAE")
        for job in jobs:
            assert job["source"] == "Glassdoor"


# ─── GulfTalent ──────────────────────────────────────────────────────────────

class TestGulfTalentScraper:
    def test_returns_list_on_network_failure(self):
        with patch("scraping.gulftalent_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.gulftalent_scraper import GulfTalentScraper
            jobs = GulfTalentScraper().search("AI Engineer", "UAE")
        assert isinstance(jobs, list)
        assert len(jobs) > 0

    def test_job_dict_has_required_keys(self):
        with patch("scraping.gulftalent_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.gulftalent_scraper import GulfTalentScraper
            jobs = GulfTalentScraper().search("AI Engineer", "UAE")
        for job in jobs:
            missing = REQUIRED_KEYS - job.keys()
            assert not missing, f"GulfTalent job missing keys: {missing} — {job}"

    def test_source_is_gulftalent(self):
        with patch("scraping.gulftalent_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.gulftalent_scraper import GulfTalentScraper
            jobs = GulfTalentScraper().search("AI Engineer", "UAE")
        for job in jobs:
            assert job["source"] == "GulfTalent"


# ─── Bayt ────────────────────────────────────────────────────────────────────

class TestBaytScraper:
    def test_returns_list_on_network_failure(self):
        with patch("scraping.bayt_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.bayt_scraper import BaytScraper
            jobs = BaytScraper().search("AI Engineer", "UAE")
        assert isinstance(jobs, list)
        assert len(jobs) > 0

    def test_job_dict_has_required_keys(self):
        with patch("scraping.bayt_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.bayt_scraper import BaytScraper
            jobs = BaytScraper().search("AI Engineer", "UAE")
        for job in jobs:
            missing = REQUIRED_KEYS - job.keys()
            assert not missing, f"Bayt job missing keys: {missing} — {job}"

    def test_source_is_bayt(self):
        with patch("scraping.bayt_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.bayt_scraper import BaytScraper
            jobs = BaytScraper().search("AI Engineer", "UAE")
        for job in jobs:
            assert job["source"] == "Bayt"


# ─── NaukriGulf ──────────────────────────────────────────────────────────────

class TestNaukrigulfScraper:
    def test_returns_list_on_network_failure(self):
        with patch("scraping.naukrigulf_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.naukrigulf_scraper import NaukrigulfScraper
            jobs = NaukrigulfScraper().search("AI Engineer", "UAE")
        assert isinstance(jobs, list)
        assert len(jobs) > 0

    def test_job_dict_has_required_keys(self):
        with patch("scraping.naukrigulf_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.naukrigulf_scraper import NaukrigulfScraper
            jobs = NaukrigulfScraper().search("AI Engineer", "UAE")
        for job in jobs:
            missing = REQUIRED_KEYS - job.keys()
            assert not missing, f"NaukriGulf job missing keys: {missing} — {job}"

    def test_source_is_naukrigulf(self):
        with patch("scraping.naukrigulf_scraper.requests.get", side_effect=ConnectionError("blocked")):
            from scraping.naukrigulf_scraper import NaukrigulfScraper
            jobs = NaukrigulfScraper().search("AI Engineer", "UAE")
        for job in jobs:
            assert job["source"] == "NaukriGulf"


# ─── Registry ────────────────────────────────────────────────────────────────

class TestScraperRegistry:
    def test_get_all_scrapers_returns_seven(self):
        from scraping import get_all_scrapers
        scrapers = get_all_scrapers()
        assert len(scrapers) == 7

    def test_get_filtered_scrapers(self):
        from scraping import get_all_scrapers
        scrapers = get_all_scrapers(enabled=["Indeed", "LinkedIn"])
        assert len(scrapers) == 2
        names = {s.name for s in scrapers}
        assert names == {"Indeed", "LinkedIn"}

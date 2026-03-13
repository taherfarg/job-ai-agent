"""
tests/test_vector_db.py
────────────────────────
Unit tests for FAISS vector DB: build_index and search_index.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pathlib import Path
import tempfile


class TestBuildIndex:
    def test_build_index_creates_file(self, tmp_path, monkeypatch):
        """build_vector_index should create the FAISS .bin file."""
        # Redirect VECTOR_INDEX_FILE to tmp_path
        import config
        original = config.VECTOR_INDEX_FILE
        config.VECTOR_INDEX_FILE = tmp_path / "test_faiss.bin"

        try:
            from vector_db.build_index import build_vector_index
            result = build_vector_index("Python AI Engineer with NLP and LLM experience")
            assert result is True
            assert config.VECTOR_INDEX_FILE.exists(), "FAISS index file was not created"
        finally:
            config.VECTOR_INDEX_FILE = original

    def test_build_index_rejects_empty_text(self):
        """build_vector_index should return False for empty CV text."""
        from vector_db.build_index import build_vector_index
        result = build_vector_index("")
        assert result is False

    def test_build_index_rejects_none(self):
        """build_vector_index should handle None gracefully."""
        from vector_db.build_index import build_vector_index
        result = build_vector_index(None)
        assert result is False


class TestSearchIndex:
    def test_score_jobs_returns_same_count(self, tmp_path, monkeypatch):
        """
        score_jobs_against_cv should return the same number of jobs it received.
        Build a temp index first, then score.
        """
        import config
        original = config.VECTOR_INDEX_FILE
        config.VECTOR_INDEX_FILE = tmp_path / "test_faiss.bin"

        try:
            from vector_db.build_index import build_vector_index
            from vector_db.search_index import score_jobs_against_cv

            build_vector_index("Python AI Engineer with LangChain and FAISS experience.")

            jobs = [
                {"title": "AI Engineer", "company": "Acme", "link": "http://a.com/1",
                 "description": "LangChain Python LLM experience required.", "source": "Test"},
                {"title": "Data Scientist", "company": "Beta", "link": "http://b.com/2",
                 "description": "Statistics R SQL experience.", "source": "Test"},
            ]
            scored = score_jobs_against_cv(jobs)
            assert len(scored) == len(jobs), "Scored jobs count mismatch"
        finally:
            config.VECTOR_INDEX_FILE = original

    def test_semantic_scores_are_floats_in_range(self, tmp_path):
        """All semantic_score values must be floats in [0.0, 1.0]."""
        import config
        original = config.VECTOR_INDEX_FILE
        config.VECTOR_INDEX_FILE = tmp_path / "test_faiss2.bin"

        try:
            from vector_db.build_index import build_vector_index
            from vector_db.search_index import score_jobs_against_cv

            build_vector_index("AI Engineer experienced with Python, PyTorch, NLP, LLMs.")

            jobs = [
                {"title": "ML Engineer", "company": "X", "link": "http://x.com",
                 "description": "Machine learning Python experience.", "source": "Test"},
            ]
            scored = score_jobs_against_cv(jobs)
            for job in scored:
                assert "semantic_score" in job
                assert isinstance(job["semantic_score"], float)
                assert 0.0 <= job["semantic_score"] <= 1.0, \
                    f"Score out of range: {job['semantic_score']}"
        finally:
            config.VECTOR_INDEX_FILE = original

    def test_score_jobs_empty_list(self):
        """Empty input returns empty list without error."""
        from vector_db.search_index import score_jobs_against_cv
        result = score_jobs_against_cv([])
        assert result == []

    def test_ai_job_scores_higher_than_unrelated(self, tmp_path):
        """An AI-related job should score higher than an unrelated one against an AI CV."""
        from unittest.mock import patch
        index_path = tmp_path / "test_faiss3.bin"

        # Patch the path in BOTH modules so they see the same temp file
        with patch("vector_db.build_index.VECTOR_INDEX_FILE", index_path), \
             patch("vector_db.search_index.VECTOR_INDEX_FILE", index_path):

            from vector_db.build_index import build_vector_index
            from vector_db.search_index import score_jobs_against_cv

            build_vector_index(
                "AI Engineer with Python, TensorFlow, NLP, LLMs, LangChain, RAG, FAISS."
            )

            jobs = [
                {"title": "AI Engineer", "company": "A", "link": "http://a.com",
                 "description": "Build LLM applications using Python and LangChain.", "source": "T"},
                {"title": "Warehouse Worker", "company": "B", "link": "http://b.com",
                 "description": "Lift heavy boxes in a warehouse. No technical skills needed.", "source": "T"},
            ]
            scored = score_jobs_against_cv(jobs)
            ai_job = next(j for j in scored if "AI" in j["title"])
            warehouse_job = next(j for j in scored if "Warehouse" in j["title"])
            assert ai_job["semantic_score"] > warehouse_job["semantic_score"], \
                "AI job should score higher than warehouse job against an AI CV"

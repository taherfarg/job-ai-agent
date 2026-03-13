"""
tests/test_cv_parser.py
────────────────────────
Unit tests for the CV parser utility.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from utils.cv_parser import load_cv


class TestCVParser:
    def test_load_cv_with_text_file(self, tmp_path):
        """load_cv should read plain-text files directly."""
        cv_file = tmp_path / "test_cv.txt"
        cv_file.write_text("Python Developer | AI Engineer | 5 years experience")
        result = load_cv(cv_file)
        assert result == "Python Developer | AI Engineer | 5 years experience"

    def test_load_cv_returns_string(self, tmp_path):
        """Return type is always str."""
        cv_file = tmp_path / "test_cv.txt"
        cv_file.write_text("Some CV text")
        result = load_cv(cv_file)
        assert isinstance(result, str)

    def test_load_cv_missing_file_returns_empty(self, tmp_path):
        """Returns empty string when CV file is not found."""
        missing = tmp_path / "nonexistent.pdf"
        result = load_cv(missing)
        assert result == ""

    def test_load_cv_default_path_returns_something(self):
        """The default CV path (from config) should always work in this repo."""
        result = load_cv()
        assert isinstance(result, str)
        assert len(result) > 0, "Default CV returned empty string — check data/TAHER FARG CV.pdf"

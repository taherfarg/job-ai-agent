import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# File Paths
CV_PATH = DATA_DIR / "TAHER FARG CV.pdf"
APPLIED_JOBS_CSV = DATA_DIR / "applied_jobs.csv"

# Model Configurations
LLM_MODEL = "qwen3.5:cloud"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_INDEX_FILE = DATA_DIR / "faiss_index.bin"
VECTOR_DIMENSION = 384

# Job Search Settings
JOB_KEYWORD = os.getenv("JOB_KEYWORD", "AI Engineer")
JOB_LOCATION = os.getenv("JOB_LOCATION", "Remote")
MIN_MATCH_SCORE = int(os.getenv("MIN_MATCH_SCORE", "75"))
MAX_APPLICATIONS_PER_DAY = int(os.getenv("MAX_APPLICATIONS_PER_DAY", "20"))
SCRAPE_LIMIT = int(os.getenv("SCRAPE_LIMIT", "15"))
SCRAPE_RETRIES = int(os.getenv("SCRAPE_RETRIES", "3"))

# Enabled Scrapers (comma-separated list, or empty for all)
# Options: Indeed, LinkedIn, HackerNews, Glassdoor, GulfTalent, Bayt, NaukriGulf
_raw_scrapers = os.getenv("ENABLED_SCRAPERS", "")
ENABLED_SCRAPERS = [s.strip() for s in _raw_scrapers.split(",") if s.strip()] if _raw_scrapers else []

# Applicant Contact Info (used by Playwright automation)
APPLICANT_EMAIL = os.getenv("APPLICANT_EMAIL", "taherfarg50@gmail.com")
APPLICANT_PHONE = os.getenv("APPLICANT_PHONE", "+971547224740")

# Ensure dummy CV exists for testing
if not CV_PATH.exists():
    with open(CV_PATH, 'w') as f:
        f.write("Dummy CV for testing (replace with actual PDF)")

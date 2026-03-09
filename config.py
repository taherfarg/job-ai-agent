import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# File Paths
CV_PATH = DATA_DIR / "TAHER FARG CV.pdf"
APPLIED_JOBS_CSV = DATA_DIR / "applied_jobs.csv"

# Model Configurations
LLM_MODEL = "qwen3.5:cloud"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_INDEX_FILE = DATA_DIR / "faiss_index.bin"
VECTOR_DIMENSION = 384

# Application Rules
MIN_MATCH_SCORE = 80
MAX_APPLICATIONS_PER_DAY = 20

# Add dummy CV for testing if it doesn't exist
if not CV_PATH.exists():
    with open(CV_PATH, 'w') as f:
        f.write("Dummy CV for testing (replace with actual PDF)")

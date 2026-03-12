import logging
import os

os.environ.setdefault("OPENAI_API_KEY", "NA")

from utils.cv_parser import load_cv
from vector_db.build_index import build_vector_index
from vector_db.search_index import score_jobs_against_cv
from scraping.indeed_scraper import search_indeed_jobs
from scraping.linkedin_scraper import search_linkedin_jobs
from scraping.hn_scraper import search_hn_jobs
from agents.crew_workflow import run_job_search_crew
from config import JOB_KEYWORD, JOB_LOCATION, SCRAPE_LIMIT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_agent():
    logger.info("Starting Job AI Agent workflow...")
    logger.info(f"Searching for: '{JOB_KEYWORD}' in '{JOB_LOCATION}' (limit: {SCRAPE_LIMIT})")

    # ── Step 1: Load CV ──────────────────────────────────────────────────────────
    cv_text = load_cv()
    if not cv_text:
        logger.error("No CV text found. Aborting.")
        return

    # ── Step 2: Build / Update FAISS Vector Index from CV ────────────────────────
    build_vector_index(cv_text)

    # ── Step 3: Scrape Jobs from All Sources ─────────────────────────────────────
    logger.info("Scraping jobs from Indeed, LinkedIn, and Hacker News...")
    indeed_jobs = search_indeed_jobs(JOB_KEYWORD, JOB_LOCATION, SCRAPE_LIMIT)
    linkedin_jobs = search_linkedin_jobs(JOB_KEYWORD, JOB_LOCATION, SCRAPE_LIMIT)
    hn_jobs = search_hn_jobs(JOB_KEYWORD, SCRAPE_LIMIT)

    all_jobs = indeed_jobs + linkedin_jobs + hn_jobs
    logger.info(f"Total raw jobs fetched: {len(all_jobs)} "
                f"(Indeed: {len(indeed_jobs)}, LinkedIn: {len(linkedin_jobs)}, HN: {len(hn_jobs)})")

    if not all_jobs:
        logger.error("No jobs found from any source. Aborting.")
        return

    # ── Step 4: Semantic Scoring via FAISS ───────────────────────────────────────
    logger.info("Running semantic similarity scoring against CV...")
    scored_jobs = score_jobs_against_cv(all_jobs)

    # ── Step 5: Trigger CrewAI Multi-Agent Workflow ──────────────────────────────
    logger.info("Triggering CrewAI workflow...")
    run_job_search_crew(cv_text, scored_jobs)

    logger.info("Job AI Agent workflow completed.")


if __name__ == "__main__":
    logger.info("Job-Searching AI Agent Initialized.")
    run_agent()

    # Uncomment to schedule daily runs at 09:00
    # import schedule, time
    # schedule.every().day.at("09:00").do(run_agent)
    # logger.info("Scheduler started. Waiting for next execution...")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)

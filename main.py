import logging
import schedule
import time
import os

os.environ["OPENAI_API_KEY"] = "NA"
import time
from utils.cv_parser import load_cv
from vector_db.build_index import build_vector_index
from agents.crew_workflow import run_job_search_crew

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_agent():
    logger.info("Starting Job AI Agent workflow...")
    
    # 1. Load CV
    cv_text = load_cv()
    if not cv_text:
        logger.error("No CV text found. Aborting.")
        return

    # 2. Build or Update Vector DB for CV
    build_vector_index(cv_text)
    
    # 3. Trigger CrewAI multi-agent workflow
    logger.info("Triggering CrewAI workflow...")
    run_job_search_crew(cv_text)
    
    logger.info("Job AI Agent workflow completed.")

if __name__ == "__main__":
    logger.info("Job-Searching AI Agent Initialized.")
    # Run once immediately for testing
    run_agent()
    
    # Schedule to run daily at 09:00
    # schedule.every().day.at("09:00").do(run_agent)
    # logger.info("Scheduler started. Waiting for next execution...")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)

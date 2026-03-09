import logging
import json
import pandas as pd
from datetime import datetime
from crewai import Crew, Process
from agents.job_finder_agent import JobFinderAgents
from agents.job_analyzer_agent import JobAnalyzerAgents
from agents.application_agent import ApplicationAgents
from automation.apply_playwright import apply_to_job
from config import CV_PATH, APPLIED_JOBS_CSV, MAX_APPLICATIONS_PER_DAY

logger = logging.getLogger(__name__)

def save_application(url: str, status: str):
    data = {"url": url, "status": status, "date": datetime.now().isoformat()}
    df = pd.DataFrame([data])
    if not APPLIED_JOBS_CSV.exists():
        df.to_csv(APPLIED_JOBS_CSV, index=False)
    else:
        df.to_csv(APPLIED_JOBS_CSV, mode='a', header=False, index=False)

def run_job_search_crew(cv_text: str):
    logger.info("Initializing Agent Crew...")
    
    # Keyword/Location can be parameterized
    keyword = "AI Engineer"
    location = "Remote"
    
    finder_mod = JobFinderAgents()
    analyzer_mod = JobAnalyzerAgents()
    applier_mod = ApplicationAgents()
    
    finder_agent = finder_mod.create_finder_agent()
    analyzer_agent = analyzer_mod.create_analyzer_agent()
    applier_agent = applier_mod.create_apply_agent()
    
    search_task = finder_mod.create_search_task(finder_agent, keyword, location)
    analysis_task = analyzer_mod.create_analysis_task(analyzer_agent, cv_text)
    apply_task = applier_mod.create_apply_task(applier_agent, MAX_APPLICATIONS_PER_DAY)
    
    # Establish Sequence: Output of search -> input to analysis -> input to apply
    analysis_task.context = [search_task]
    apply_task.context = [analysis_task]

    crew = Crew(
        agents=[finder_agent, analyzer_agent, applier_agent],
        tasks=[search_task, analysis_task, apply_task],
        process=Process.sequential,
        verbose=True
    )
    
    logger.info("Kicking off the CrewAI Process...")
    try:
        result = crew.kickoff()
        logger.info(f"CrewAI Process Output: {result}")
        
        # In a robust implementation, the applier_agent would output a clean list of URLs, 
        # but since LLM output may vary, we parse loosely or use proper format enforcers (like Pydantic).
        
        # Here we do a generic fallback: If there's URLs in the final text, try to apply!
        # For simplicity, we assume result is a list of strings or string with URLs
        # In production this requires Strict JSON parsing.
        
        # For demonstration of the architectural flow:
        # We simulate reading the URLs and driving Playwright
        raw_result_str = str(result)
        urls_to_apply = [line.strip() for line in raw_result_str.split() if line.startswith("http")]
        
        applied_count = 0
        for url in urls_to_apply[:MAX_APPLICATIONS_PER_DAY]:
            logger.info(f"Dispatching apply task for {url}")
            success = apply_to_job(url, str(CV_PATH))
            status = "SUCCESS" if success else "FAILED"
            save_application(url, status)
            applied_count += 1
            
        logger.info(f"Workflow Complete. Attempted applications: {applied_count}")
        
    except Exception as e:
        logger.error(f"Crew AI execution failed: {e}")

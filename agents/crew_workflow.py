import logging
import json
import re
import pandas as pd
from datetime import datetime
from crewai import Crew, Process
from agents.job_finder_agent import JobFinderAgents
from agents.job_analyzer_agent import JobAnalyzerAgents
from agents.application_agent import ApplicationAgents
from automation.apply_playwright import apply_to_job
from vector_db.search_index import score_jobs_against_cv
from utils.reporter import generate_report
from config import (
    CV_PATH, APPLIED_JOBS_CSV, MAX_APPLICATIONS_PER_DAY,
    JOB_KEYWORD, JOB_LOCATION
)

logger = logging.getLogger(__name__)


def save_application(job: dict, status: str):
    """Append a single application record to the CSV log."""
    data = {
        "title": job.get("title", ""),
        "company": job.get("company", ""),
        "url": job.get("link", ""),
        "source": job.get("source", ""),
        "semantic_score": job.get("semantic_score", ""),
        "status": status,
        "date": datetime.now().isoformat(),
    }
    df = pd.DataFrame([data])
    if not APPLIED_JOBS_CSV.exists():
        df.to_csv(APPLIED_JOBS_CSV, index=False)
    else:
        df.to_csv(APPLIED_JOBS_CSV, mode="a", header=False, index=False)


def _parse_apply_urls(raw_output: str) -> list[str]:
    """
    Robustly extract a list of URLs from the applier agent's output.
    Tries JSON parse first, falls back to regex URL extraction.
    """
    # Strategy 1: strict JSON parse
    try:
        # Find the first JSON array in the output
        match = re.search(r"\[.*?\]", raw_output, re.DOTALL)
        if match:
            urls = json.loads(match.group(0))
            if isinstance(urls, list):
                return [u for u in urls if str(u).startswith("http")]
    except (json.JSONDecodeError, Exception):
        pass

    # Strategy 2: regex URL extraction
    urls = re.findall(r"https?://[^\s\"'\]>]+", raw_output)
    return list(dict.fromkeys(urls))  # deduplicate preserving order


def _parse_analysis_jobs(raw_output: str) -> list[dict]:
    """
    Extract the list of job decisions from the analyzer agent's output.
    Returns list of job dicts with decision/score, or [] on parse failure.
    """
    try:
        # Try to find JSON object with a `jobs` key
        match = re.search(r'\{.*?"jobs"\s*:\s*\[.*?\]\s*\}', raw_output, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return data.get("jobs", [])
    except Exception:
        pass

    # Fallback: try to find a bare JSON array
    try:
        match = re.search(r"\[.*?\]", raw_output, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            if isinstance(data, list) and data and isinstance(data[0], dict):
                return data
    except Exception:
        pass

    logger.warning("Could not parse structured JSON from analyzer output.")
    return []


def run_job_search_crew(cv_text: str, jobs_found: list[dict]):
    """
    Run the full CrewAI pipeline.

    Args:
        cv_text:    Candidate CV text.
        jobs_found: All scraped jobs (already includes `semantic_score` field).
    """
    logger.info("Initializing Agent Crew...")

    finder_mod = JobFinderAgents()
    analyzer_mod = JobAnalyzerAgents()
    applier_mod = ApplicationAgents()

    finder_agent = finder_mod.create_finder_agent()
    analyzer_agent = analyzer_mod.create_analyzer_agent()
    applier_agent = applier_mod.create_apply_agent()

    search_task = finder_mod.create_search_task(finder_agent, JOB_KEYWORD, JOB_LOCATION, jobs_found)
    analysis_task = analyzer_mod.create_analysis_task(analyzer_agent, cv_text)
    apply_task = applier_mod.create_apply_task(applier_agent, MAX_APPLICATIONS_PER_DAY)

    analysis_task.context = [search_task]
    apply_task.context = [analysis_task]

    crew = Crew(
        agents=[finder_agent, analyzer_agent, applier_agent],
        tasks=[search_task, analysis_task, apply_task],
        process=Process.sequential,
        verbose=True,
    )

    logger.info("Kicking off the CrewAI Process...")
    jobs_to_apply: list[dict] = []
    applied_jobs: list[dict] = []

    try:
        result = crew.kickoff()
        raw_output = str(result)
        logger.info(f"CrewAI raw output:\n{raw_output[:800]}...")

        # ── Parse the analyzed job list from the analysis task
        for task_output in crew.tasks:
            if hasattr(task_output, "output") and task_output.output:
                parsed = _parse_analysis_jobs(str(task_output.output))
                if parsed:
                    # Merge semantic_score from pre-scored jobs
                    score_map = {j["link"]: j.get("semantic_score", 0.5) for j in jobs_found}
                    for job in parsed:
                        job["semantic_score"] = score_map.get(job.get("link", ""), 0.5)
                    jobs_to_apply = [j for j in parsed if j.get("decision") == "APPLY"]
                    logger.info(f"Analyzer marked {len(jobs_to_apply)} jobs as APPLY.")
                    break

        # ── Parse apply URLs from final crew output
        urls_to_apply = _parse_apply_urls(raw_output)
        logger.info(f"Extracted {len(urls_to_apply)} URLs for application.")

        # ── Build a quick lookup from jobs_to_apply
        job_lookup = {j.get("link", ""): j for j in jobs_to_apply}

        # ── Dispatch Playwright for each approved URL
        applied_count = 0
        for url in urls_to_apply[:MAX_APPLICATIONS_PER_DAY]:
            logger.info(f"Dispatching apply task for: {url}")
            success = apply_to_job(url, str(CV_PATH))
            status = "SUCCESS" if success else "FAILED"
            job_record = job_lookup.get(url, {"title": url, "company": "Unknown", "link": url})
            job_record["status"] = status
            save_application(job_record, status)
            applied_jobs.append(job_record)
            applied_count += 1

        logger.info(f"Workflow complete. Attempted applications: {applied_count}")

    except Exception as e:
        logger.error(f"CrewAI execution failed: {e}")

    # ── Generate run report regardless of errors
    generate_report(jobs_found, jobs_to_apply, applied_jobs, JOB_KEYWORD, JOB_LOCATION)

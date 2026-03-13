from crewai import Agent, Task
from config import LLM_MODEL_FAST
from json import dumps
import logging

logger = logging.getLogger(__name__)


class JobFinderAgents:
    def create_finder_agent(self):
        return Agent(
            role="Senior Job Discovery Specialist",
            goal=(
                "Synthesize raw job listings from multiple sources into a "
                "clean, structured list ready for the Analyzer agent."
            ),
            backstory=(
                "An expert at aggregating and cleaning job market data. "
                "You transform raw, messy listings into perfectly formatted information."
            ),
            verbose=True,
            allow_delegation=False,
            llm=f"ollama/{LLM_MODEL_FAST}",
        )

    def create_search_task(
        self,
        agent,
        keyword: str,
        location: str,
        jobs: list[dict],
    ):
        """
        Build the finder task with pre-fetched and pre-scored jobs injected
        directly into the prompt so sources are aggregated outside the LLM
        (faster, cheaper, more reliable).
        """
        # Trim descriptions to avoid context explosion
        trimmed = []
        for job in jobs:
            trimmed.append({
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "link": job.get("link", ""),
                "description": (job.get("description", "") or "")[:300],
                "source": job.get("source", ""),
                "semantic_score": round(job.get("semantic_score", 0.5), 3),
            })

        jobs_json = dumps(trimmed, indent=2)

        return Task(
            description=f"""
Search keyword: "{keyword}" | Location: "{location}"

I have already fetched and semantically scored raw job listings for you.
Each job has a `semantic_score` (0.0–1.0) showing how well the description matches the candidate's CV.

Raw Job Data:
{jobs_json}

Your task:
1. Review all jobs.
2. Remove any duplicate entries (same company + same title).
3. Format into a clean, numbered markdown list preserving ALL fields.
4. Pass the full list (including links and descriptions) to the Analyzer agent.
""",
            expected_output=(
                "A clean, numbered list of job postings with: Title, Company, Link, "
                "Description (brief), Source, and Semantic Score."
            ),
            agent=agent,
        )

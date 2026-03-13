from crewai import Agent, Task
from config import LLM_MODEL_FAST
import logging

logger = logging.getLogger(__name__)


class ApplicationAgents:
    def create_apply_agent(self):
        return Agent(
            role="Application Coordinator",
            goal="Extract a clean list of job links that should be applied to, respecting daily limits.",
            backstory=(
                "You are a meticulous application coordinator. You receive a JSON list of evaluated jobs "
                "and extract only the URLs that are marked 'APPLY', formatting them precisely for downstream automation."
            ),
            verbose=True,
            allow_delegation=False,
            llm=f"ollama/{LLM_MODEL_FAST}",
        )

    def create_apply_task(self, agent, max_applications: int):
        return Task(
            description=f"""
You will receive a JSON object from the Job Analyzer agent containing a list of evaluated jobs.
Each job has a "decision" field that is either "APPLY" or "SKIP".

Your job:
1. Identify all jobs where decision == "APPLY".
2. Extract their "link" values.
3. Respect the daily limit: maximum {max_applications} links total.
4. Return ONLY a JSON array of URL strings, nothing else.

Example output:
["https://linkedin.com/jobs/view/...", "https://example.com/job/1"]

Do NOT include any explanatory text outside the JSON array.
""",
            expected_output=(
                f"A JSON array of up to {max_applications} URL strings for jobs marked APPLY."
            ),
            agent=agent,
        )

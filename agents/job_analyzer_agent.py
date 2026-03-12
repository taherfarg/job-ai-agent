from crewai import Agent, Task
from pydantic import BaseModel
from typing import List
from config import LLM_MODEL, MIN_MATCH_SCORE
import logging

logger = logging.getLogger(__name__)


class JobDecision(BaseModel):
    title: str
    company: str
    link: str
    score: int
    decision: str   # "APPLY" or "SKIP"
    reason: str


class JobAnalysisOutput(BaseModel):
    jobs: List[JobDecision]


class JobAnalyzerAgents:
    def create_analyzer_agent(self):
        return Agent(
            role="Senior Technical Recruiter & CV Match Evaluator",
            goal=(
                "Rigorously evaluate each job description against the candidate's CV. "
                "Determine fit scores and decide whether to apply."
            ),
            backstory=(
                "You are a hyper-critical senior technical recruiter with 15 years of experience "
                "matching candidates to engineering roles. You are precise, data-driven, "
                "and always output valid JSON."
            ),
            verbose=True,
            allow_delegation=False,
            llm=f"ollama/{LLM_MODEL}",
        )

    def create_analysis_task(self, agent, cv_text: str):
        cv_snippet = cv_text[:3000] if len(cv_text) > 3000 else cv_text

        return Task(
            description=f"""
You will receive a structured list of job listings from the Job Finder agent.
Evaluate each job against the candidate's CV below.

=== CANDIDATE CV (truncated to 3000 chars) ===
{cv_snippet}
=== END CV ===

For EACH job in the list:
1. Read the job title, company, and description carefully.
2. Compare required skills to candidate's actual skills from the CV.
3. Assign a fit score from 0 to 100.
4. If score >= {MIN_MATCH_SCORE}: decision = "APPLY". Otherwise: decision = "SKIP".
5. Write a one-sentence reason for the decision.

Return a valid JSON object matching this schema exactly:
{{
  "jobs": [
    {{
      "title": "...",
      "company": "...",
      "link": "...",
      "score": 85,
      "decision": "APPLY",
      "reason": "Strong match on Python and LLM experience."
    }},
    ...
  ]
}}
Do NOT include any explanation outside the JSON block.
""",
            expected_output=(
                'A valid JSON object with a "jobs" array. Each element has: '
                'title, company, link, score (int 0-100), decision ("APPLY" or "SKIP"), reason (string).'
            ),
            agent=agent,
        )

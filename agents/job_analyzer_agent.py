from crewai import Agent, Task
from config import LLM_MODEL, MIN_MATCH_SCORE
import logging

logger = logging.getLogger(__name__)

class JobAnalyzerAgents:
    def create_analyzer_agent(self):
        return Agent(
            role='Senior Candidate Match Evaluator',
            goal='Analyze job descriptions against a candidate CV and determine if the candidate should apply.',
            backstory='A highly critical Technical Recruiter who expertly screens jobs for candidate fit.',
            verbose=True,
            allow_delegation=False,
            llm=f"ollama/{LLM_MODEL}"
        )
        
    def create_analysis_task(self, agent, cv_text: str):
        return Task(
            description=f'''
            You will receive a list of jobs from the Job Finder agent.
            You must evaluate each job against the candidate's CV text.
            Candidate CV:
            {cv_text[:3000]} # Truncating to avoid context window explosion
            
            For each job:
            1. Determine relevance based on required skills vs candidate skills.
            2. Assign a fit score (0-100).
            3. If the score is >= {MIN_MATCH_SCORE}, mark it as "APPLY". Otherwise "SKIP".
            
            Return the final JSON list of jobs marked with "APPLY" and their URLs.
            ''',
            expected_output='JSON list containing objects with keys: title, company, link, score, decision (APPLY/SKIP), reason.',
            agent=agent
        )

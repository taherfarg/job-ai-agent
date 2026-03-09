from crewai import Agent, Task
from scraping.indeed_scraper import search_indeed_jobs
from scraping.linkedin_scraper import search_linkedin_jobs
from config import LLM_MODEL
from json import dumps
import logging

logger = logging.getLogger(__name__)

class JobFinderAgents:
    def create_finder_agent(self):
        return Agent(
            role='Senior Job Discovery Specialist',
            goal='Search across multiple platforms for highly relevant job postings matching the candidate criteria.',
            backstory='An expert in finding hidden job opportunities and curating massive lists of openings.',
            verbose=True,
            allow_delegation=False,
            llm=f"ollama/{LLM_MODEL}"
        )
        
    def create_search_task(self, agent, keyword: str, location: str):
        # We perform the search directly to feed the data to the analyzer later,
        # or we wrap it in a CrewAI Tool. For simplicity and robustness, we fetch data here
        # and provide it as context, or we can create a custom Tool.
        
        # In a real CrewAI setup with LLM, we would define custom tools. Here we just fetch directly
        # and ask the agent to structure it.
        def fetch_jobs():
            indeed_jobs = search_indeed_jobs(keyword, location)
            linkedin_jobs = search_linkedin_jobs(keyword, location)
            all_jobs = indeed_jobs + linkedin_jobs
            return dumps(all_jobs, indent=2)

        jobs_json = fetch_jobs()

        return Task(
            description=f'''
            Search for "{keyword}" jobs in "{location}". 
            I have already fetched some raw listings for you from the web.
            Raw Job Data: {jobs_json}
            
            Review this data and format it into a clean, structured list so the Analyzer agent can process it.
            Keep all links and descriptions intact.
            ''',
            expected_output='A clean list of jobs with Title, Company, Link, Description, and Source.',
            agent=agent
        )

from crewai import Agent, Task
from config import LLM_MODEL
import logging

logger = logging.getLogger(__name__)

class ApplicationAgents:
    def create_apply_agent(self):
        return Agent(
            role='Application Submitter',
            goal='Take approved job URLs and automatically submit applications using provided tools.',
            backstory='An efficient operative who executes routine application submissions without hesitation.',
            verbose=True,
            allow_delegation=False,
            llm=f"ollama/{LLM_MODEL}"
        )
        
    def create_apply_task(self, agent, max_applications: int):
        # We define a task to parse the Analyzer's JSON and trigger playwright for jobs marked "APPLY"
        return Task(
            description=f'''
            You will receive a list of analyzed jobs from the Job Analyzer agent (usually in JSON).
            Review the list to identify jobs marked "APPLY".
            
            Extract the exact URLs for jobs marked "APPLY".
            There is a maximum limit of {max_applications} applications per day. Stop processing if the limit is reached.
            Format the output strictly as a list of URLs that need to be applied to.
            ''',
            expected_output='A clean list of valid URLs for approved jobs.',
            agent=agent
        )

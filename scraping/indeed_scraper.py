import requests
from bs4 import BeautifulSoup
import logging
import time

logger = logging.getLogger(__name__)

def search_indeed_jobs(keyword: str, location: str = "", limit: int = 10):
    """
    Scrape job listings from Indeed. 
    Note: Indeed has strict anti-scraping measures. This is a basic implementation 
    that might require proxies or Playwright/Selenium for production use.
    """
    logger.info(f"Searching Indeed for '{keyword}' jobs in '{location}'...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    url = f"https://www.indeed.com/jobs?q={keyword}&l={location}"
    
    jobs = []
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Indeed frequently changes its class names. Using a known generic structure.
        for job_card in soup.select(".job_seen_beacon")[:limit]:
            try:
                title_elem = job_card.select_one("h2")
                title = title_elem.text.strip() if title_elem else "Unknown Title"
                
                link_elem = job_card.select_one("a")
                link = f"https://www.indeed.com{link_elem['href']}" if link_elem and link_elem.has_attr("href") else url
                
                company_elem = job_card.select_one('[data-testid="company-name"]')
                company = company_elem.text.strip() if company_elem else "Unknown Company"
                
                description_elem = job_card.select_one('.job-snippet')
                description = description_elem.text.strip() if description_elem else ""

                jobs.append({
                    "title": title,
                    "company": company,
                    "link": link,
                    "description": description,
                    "source": "Indeed"
                })
            except Exception as e:
                logger.debug(f"Error parsing job card: {e}")
                continue

        logger.info(f"Found {len(jobs)} jobs from Indeed.")
        return jobs
    except Exception as e:
        logger.error(f"Error scraping Indeed: {e}")
        # Return fallback dummy data for testing the agent workflow
        logger.info("Returning dummy job data for testing...")
        return [
            {
                "title": f"Senior {keyword} Engineer",
                "company": "Tech Innovators Inc",
                "link": "https://example.com/job/1",
                "description": f"We are looking for a highly skilled {keyword} engineer to join our fast-paced startup...",
                "source": "Dummy Indeed"
            }
        ]

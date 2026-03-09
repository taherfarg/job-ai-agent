import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def search_linkedin_jobs(keyword: str, location: str = "United States", limit: int = 10):
    """
    Search LinkedIn Jobs.
    Uses generic LinkedIn jobs search URL.
    """
    logger.info(f"Searching LinkedIn for '{keyword}' jobs in '{location}'...")
    
    url = f"https://www.linkedin.com/jobs/search?keywords={keyword}&location={location}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    jobs = []
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        job_cards = soup.find_all("div", class_="base-card")
        
        for card in job_cards[:limit]:
            title_elem = card.find("h3", class_="base-search-card__title")
            title = title_elem.text.strip() if title_elem else "Unknown"
            
            company_elem = card.find("h4", class_="base-search-card__subtitle")
            company = company_elem.text.strip() if company_elem else "Unknown"
            
            link_elem = card.find("a", class_="base-card__full-link")
            link = link_elem["href"].split("?")[0] if link_elem else url
            
            jobs.append({
                "title": title,
                "company": company,
                "link": link,
                "description": f"LinkedIn job description for {title} at {company}",
                "source": "LinkedIn"
            })
            
        logger.info(f"Found {len(jobs)} jobs from LinkedIn.")
        return jobs
    except Exception as e:
        logger.error(f"Error scraping LinkedIn: {e}")
        # Return fallback dummy data for testing the agent workflow
        logger.info("Returning dummy job data for testing...")
        return [
            {
                "title": f"Lead {keyword} Developer",
                "company": "Global Corp LLC",
                "link": "https://example.com/job/2",
                "description": f"Global Corp is looking for a {keyword} expert. Requirements: 5+ years experience, solid understanding of modern architectures and AI.",
                "source": "Dummy LinkedIn"
            }
        ]

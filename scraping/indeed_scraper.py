import requests
from bs4 import BeautifulSoup
import logging
import time
from urllib.parse import quote_plus
from config import SCRAPE_LIMIT, SCRAPE_RETRIES

logger = logging.getLogger(__name__)

DUMMY_JOBS = [
    {
        "title": "Senior AI Engineer",
        "company": "Tech Innovators Inc",
        "link": "https://example.com/job/1",
        "description": "We are looking for a highly skilled AI Engineer to join our fast-paced startup. Must have experience with Python, LLMs, and MLOps.",
        "source": "Dummy Indeed"
    },
    {
        "title": "Machine Learning Engineer",
        "company": "DataVision AI",
        "link": "https://example.com/job/2",
        "description": "DataVision AI seeks a Machine Learning Engineer with strong Python, TensorFlow/PyTorch, and cloud deployment (AWS/GCP) experience.",
        "source": "Dummy Indeed"
    },
    {
        "title": "AI Research Engineer",
        "company": "NeuralCore Labs",
        "link": "https://example.com/job/3",
        "description": "Exciting opportunity to work on cutting-edge NLP and LLM research. Requires deep learning expertise and publication record.",
        "source": "Dummy Indeed"
    },
]


def search_indeed_jobs(keyword: str, location: str = "", limit: int = SCRAPE_LIMIT):
    """
    Scrape job listings from Indeed with retry/back-off.
    Falls back to rich dummy data if scraping fails (Indeed has strict anti-bot measures).
    """
    logger.info(f"Searching Indeed for '{keyword}' jobs in '{location}'...")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    url = f"https://www.indeed.com/jobs?q={quote_plus(keyword)}&l={quote_plus(location)}"

    for attempt in range(1, SCRAPE_RETRIES + 1):
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")
            job_cards = soup.select(".job_seen_beacon")

            if not job_cards:
                raise ValueError("No job cards found – page structure may have changed")

            jobs = []
            for job_card in job_cards[:limit]:
                try:
                    title_elem = job_card.select_one("h2")
                    title = title_elem.text.strip() if title_elem else "Unknown Title"

                    link_elem = job_card.select_one("a")
                    link = (
                        f"https://www.indeed.com{link_elem['href']}"
                        if link_elem and link_elem.has_attr("href")
                        else url
                    )

                    company_elem = job_card.select_one('[data-testid="company-name"]')
                    company = company_elem.text.strip() if company_elem else "Unknown Company"

                    description_elem = job_card.select_one(".job-snippet")
                    description = description_elem.text.strip() if description_elem else ""

                    jobs.append({
                        "title": title,
                        "company": company,
                        "link": link,
                        "description": description,
                        "source": "Indeed",
                    })
                except Exception as e:
                    logger.debug(f"Error parsing Indeed job card: {e}")
                    continue

            logger.info(f"Found {len(jobs)} jobs from Indeed.")
            return jobs

        except Exception as e:
            wait = 2 ** attempt
            logger.warning(f"Indeed attempt {attempt}/{SCRAPE_RETRIES} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)

    logger.error("All Indeed attempts failed. Returning dummy job data.")
    return DUMMY_JOBS

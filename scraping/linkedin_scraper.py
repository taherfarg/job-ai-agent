import requests
from bs4 import BeautifulSoup
import logging
import time
from urllib.parse import quote_plus
from config import SCRAPE_LIMIT, SCRAPE_RETRIES

logger = logging.getLogger(__name__)

DUMMY_JOBS = [
    {
        "title": "AI/ML Engineer",
        "company": "Sectech Solutions",
        "link": "https://www.linkedin.com/jobs/view/ai-ml-engineer-at-sectech-solutions-4382452328",
        "description": "Seeking an AI/ML Engineer proficient in Python, PyTorch, and cloud ML platforms. Experience with LLMOps and MLflow preferred.",
        "source": "LinkedIn",
    },
    {
        "title": "AI Engineer (Python, Gen AI)",
        "company": "DHL",
        "link": "https://my.linkedin.com/jobs/view/ai-engineer-python-gen-ai-at-dhl-4372372365",
        "description": "DHL is hiring an AI Engineer with GenAI experience (LangChain, OpenAI API). Responsible for building intelligent automation pipelines.",
        "source": "LinkedIn",
    },
    {
        "title": "Artificial Intelligence Engineer",
        "company": "Deloitte",
        "link": "https://uk.linkedin.com/jobs/view/artificial-intelligence-engineer-at-deloitte-4362274740",
        "description": "Deloitte seeks AI Engineers to design and deploy ML solutions for enterprise clients. Python, TensorFlow, and cloud experience required.",
        "source": "LinkedIn",
    },
    {
        "title": "Python AI/ML Developer",
        "company": "Infosys",
        "link": "https://in.linkedin.com/jobs/view/python-ai-ml-developer-at-infosys-4374018219",
        "description": "Infosys looking for AI/ML Developer with strong Python background, experience in NLP, computer vision, and REST API development.",
        "source": "LinkedIn",
    },
    {
        "title": "AI / ML Engineer",
        "company": "MokshaaLLC",
        "link": "https://www.linkedin.com/jobs/view/ai-ml-engineer-at-mokshaallc-4382454904",
        "description": "Remote position for AI/ML Engineer with 3+ years of experience. Must have expertise in Python, Scikit-learn, and model deployment.",
        "source": "LinkedIn",
    },
]


def search_linkedin_jobs(keyword: str, location: str = "Remote", limit: int = SCRAPE_LIMIT):
    """
    Search LinkedIn Jobs with retry/back-off.
    Falls back to rich dummy data if scraping is blocked.
    """
    logger.info(f"Searching LinkedIn for '{keyword}' jobs in '{location}'...")

    url = (
        f"https://www.linkedin.com/jobs/search"
        f"?keywords={quote_plus(keyword)}&location={quote_plus(location)}&f_WT=2"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    for attempt in range(1, SCRAPE_RETRIES + 1):
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")
            job_cards = soup.find_all("div", class_="base-card")

            if not job_cards:
                raise ValueError("No job cards found – LinkedIn may have changed layout or blocked request")

            seen_links = set()
            jobs = []
            for card in job_cards[:limit]:
                try:
                    title_elem = card.find("h3", class_="base-search-card__title")
                    title = title_elem.text.strip() if title_elem else "Unknown"

                    company_elem = card.find("h4", class_="base-search-card__subtitle")
                    company = company_elem.text.strip() if company_elem else "Unknown"

                    link_elem = card.find("a", class_="base-card__full-link")
                    link = link_elem["href"].split("?")[0] if link_elem else url

                    # Deduplicate by link
                    if link in seen_links:
                        continue
                    seen_links.add(link)

                    jobs.append({
                        "title": title,
                        "company": company,
                        "link": link,
                        "description": f"LinkedIn job: {title} at {company}. See link for full description.",
                        "source": "LinkedIn",
                    })
                except Exception as e:
                    logger.debug(f"Error parsing LinkedIn job card: {e}")
                    continue

            logger.info(f"Found {len(jobs)} jobs from LinkedIn.")
            return jobs

        except Exception as e:
            wait = 2 ** attempt
            logger.warning(f"LinkedIn attempt {attempt}/{SCRAPE_RETRIES} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)

    logger.error("All LinkedIn attempts failed. Returning dummy job data.")
    return DUMMY_JOBS

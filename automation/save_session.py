import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from config import DATA_DIR
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SESSION_FILE = DATA_DIR / "linkedin_session.json"

def login_and_save_session():
    print("="*60)
    print("Opening browser. Please log in to LinkedIn manually.")
    print("Once you are fully logged in and see the feed, close the browser window.")
    print("="*60)
    
    with sync_playwright() as p:
        # Launch headed browser so you can interact
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto("https://www.linkedin.com/login")
        
        # Wait until the user closes the page manually
        try:
            page.wait_for_event("close", timeout=0)
        except Exception as e:
            logger.info("Browser closed by user.")
        
        # Save the authenticated state (cookies, localStorage, session storage)
        context.storage_state(path=SESSION_FILE)
        logger.info(f"Session successfully saved to {SESSION_FILE}!")
        
        browser.close()

if __name__ == "__main__":
    login_and_save_session()

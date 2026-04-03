"""
save_session.py
───────────────
Utility script to manually log into job portals and securely save the session cookies/state.
You must run this manually in headed mode whenever your session expires.
"""

import os
import sys

# Ensure project root is in PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from config import DATA_DIR
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def _get_browser_executable():
    paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/brave-browser",
        "/usr/bin/microsoft-edge-stable"
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

SITES = {
    "1": ("linkedin", "https://www.linkedin.com/login"),
    "2": ("indeed", "https://secure.indeed.com/auth"),
    "3": ("naukrigulf", "https://www.naukrigulf.com/login"),
    "4": ("bayt", "https://www.bayt.com/en/login/"),
    "5": ("gulftalent", "https://www.gulftalent.com/login"),
    "6": ("glassdoor", "https://www.glassdoor.com/profile/login_input.htm"),
}

def login_and_save_session():
    print("\n" + "=" * 60)
    print(" Job Portal Authentication Setup ")
    print("=" * 60)
    print("Which platform do you want to authenticate with?")
    for key, (name, _) in SITES.items():
        print(f"  [{key}] {name.capitalize()}")
    
    choice = input("\nEnter number (1-6): ").strip()
    
    if choice not in SITES:
        print("Invalid choice. Exiting.")
        sys.exit(1)
        
    site_name, login_url = SITES[choice]
    session_file = DATA_DIR / f"{site_name}_session.json"
    
    print("\n" + "=" * 60)
    print(f"Opening browser for {site_name.upper()}.")
    print("Please physically log in using your credentials.")
    print("Once you are fully logged in and see the dashboard/feed,")
    print("SIMPLY CLOSE THE BROWSER WINDOW to securely save your session.")
    print("=" * 60)
    
    with sync_playwright() as p:
        # Launch headed browser so the user can interact
        # Use native browser executable to easily bypass Cloudflare
        exec_path = _get_browser_executable()
        launch_kwargs = {
            "headless": False,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
        }
        if exec_path:
            launch_kwargs["executable_path"] = exec_path
            
        browser = p.chromium.launch(**launch_kwargs)
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        # Apply stealth mode immediately to bypass Cloudflare and Turnstile
        Stealth().apply_stealth_sync(page)
        
        try:
            page.goto(login_url)
            
            # Wait endlessly until the user manually closes the page or browser
            page.wait_for_event("close", timeout=0)
            
        except Exception as e:
            if "Browser closed" in str(e):
                logger.info(f"Browser manually closed by user. Proceeding to save...")
            else:
                logger.info(f"Page closed. (Reason: {e})")
        
        # At this point, the browser was closed. We extract the state from the context.
        # Ensure DATA_DIR exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        context.storage_state(path=str(session_file))
        logger.info(f"✅ Session successfully saved to {session_file}!")
        
        browser.close()

if __name__ == "__main__":
    login_and_save_session()

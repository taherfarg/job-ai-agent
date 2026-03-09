import logging
from playwright.sync_api import sync_playwright

from config import DATA_DIR

logger = logging.getLogger(__name__)
SESSION_FILE = DATA_DIR / "linkedin_session.json"

def apply_to_job(url: str, cv_path: str) -> bool:
    """
    Attempts to autonomously apply for the job via Playwright.
    """
    logger.info(f"Navigating to {url} to apply...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            # Inject Authenticated Session if it exists
            if SESSION_FILE.exists():
                logger.info("Found saved session. Injecting authenticated cookies...")
                context = browser.new_context(storage_state=SESSION_FILE)
            else:
                logger.warning("No session file found. Operating as unauthenticated guest.")
                context = browser.new_context()
                
            page = context.new_page()
            
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # LinkedIn Easy Apply Heuristics
            try:
                page.wait_for_timeout(3000) # Give page time to load cleanly
                logger.info("Looking for 'Easy Apply' button...")

                easy_apply_buttons = page.locator("button:has-text('Easy Apply'), button.jobs-apply-button--top-card")
                if easy_apply_buttons.count() == 0:
                    logger.warning("No 'Easy Apply' button found. It might be a regular 'Apply' (external) or already applied.")
                    browser.close()
                    return False
                
                # Click the first matching Apply button
                easy_apply_buttons.first.click(timeout=5000)
                logger.info("Clicked 'Easy Apply'. Waiting for modal...")
                page.wait_for_selector(".jobs-easy-apply-modal", timeout=5000)

                # Modal navigation loop
                logger.info("Modal opened. Attempting to step through the form...")
                max_steps = 10
                for step in range(max_steps):
                    page.wait_for_timeout(1500) # UI rendering buffer
                    
                    # Fill visible required fields dynamically (rough heuristic)
                    if page.locator("input[type='text'], input[type='email'], input[type='tel']").count() > 0:
                        inputs = page.locator("input[type='text'], input[type='email'], input[type='tel']").all()
                        for input_field in inputs:
                            if input_field.is_visible() and input_field.is_editable():
                                try:
                                    # Fallback values if empty
                                    input_val = input_field.input_value()
                                    if not input_val:
                                        name = input_field.get_attribute("name") or ""
                                        if "email" in name.lower():
                                            input_field.fill("taherfarg50@gmail.com")
                                        elif "phone" in name.lower() or "tel" in name.lower():
                                            input_field.fill("+971547224740")
                                except:
                                    pass
                    
                    # Look for Next, Review, or Submit
                    submit_btn = page.locator("button:has-text('Submit application')")
                    review_btn = page.locator("button:has-text('Review')")
                    next_btn = page.locator("button:has-text('Next')")

                    if submit_btn.is_visible():
                        logger.info("Found 'Submit application' button. Clicking!")
                        submit_btn.click(timeout=3000)
                        page.wait_for_timeout(3000)
                        browser.close()
                        return True
                    elif review_btn.is_visible():
                        logger.info("Found 'Review' button. Clicking!")
                        review_btn.click(timeout=3000)
                    elif next_btn.is_visible():
                        logger.info("Found 'Next' button. Clicking!")
                        next_btn.click(timeout=3000)
                    else:
                        logger.warning("No progression buttons found. Form might be stuck or requires complex inputs.")
                        break

                logger.warning("Reached max steps or got stuck in the modal.")
                browser.close()
                return False

            except Exception as e:
                logger.warning(f"Easy Apply flow fell through: {e}")
                browser.close()
                return False
    except Exception as e:
        logger.error(f"Browser automation failed for {url}: {e}")
        return False

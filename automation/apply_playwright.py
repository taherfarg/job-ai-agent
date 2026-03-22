"""
apply_playwright.py
───────────────────
Multi-platform Playwright automation for job applications.
Supports LinkedIn Easy Apply, Indeed, Glassdoor, GulfTalent, Bayt, NaukriGulf,
and a generic fallback flow for any other site.
"""

import logging
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

from config import DATA_DIR, APPLICANT_EMAIL, APPLICANT_PHONE, CV_PATH

logger = logging.getLogger(__name__)
SESSION_FILE = DATA_DIR / "linkedin_session.json"



# ── Site Detection ──────────────────────────────────────────────────────────

def _detect_site(url: str) -> str:
    """Detect which job platform the URL belongs to."""
    domain = urlparse(url).netloc.lower()
    if "linkedin" in domain:
        return "linkedin"
    elif "indeed" in domain:
        return "indeed"
    elif "glassdoor" in domain:
        return "glassdoor"
    elif "gulftalent" in domain:
        return "gulftalent"
    elif "bayt" in domain:
        return "bayt"
    elif "naukrigulf" in domain:
        return "naukrigulf"
    else:
        return "generic"


# ── Apply Dispatcher ────────────────────────────────────────────────────────

def apply_to_job(url: str, cv_path: str = str(CV_PATH)) -> bool:
    """
    Attempts to autonomously apply for the job via Playwright.
    Routes to the appropriate site-specific flow.
    """
    site = _detect_site(url)
    logger.info(f"[{site.upper()}] Navigating to {url} to apply...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=500)

            # Use saved LinkedIn session if available
            if site == "linkedin" and SESSION_FILE.exists():
                logger.info("Found saved LinkedIn session. Injecting authenticated cookies...")
                context = browser.new_context(
                    storage_state=SESSION_FILE,
                )
            else:
                context = browser.new_context()

            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)

            # Route to the correct apply flow
            if site == "linkedin":
                result = _apply_linkedin(page, cv_path)
            elif site == "indeed":
                result = _apply_indeed(page, cv_path)
            elif site == "glassdoor":
                result = _apply_glassdoor(page, cv_path)
            elif site in ("gulftalent", "bayt", "naukrigulf"):
                result = _apply_gulf_site(page, cv_path, site)
            else:
                result = _apply_generic(page, cv_path)

            browser.close()
            return result

    except Exception as e:
        logger.error(f"Browser automation failed for {url}: {e}")
        return False


# ── LinkedIn Easy Apply Flow ───────────────────────────────────────────────

def _apply_linkedin(page, cv_path: str) -> bool:
    """Handle LinkedIn Easy Apply modal flow."""
    try:
        logger.info("Looking for 'Easy Apply' button...")
        easy_apply = page.locator(
            "button:has-text('Easy Apply'), button.jobs-apply-button--top-card"
        )
        if easy_apply.count() == 0:
            logger.warning("No 'Easy Apply' button found.")
            return False

        easy_apply.first.click(timeout=5000)
        logger.info("Clicked 'Easy Apply'. Waiting for modal...")
        page.wait_for_selector(".jobs-easy-apply-modal", timeout=5000)

        return _step_through_modal(page, max_steps=10)

    except Exception as e:
        logger.warning(f"LinkedIn Easy Apply flow failed: {e}")
        return False


# ── Indeed Apply Flow ──────────────────────────────────────────────────────

def _apply_indeed(page, cv_path: str) -> bool:
    """Handle Indeed's application flow."""
    try:
        logger.info("Looking for Indeed 'Apply now' button...")
        apply_btn = page.locator(
            "button:has-text('Apply now'), "
            "a:has-text('Apply now'), "
            "button:has-text('Apply on company site'), "
            "a:has-text('Apply on company site')"
        )

        if apply_btn.count() == 0:
            logger.warning("No Indeed apply button found.")
            return False

        apply_btn.first.click(timeout=5000)
        page.wait_for_timeout(3000)

        # If redirected to external site, try generic flow
        if "indeed.com" not in page.url:
            logger.info("Redirected to external application site.")
            return _apply_generic(page, cv_path)

        # Fill form fields and upload CV
        _fill_common_fields(page)
        _try_upload_cv(page, cv_path)

        return _click_submit(page)

    except Exception as e:
        logger.warning(f"Indeed apply flow failed: {e}")
        return False


# ── Glassdoor Apply Flow ──────────────────────────────────────────────────

def _apply_glassdoor(page, cv_path: str) -> bool:
    """Handle Glassdoor's application flow."""
    try:
        logger.info("Looking for Glassdoor apply button...")
        apply_btn = page.locator(
            "button:has-text('Apply'), "
            "a:has-text('Apply'), "
            "button:has-text('Easy Apply'), "
            "[data-test='applyButton']"
        )

        if apply_btn.count() == 0:
            logger.warning("No Glassdoor apply button found.")
            return False

        apply_btn.first.click(timeout=5000)
        page.wait_for_timeout(3000)

        # Glassdoor may redirect to company site
        if "glassdoor.com" not in page.url:
            logger.info("Redirected to company application page.")
            return _apply_generic(page, cv_path)

        _fill_common_fields(page)
        _try_upload_cv(page, cv_path)

        return _click_submit(page)

    except Exception as e:
        logger.warning(f"Glassdoor apply flow failed: {e}")
        return False


# ── Gulf Sites (GulfTalent / Bayt / NaukriGulf) ───────────────────────────

def _apply_gulf_site(page, cv_path: str, site: str) -> bool:
    """Handle GulfTalent, Bayt, and NaukriGulf application flows."""
    try:
        logger.info(f"Looking for {site} apply button...")
        apply_btn = page.locator(
            "button:has-text('Apply'), "
            "a:has-text('Apply'), "
            "button:has-text('Apply Now'), "
            "a:has-text('Apply Now'), "
            "button:has-text('Quick Apply'), "
            "a:has-text('Quick Apply'), "
            "[class*='apply'] button, "
            "[class*='apply'] a"
        )

        if apply_btn.count() == 0:
            logger.warning(f"No {site} apply button found.")
            return False

        apply_btn.first.click(timeout=5000)
        page.wait_for_timeout(3000)

        _fill_common_fields(page)
        _try_upload_cv(page, cv_path)

        return _click_submit(page)

    except Exception as e:
        logger.warning(f"{site} apply flow failed: {e}")
        return False


# ── Generic Apply Flow (any site) ─────────────────────────────────────────

def _apply_generic(page, cv_path: str) -> bool:
    """Generic apply flow that tries to find and click apply buttons on any site."""
    try:
        logger.info("Attempting generic application flow...")

        # Try common apply button patterns
        apply_btn = page.locator(
            "button:has-text('Apply'), "
            "a:has-text('Apply'), "
            "button:has-text('Submit Application'), "
            "a:has-text('Submit Application'), "
            "button:has-text('Apply Now'), "
            "a:has-text('Apply Now'), "
            "input[type='submit'][value*='Apply' i]"
        )

        if apply_btn.count() > 0:
            apply_btn.first.click(timeout=5000)
            page.wait_for_timeout(3000)

        _fill_common_fields(page)
        _try_upload_cv(page, cv_path)

        return _click_submit(page)

    except Exception as e:
        logger.warning(f"Generic apply flow failed: {e}")
        return False


# ── Shared Helpers ─────────────────────────────────────────────────────────

def _fill_common_fields(page):
    """Fill standard form fields (name, email, phone) using heuristics."""
    inputs = page.locator(
        "input[type='text'], input[type='email'], input[type='tel'], "
        "input[type='number'], textarea"
    ).all()

    for field in inputs:
        try:
            if not field.is_visible() or not field.is_editable():
                continue

            current_val = field.input_value()
            if current_val:
                continue

            name = (field.get_attribute("name") or "").lower()
            placeholder = (field.get_attribute("placeholder") or "").lower()
            label_id = field.get_attribute("id") or ""
            aria_label = (field.get_attribute("aria-label") or "").lower()
            all_attrs = f"{name} {placeholder} {label_id} {aria_label}"

            if any(kw in all_attrs for kw in ["email", "e-mail"]):
                field.fill(APPLICANT_EMAIL)
                logger.debug(f"Filled email: {APPLICANT_EMAIL}")
            elif any(kw in all_attrs for kw in ["phone", "tel", "mobile", "contact"]):
                field.fill(APPLICANT_PHONE)
                logger.debug(f"Filled phone: {APPLICANT_PHONE}")
            elif any(kw in all_attrs for kw in ["first", "fname"]):
                field.fill("Taher")
            elif any(kw in all_attrs for kw in ["last", "lname", "surname"]):
                field.fill("Farg")
            elif any(kw in all_attrs for kw in ["full", "name"]):
                field.fill("Taher Farg")

        except Exception:
            pass


def _try_upload_cv(page, cv_path: str):
    """Try to upload CV to any visible file input."""
    try:
        file_inputs = page.locator("input[type='file']").all()
        for file_input in file_inputs:
            try:
                file_input.set_input_files(cv_path)
                logger.info(f"Uploaded CV: {cv_path}")
                break
            except Exception:
                continue
    except Exception:
        logger.debug("No file upload inputs found or upload failed.")


def _click_submit(page) -> bool:
    """Try to find and click the submit/apply button."""
    submit_btn = page.locator(
        "button:has-text('Submit'), "
        "button:has-text('Submit Application'), "
        "button:has-text('Apply'), "
        "button:has-text('Send Application'), "
        "button:has-text('Confirm'), "
        "input[type='submit']"
    )

    if submit_btn.count() > 0:
        submit_btn.first.click(timeout=5000)
        page.wait_for_timeout(3000)
        logger.info("Clicked submit button.")
        return True

    logger.warning("No submit button found.")
    return False


def _step_through_modal(page, max_steps: int = 10) -> bool:
    """Step through a multi-step modal (LinkedIn Easy Apply style)."""
    logger.info("Stepping through application modal...")

    for step in range(max_steps):
        page.wait_for_timeout(1500)

        # Fill visible required fields
        _fill_common_fields(page)

        # Look for progression buttons
        submit_btn = page.locator("button:has-text('Submit application')")
        review_btn = page.locator("button:has-text('Review')")
        next_btn = page.locator("button:has-text('Next')")

        if submit_btn.is_visible():
            logger.info("Found 'Submit application' button. Clicking!")
            submit_btn.click(timeout=3000)
            page.wait_for_timeout(3000)
            return True
        elif review_btn.is_visible():
            logger.info("Found 'Review' button. Clicking!")
            review_btn.click(timeout=3000)
        elif next_btn.is_visible():
            logger.info("Found 'Next' button. Clicking!")
            next_btn.click(timeout=3000)
        else:
            logger.warning("No progression buttons found. Form might need complex inputs.")
            break

    logger.warning("Reached max steps or got stuck in modal.")
    return False

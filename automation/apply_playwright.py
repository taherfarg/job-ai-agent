"""
apply_playwright.py
───────────────────
Multi-platform Playwright automation for job applications.
Supports LinkedIn Easy Apply, Indeed, Glassdoor, GulfTalent, Bayt, NaukriGulf,
and a generic fallback flow for any other site.

v2 — Enhanced with:
  • Dynamic waits (networkidle) instead of fixed sleep
  • Much broader CSS/XPath selectors
  • Detailed tracing & reason logging for failures
  • Video recording of each application session
"""

import logging
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

from config import DATA_DIR, APPLICANT_EMAIL, APPLICANT_PHONE, CV_PATH

logger = logging.getLogger(__name__)
RECORDINGS_DIR = DATA_DIR / "recordings"
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)



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
    Records a video of each application attempt.
    """
    site = _detect_site(url)
    logger.info(f"[{site.upper()}] Navigating to {url} to apply...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=400)

            # Use saved session for the current site if available
            session_file = DATA_DIR / f"{site}_session.json"
            if session_file.exists():
                logger.info(f"Injecting saved {site.upper()} session cookies...")
                context = browser.new_context(
                    storage_state=str(session_file),
                    record_video_dir=str(RECORDINGS_DIR),
                    record_video_size={"width": 1280, "height": 720},
                )
            else:
                logger.info(f"No saved session found for {site.upper()} (checked {session_file.name}). Proceeding as guest.")
                context = browser.new_context(
                    record_video_dir=str(RECORDINGS_DIR),
                    record_video_size={"width": 1280, "height": 720},
                )

            page = context.new_page()

            # Navigate with longer timeout for slow sites
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except Exception as nav_err:
                logger.error(f"[{site.upper()}] Page failed to load: {nav_err}")
                browser.close()
                return False

            # Dynamic wait — wait for network to settle instead of fixed sleep
            _smart_wait(page)

            # Check if the page actually loaded a job (not a 404/error page)
            if _is_error_page(page):
                logger.warning(f"[{site.upper()}] Page appears to be an error/404 page. Skipping.")
                browser.close()
                return False

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

            if result:
                logger.info(f"[{site.upper()}] ✅ Application submitted successfully!")
            else:
                logger.warning(f"[{site.upper()}] ❌ Application could not be completed.")

            # Close context first so video is saved properly
            context.close()
            browser.close()
            return result

    except Exception as e:
        logger.error(f"Browser automation failed for {url}: {e}")
        return False


# ── Smart Helpers ──────────────────────────────────────────────────────────

def _smart_wait(page, timeout: int = 10000):
    """Wait for the network to settle, with a maximum timeout."""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        # Fallback to a short fixed wait if networkidle times out
        page.wait_for_timeout(3000)


def _dismiss_overlays(page):
    """
    Remove sticky headers, cookie banners, and overlay elements that
    intercept pointer events and block button clicks.
    """
    try:
        page.evaluate("""
            // Remove fixed/sticky elements that block clicks
            const selectors = [
                '[class*="gnav"]',       // Indeed sticky nav
                '[class*="cookie"]',     // Cookie banners
                '[class*="banner"]',     // Promotional banners
                '[class*="overlay"]',    // Generic overlays
                '[class*="popup"]',      // Popups
                '[class*="modal-backdrop"]',
                '[id*="onetrust"]',      // OneTrust cookie consent
            ];
            for (const sel of selectors) {
                document.querySelectorAll(sel).forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' || style.position === 'sticky') {
                        el.style.display = 'none';
                    }
                });
            }
            // Also hide any element with position:fixed that's at the top
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                if ((style.position === 'fixed' || style.position === 'sticky') &&
                    parseInt(style.top) <= 60 && el.offsetHeight < 200) {
                    el.style.display = 'none';
                }
            });
        """)
        logger.debug("  ↳ Dismissed overlay/sticky elements.")
    except Exception:
        pass


def _is_error_page(page) -> bool:
    """Check if the loaded page is a 404, expired job, or error page."""
    title = page.title().lower()
    content = page.text_content("body")[:500].lower() if page.query_selector("body") else ""

    error_signals = [
        "404", "not found", "page not found", "no longer available",
        "job has expired", "this job is no longer", "error",
        "access denied", "forbidden",
    ]

    for signal in error_signals:
        if signal in title or signal in content:
            logger.info(f"  ↳ Error signal detected: '{signal}'")
            return True

    return False


# ── LinkedIn Easy Apply Flow ───────────────────────────────────────────────

def _apply_linkedin(page, cv_path: str) -> bool:
    """Handle LinkedIn Easy Apply modal flow."""
    try:
        logger.info("Looking for 'Easy Apply' button...")

        # Broad set of selectors for LinkedIn's Easy Apply button
        easy_apply = page.locator(
            "button:has-text('Easy Apply'), "
            "button.jobs-apply-button--top-card, "
            "button.jobs-apply-button, "
            "button[aria-label*='Easy Apply'], "
            "button[class*='apply'], "
            "div.jobs-apply-button--top-card button"
        )

        if easy_apply.count() == 0:
            # Check if it's an external apply (redirect to company site)
            external = page.locator(
                "button:has-text('Apply'), "
                "a:has-text('Apply on company website'), "
                "a:has-text('Apply')"
            )
            if external.count() > 0:
                logger.info("This is an external application (not Easy Apply). Clicking through...")
                external.first.click(timeout=5000)
                _smart_wait(page)
                return _apply_generic(page, cv_path)

            logger.warning("No 'Easy Apply' or 'Apply' button found on LinkedIn.")
            logger.info("  ↳ Possible reasons: job expired, login required, or not an Easy Apply job.")
            return False

        easy_apply.first.click(timeout=5000)
        logger.info("Clicked 'Easy Apply'. Waiting for modal...")

        try:
            page.wait_for_selector(
                ".jobs-easy-apply-modal, "
                "[class*='easy-apply'], "
                "div[role='dialog']",
                timeout=8000,
            )
        except Exception:
            logger.warning("Easy Apply modal did not appear.")
            return False

        return _step_through_modal(page, max_steps=12)

    except Exception as e:
        logger.warning(f"LinkedIn Easy Apply flow failed: {e}")
        return False


# ── Indeed Apply Flow ──────────────────────────────────────────────────────

def _apply_indeed(page, cv_path: str) -> bool:
    """Handle Indeed's application flow."""
    try:
        # Dismiss overlays that block clicks (Indeed's sticky nav bar)
        _dismiss_overlays(page)

        logger.info("Looking for Indeed apply button...")
        apply_btn = page.locator(
            "button:has-text('Apply now'), "
            "a:has-text('Apply now'), "
            "button:has-text('Apply on company site'), "
            "a:has-text('Apply on company site'), "
            "button[id*='apply'], "
            "a[id*='apply'], "
            "button[class*='apply'], "
            "a[class*='apply']"
        )

        if apply_btn.count() == 0:
            logger.warning("No Indeed apply button found.")
            logger.info("  ↳ Possible reasons: job expired, requires Indeed login, or external redirect.")
            return False

        apply_btn.first.click(timeout=5000)
        _smart_wait(page)

        # Dismiss overlays again after new page load
        _dismiss_overlays(page)

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
            "[data-test='applyButton'], "
            "button[class*='apply'], "
            "a[class*='apply']"
        )

        if apply_btn.count() == 0:
            logger.warning("No Glassdoor apply button found.")
            logger.info("  ↳ Possible reasons: requires Glassdoor login or job has expired.")
            return False

        apply_btn.first.click(timeout=5000)
        _smart_wait(page)

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
            "button:has-text('Easy Apply'), "
            "a:has-text('Easy Apply'), "
            "[class*='apply'] button, "
            "[class*='apply'] a, "
            "button[class*='apply'], "
            "a[class*='apply'], "
            "input[type='submit'][value*='Apply' i]"
        )

        if apply_btn.count() == 0:
            logger.warning(f"No {site} apply button found.")
            logger.info(f"  ↳ Possible reasons: requires {site} login, job expired, or page structure changed.")
            return False

        apply_btn.first.click(timeout=5000)
        _smart_wait(page)

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

        # Try common apply button patterns (very broad)
        apply_btn = page.locator(
            "button:has-text('Apply'), "
            "a:has-text('Apply'), "
            "button:has-text('Submit Application'), "
            "a:has-text('Submit Application'), "
            "button:has-text('Apply Now'), "
            "a:has-text('Apply Now'), "
            "button:has-text('Submit'), "
            "input[type='submit'][value*='Apply' i], "
            "input[type='submit'][value*='Submit' i], "
            "button[class*='apply'], "
            "a[class*='apply']"
        )

        if apply_btn.count() > 0:
            apply_btn.first.click(timeout=5000)
            _smart_wait(page)
        else:
            logger.info("  ↳ No apply button found on the generic page.")

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

    filled_count = 0
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
            field_type = (field.get_attribute("type") or "").lower()
            all_attrs = f"{name} {placeholder} {label_id} {aria_label}"

            if field_type == "email" or any(kw in all_attrs for kw in ["email", "e-mail"]):
                field.fill(APPLICANT_EMAIL)
                logger.debug(f"  ↳ Filled email field")
                filled_count += 1
            elif field_type == "tel" or any(kw in all_attrs for kw in ["phone", "tel", "mobile", "contact"]):
                field.fill(APPLICANT_PHONE)
                logger.debug(f"  ↳ Filled phone field")
                filled_count += 1
            elif any(kw in all_attrs for kw in ["first", "fname"]):
                field.fill("Taher")
                filled_count += 1
            elif any(kw in all_attrs for kw in ["last", "lname", "surname"]):
                field.fill("Farg")
                filled_count += 1
            elif any(kw in all_attrs for kw in ["full", "name"]):
                field.fill("Taher Farg")
                filled_count += 1

        except Exception:
            pass

    if filled_count > 0:
        logger.info(f"  ↳ Auto-filled {filled_count} form fields.")


def _try_upload_cv(page, cv_path: str):
    """Try to upload CV to any visible file input."""
    try:
        file_inputs = page.locator("input[type='file']").all()
        for file_input in file_inputs:
            try:
                file_input.set_input_files(cv_path)
                logger.info(f"  ↳ Uploaded CV: {cv_path}")
                break
            except Exception:
                continue
    except Exception:
        logger.debug("  ↳ No file upload inputs found or upload failed.")


def _click_submit(page) -> bool:
    """Try to find and click the submit/apply button."""
    # Dismiss any overlays that might block the button
    _dismiss_overlays(page)

    submit_btn = page.locator(
        "button:has-text('Submit'), "
        "button:has-text('Submit Application'), "
        "button:has-text('Apply'), "
        "button:has-text('Send Application'), "
        "button:has-text('Confirm'), "
        "button:has-text('Submit application'), "
        "button:has-text('Complete Application'), "
        "input[type='submit'], "
        "button[type='submit']"
    )

    if submit_btn.count() > 0:
        try:
            submit_btn.first.scroll_into_view_if_needed()
            submit_btn.first.click(timeout=5000)
        except Exception:
            # Force click as last resort if overlay still blocks
            logger.info("  ↳ Normal click blocked. Trying force click...")
            try:
                submit_btn.first.click(force=True, timeout=5000)
            except Exception as e:
                logger.warning(f"  ↳ Force click also failed: {e}")
                return False
        _smart_wait(page, timeout=5000)
        logger.info("  ↳ Clicked submit button.")
        return True

    logger.warning("  ↳ No submit button found. Application may require manual completion.")
    return False


def _step_through_modal(page, max_steps: int = 12) -> bool:
    """Step through a multi-step modal (LinkedIn Easy Apply style)."""
    logger.info("Stepping through application modal...")

    for step in range(max_steps):
        _smart_wait(page, timeout=3000)

        # Fill visible required fields
        _fill_common_fields(page)

        # Try to upload CV if a file input appears
        _try_upload_cv(page, str(CV_PATH))

        # Look for progression buttons (order matters: submit > review > next)
        submit_btn = page.locator(
            "button:has-text('Submit application'), "
            "button:has-text('Submit'), "
            "button[aria-label*='Submit']"
        )
        review_btn = page.locator(
            "button:has-text('Review'), "
            "button[aria-label*='Review']"
        )
        next_btn = page.locator(
            "button:has-text('Next'), "
            "button:has-text('Continue'), "
            "button[aria-label*='Next'], "
            "button[aria-label*='Continue']"
        )

        if submit_btn.count() > 0 and submit_btn.first.is_visible():
            logger.info(f"  ↳ Step {step + 1}: Found 'Submit' button. Clicking!")
            submit_btn.first.click(timeout=3000)
            _smart_wait(page, timeout=5000)
            return True
        elif review_btn.count() > 0 and review_btn.first.is_visible():
            logger.info(f"  ↳ Step {step + 1}: Found 'Review' button. Clicking!")
            review_btn.first.click(timeout=3000)
        elif next_btn.count() > 0 and next_btn.first.is_visible():
            logger.info(f"  ↳ Step {step + 1}: Found 'Next' button. Clicking!")
            next_btn.first.click(timeout=3000)
        else:
            logger.warning(f"  ↳ Step {step + 1}: No progression buttons. Form may need complex/manual inputs.")
            break

    logger.warning("  ↳ Reached max steps or got stuck in modal.")
    return False

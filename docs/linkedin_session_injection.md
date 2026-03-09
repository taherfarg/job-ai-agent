# LinkedIn Session Injection Guide

To bypass LinkedIn's strict login walls, we will use "Session Saving" in Playwright. Instead of logging in programmatically (which triggers CAPTCHAs), we will open a headed browser once, log in manually, save that authenticated session to a file, and then load that file for all future automated runs.

## Step 1: Create a Session Saver Helper Script

We need a separate script that simply opens LinkedIn and waits for you to log in, then saves the cookies and local storage to a file called `linkedin_session.json`.

Save the following code as `automation/save_session.py`:

```python
import os
from playwright.sync_api import sync_playwright
from config import DATA_DIR

SESSION_FILE = os.path.join(DATA_DIR, "linkedin_session.json")

def login_and_save_session():
    print("Opening browser. Please log in to LinkedIn manually.")
    print("Once you are fully logged in and see the feed, close the browser window.")
    
    with sync_playwright() as p:
        # Launch headed browser so you can interact
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto("https://www.linkedin.com/login")
        
        # Wait until the user closes the page manually
        page.wait_for_event("close", timeout=0)
        
        # Save the authenticated state (cookies, localStorage, session storage)
        context.storage_state(path=SESSION_FILE)
        print(f"Session successfully saved to {SESSION_FILE}!")
        
        browser.close()

if __name__ == "__main__":
    login_and_save_session()
```

## Step 2: Run the Helper Script

1. Open your terminal in the virtual environment.
2. Run the script: `python automation/save_session.py`
3. A Chromium browser window will open.
4. Enter your LinkedIn credentials and sign in.
5. Solve any 2FA or CAPTCHAs manually.
6. Once you see your LinkedIn home feed, **close the browser window**.
7. The script will save the session to `data/linkedin_session.json`.

## Step 3: Inject the Session into Your Application Agent

Now you must modify `automation/apply_playwright.py` to use that `linkedin_session.json` file when it launches, bypassing the login screen completely.

Modify the Playwright initialization in `apply_playwright.py` from this:

```python
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
```

To this:

```python
import os
from config import DATA_DIR
SESSION_FILE = os.path.join(DATA_DIR, "linkedin_session.json")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    # Check if we have a saved authenticated session
    if os.path.exists(SESSION_FILE):
        context = browser.new_context(storage_state=SESSION_FILE)
    else:
        print("Warning: No session file found. Proceeding unauthenticated.")
        context = browser.new_context()
        
    page = context.new_page()
```

## Security Warning
Your `linkedin_session.json` file now contains the equivalent of your username and password (your persistent session tokens). **Never commit this file to GitHub or share it with anyone.** It should be strictly ignored in `.gitignore`.

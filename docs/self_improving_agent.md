# How to Build a "Self-Improving Job Agent"

To make your agent **10x more powerful**, you don't just want it to apply blindly; you want it to learn from its mistakes and optimize its strategy over time. 

A standard agent is a "fire-and-forget" system. A **Self-Improving Agent** uses a closed feedback loop.

## Architecture of the Self-Improving Feedback Loop

1. **The Application Tracker** records every application sent, including the job description and the specific CV version used.
2. **The Inbox Monitor** scans your email inbox using IMAP for standard auto-responses and rejection letters.
3. **The Diagnostics Agent (LLM)** analyzes the rejection context:
   - Was it an immediate rejection? (Likely ATS filtering -> CV keywords need adjustment).
   - Was it after a technical test? (Need to upskill or target different tier jobs).
4. **The Strategy Optimizer** updates the vector database or prompts the Generator Agent to modify your CV for future applications.

## Technical Implementation Guide

### 1. Monitor Emails for Rejections
Use Python's `imaplib` or a service like Nylas/Google Workspace APIs to scan for emails containing "Application Status", "Update on your application", or "Moving forward with other candidates".

```python
import imaplib
import email

def fetch_rejection_emails(email_user, email_pass):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(email_user, email_pass)
    mail.select("inbox")
    
    # Search for common rejection keywords
    status, messages = mail.search(None, '(SUBJECT "Update on your application")')
    # ... parse emails and extract the company name and context
```

### 2. Add an "Evaluation Agent" to your CrewAI
Create a 4th agent in your CrewAI setup that runs weekly.

```python
from crewai import Agent

feedback_agent = Agent(
    role='Application Strategist',
    goal='Analyze rejection emails against applied job descriptions and determine why the candidate was rejected.',
    backstory='A former FAANG Recruiter who knows exactly why ATS systems reject resumes.',
    verbose=True,
    llm=ollama_llm
)
```

**Task for Feedback Agent:**
Pass the rejected job's description and the candidate's CV.
*Prompt*: *"The candidate was immediately rejected for this job. What keywords or skills were missing from the CV? Provide a list of 3 actionable CV tweaks."*

### 3. Dynamic Resume Tailoring (The Ultimate Hack)
Instead of applying with `cv.pdf`, have the agent generate a **tailored PDF** for every single job on the fly. 

Before the `Application Agent` runs Playwright:
1. Pass the approved job description and your base markdown CV to `llama3`.
2. Ask the LLM to emphasize the traits found in the job description in your experience section (without lying).
3. Use a library like `pdfkit` or `WeasyPrint` to compile the markdown into a fresh PDF (`data/cv_tailored_COMPANY.pdf`).
4. Upload that specific PDF using Playwright.

### 4. Updating the Match Threshold
If the system detects an 80% rejection rate for jobs where the vector match score was between 80-85, the agent autonomously updates `config.py`:
`MIN_MATCH_SCORE = 88`
This saves compute power and respects the daily application limits by only targeting the highest probability subsets.

---

### Summary of the Self-Improving Cycle
```
Apply -> Record in DB -> Listen to Inbox -> Detect Rejection -> Identify Missing Keyword from Job Description -> Update Base CV Prompt -> Generate Better Tailored CV on Next Apply
```

By adding these 4 steps, your agent transforms from a simple automation bot into a **hyper-optimized digital proxy** of yourself that conducts A/B testing on the job market!

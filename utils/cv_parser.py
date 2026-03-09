import pdfplumber
import logging
from config import CV_PATH

logger = logging.getLogger(__name__)

def load_cv(cv_path=CV_PATH):
    """
    Extracts text from the provided CV PDF.
    """
    if not cv_path.exists():
        logger.error(f"CV file not found at {cv_path}")
        return ""
    
    text = ""
    try:
        # Check if it's a dummy text file
        if cv_path.suffix != '.pdf':
            with open(cv_path, 'r', encoding='utf-8') as f:
                return f.read()

        with pdfplumber.open(cv_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error parsing CV: {e}")
        # Fallback to plain text read for testing
        with open(cv_path, 'r', encoding='utf-8') as f:
            return f.read()

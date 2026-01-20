"""
Configuration settings for the cold email engine.
Edit these values for your use case.
"""

import sys
from pathlib import Path

# === PATHS ===
# Handle PyInstaller bundled executable vs running from source
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = Path(sys.executable).parent
else:
    # Running from source
    BASE_DIR = Path(__file__).parent.parent

DATA_DIR = BASE_DIR / "data"

RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"
ENRICHED_DIR = DATA_DIR / "enriched"
SCORED_DIR = DATA_DIR / "scored"
EMAILS_DIR = DATA_DIR / "emails"
FINAL_DIR = DATA_DIR / "final"

# === SCRAPER SETTINGS ===
REQUEST_TIMEOUT = 10  # seconds
MAX_CONCURRENT_REQUESTS = 10  # parallel scraping
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# === SCORING WEIGHTS ===
SCORE_WEIGHTS = {
    "no_ssl": 3,
    "slow_site": 2,      # > 3 seconds
    "very_slow_site": 3, # > 5 seconds
    "no_contact_page": 1,
    "old_cms": 2,
    "no_mobile": 1,
    "missing_meta": 1,
}

# === EMAIL PATTERNS ===
# Common patterns for business emails
EMAIL_PATTERNS = [
    "{first}@{domain}",
    "{first}.{last}@{domain}",
    "{first}{last}@{domain}",
    "{f}{last}@{domain}",
    "{first}_{last}@{domain}",
    "info@{domain}",
    "contact@{domain}",
    "hello@{domain}",
    "admin@{domain}",
]

# === AI SETTINGS ===
OLLAMA_MODEL = "mistral"
OLLAMA_HOST = "http://localhost:11434"

# === OLD CMS INDICATORS ===
OLD_CMS_MARKERS = [
    "wordpress 4.",
    "wordpress 3.",
    "joomla 2.",
    "joomla 1.",
    "drupal 7",
    "drupal 6",
]
"""
config.py
---------
Central configuration for the Real Estate extraction pipeline.
Change settings here — every module reads from this file.
"""

import os

_HERE = os.path.dirname(__file__)

# ── Database ──────────────────────────────────────────────────────────────────

DB_PATH = os.path.join(_HERE, "TestOrg2.db")

# ── Gemini model ──────────────────────────────────────────────────────────────

GEMINI_MODEL = "gemini-2.5-flash-lite"
MAX_RETRIES  = 3
TEMPERATURE  = 0.5

# ── Gemini pricing  (USD per 1 million tokens) ────────────────────────────────
# Gemini 2.5 Flash Lite pricing as of 2025.
# Update these if your model tier or Gemini's price sheet changes.

PRICE_INPUT       = 0.10    # fresh input tokens
PRICE_CACHED_READ = 0.025   # cached input tokens (Gemini implicit cache rate)
PRICE_OUTPUT      = 0.40    # output tokens (thinking tokens billed at same rate)

# ── Batching ──────────────────────────────────────────────────────────────────

MAX_CHARS_PER_BATCH = 8_000   # fill a batch up to this many characters …
MAX_ADS_PER_BATCH   = 10      # … or this many ads, whichever comes first
CHARS_PER_TOKEN     = 3.0     # rough estimate for mixed Arabic / English text

# ── Daily cost guard ──────────────────────────────────────────────────────────

MAX_DAILY_LIMIT = 2.0   # USD — pipeline prints a warning when exceeded

# ── File paths ────────────────────────────────────────────────────────────────

PROGRESS_FILE      = "progress.json"
UPLOADED_CHAT_FILE = "uploaded_chat_file.txt"
COST_FILE          = "costs.json"
ANALYSIS_PATH      = os.path.join(_HERE, "Big_Analysis.md")

# ── Miscellaneous ─────────────────────────────────────────────────────────────

TRUNCATE_CHARS = 10_000   # max chars shown inside collapsible analysis blocks
MIN_BODY_LEN   = 20       # filter: reject messages shorter than this (chars)

"""
Real Estate Ad Extraction Pipeline
===================================
1. Parses a WhatsApp chat export (.txt)
2. Filters to a target day of messages
3. Removes non-ad messages using a 3-gate filter:
      Gate 1 — System messages (group events, media, calls)
      Gate 2 — Blocklist  (buyer requests, spam, greetings)
      Gate 3 — Allowlist  (must contain ≥1 real-estate keyword)
4. Sends ads to Gemini for structured extraction
5. Stores results in SQLite

Usage:
    pip install google-genai
    python extractFromChatExport.py
"""

import re
import os
import json
import sqlite3
import time
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv


# ─── Timing helpers ──────────────────────────────────────────────────────────

LOG_PATH = "pipeline_runs.log"

def _ts() -> float:
    return time.perf_counter()

def _elapsed(start: float) -> float:
    return time.perf_counter() - start

def _fmt(seconds: float) -> str:
    return f"{seconds*1000:.0f}ms" if seconds < 1 else f"{seconds:.2f}s"

def _log(run_record: dict):
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(run_record, ensure_ascii=False) + "\n")


# Load environment variables
load_dotenv()

# ─── Configuration ───────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL   = "gemini-2.5-flash-lite"
DB_PATH        = "listings.db"
BATCH_SIZE     = 10
MAX_RETRIES    = 3

# ─── 1. Parse WhatsApp Export ────────────────────────────────────────────────

# WhatsApp uses U+202F (narrow no-break space) between time and am/pm in native
# exports. \s already matches it, so this handles both native and converted files.
WA_MSG_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+"         # date
    r"(\d{1,2}:\d{2}(?::\d{2})?\s*[aApP][mM])"  # time  (U+202F covered by \s)
    r"\s*-\s+"                                    # separator
    r"(.+?):\s+"                                  # sender
    r"([\s\S]*?)$"                                # body (first line)
)


def parse_whatsapp_export(filepath: str) -> list[dict]:
    """Parse a WhatsApp .txt export into structured message dicts."""
    with open(chat_file, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()

    messages = []
    current  = None

    for line in raw.split("\n"):
        m = WA_MSG_PATTERN.match(line)
        if m:
            if current:
                messages.append(current)
            date_str, time_str, sender, body = m.groups()
            dt = _parse_datetime(date_str, time_str)
            current = {"datetime": dt, "sender": sender.strip(), "body": body.strip()}
        elif current:
            current["body"] += "\n" + line

    if current:
        messages.append(current)
    return messages


def _parse_datetime(date_str: str, time_str: str) -> datetime:
    combined = f"{date_str}, {time_str}".strip()
    formats = [
        "%d/%m/%Y, %I:%M %p",  "%d/%m/%Y, %I:%M%p",
        "%d/%m/%y, %I:%M %p",  "%d/%m/%y, %I:%M%p",
        "%m/%d/%Y, %I:%M %p",  "%m/%d/%y, %I:%M %p",
        "%d/%m/%Y, %I:%M:%S %p",
    ]
    # Normalise casing of am/pm and try each format
    clean = re.sub(r'[aApP][mM]', lambda x: x.group().upper(), combined)
    for fmt in formats:
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {combined!r}")


# ─── Date-range Crop Utility ─────────────────────────────────────────────────

def crop_chat_by_date(
    filepath: str,
    start_day: int, start_month: int, start_year: int,
    end_day:   int, end_month:   int, end_year:   int,
) -> str:
    """
    Write all messages in [start_date, end_date] (inclusive) to a new file:
        <basename>_cropped_DDMMYYYY-DDMMYYYY.txt

    Preserves every raw line exactly (multi-line messages stay intact).
    Returns the output file path.

    Example:
        crop_chat_by_date("chat.txt", 1, 3, 2025, 7, 3, 2025)
        # → chat_cropped_01032025-07032025.txt
    """
    from datetime import date as _date
    start_date = _date(start_year, start_month, start_day)
    end_date   = _date(end_year,   end_month,   end_day)
    if start_date > end_date:
        raise ValueError(f"start_date {start_date} is after end_date {end_date}")

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    out_lines:     list[str]       = []
    current_block: list[str]       = []
    in_range:      bool | None     = None

    def flush():
        if in_range:
            out_lines.extend(current_block)

    for line in lines:
        m = WA_MSG_PATTERN.match(line)
        if m:
            flush()
            current_block = [line]
            try:
                dt = _parse_datetime(m.group(1), m.group(2))
                in_range = start_date <= dt.date() <= end_date
            except ValueError:
                in_range = False
        else:
            current_block.append(line)
    flush()

    base, ext = os.path.splitext(filepath)
    tag      = f"{start_day:02d}{start_month:02d}{start_year}-{end_day:02d}{end_month:02d}{end_year}"
    out_path = f"{base}_cropped_{tag}{ext}"

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)

    n = sum(1 for l in out_lines if WA_MSG_PATTERN.match(l))
    print(f"Cropped {n} messages ({start_date} → {end_date}) → {out_path}")
    return out_path


# ─── 2. Filter Messages ──────────────────────────────────────────────────────
#
# Three-gate strategy:
#   Gate 1 — SYSTEM_RE   : WhatsApp group-management events, media notices, etc.
#             Drop unconditionally — these are never ads.
#   Gate 2 — BLOCKLIST_RE: Buyer requests, financial spam, greetings.
#             Drop even if an RE keyword happens to appear.
#   Gate 3 — ALLOWLIST_RE: Must contain ≥1 real-estate keyword to pass.
#             Anything without a property/transaction/location signal is dropped.
#
# This mirrors the notebook's allowlist approach while keeping your explicit
# blocklist for patterns that would otherwise survive keyword matching.

# ── Gate 1: system messages ───────────────────────────────────────────────────
_SYSTEM_PATTERNS = [
    r"Messages and calls are end-to-end encrypted",
    r"\badded\s+\+?\d",
    r"\bleft$",
    r"\bremoved\s+\+?\d",
    r"changed the subject",
    r"changed this group",
    r"changed the group",
    r"created group",
    r"joined using this group",
    r"security code changed",
    r"Your security code with",
    r"<[Mm]edia omitted>",
    r"image omitted",
    r"video omitted",
    r"audio omitted",
    r"sticker omitted",
    r"document omitted",
    r"Contact card omitted",
    r"GIF omitted",
    r"location:?\s*https?://",
    r"This message was deleted",
    r"You deleted this message",
    r"Missed voice call",
    r"Missed video call",
    r"^null$",
]
SYSTEM_RE = re.compile("|".join(_SYSTEM_PATTERNS), re.IGNORECASE)

# ── Gate 2: blocklist ─────────────────────────────────────────────────────────
# Rejected even if RE keywords appear — these are never listings.
_BLOCKLIST_PATTERNS = [
    # Buyer requests — Arabic                                               # wanted/required (anywhere)
    r"أبحث\s*عن|ابحث\s*عن",                               # I'm looking for
    r"بدور\s*على|بدوّر\s*على",                             # looking for (colloquial)
    r"محتاج\s*(شقة|شقه|فيلا|وحدة|وحده|أرض|ارض|محل)",
    r"عايز\s*(أشتري|اشتري|اجار|ايجار|ايجاره)",
    # Buyer requests — English / Franco
    r"urgent\s*request",
    r"\blooking\s+for\b",
    r"\bwanted\b.{0,40}\b(apartment|villa|flat|unit|land|office)\b",
    r"\b(3ayez|3ayz)\b",
    # Financial spam
    r"تمويلات?\s*بنكي",
    r"قرض\s*شخصي",
    r"كاش\s*باك",
    r"#.*تمويل",
    r"\busdt\b",
    r"\bbitcoin\b|\bcrypto\b|\berc20\b",
    # Recruitment / off-topic
    r"we\s*are\s*hiring",
    r"sales\s*team\s*leader",
    r"chat\.whatsapp\.com",
    r"not\s*spam\s*please",
    r"ممنوع\s*الصور",
    r"سيتم\s*الحذف",
    # Pure greetings (full-message)
    r"^(السلام\s*عليكم|وعليكم\s*السلام|صباح\s*الخير|صباح\s*النور|مساء\s*الخير)\s*$",
    r"^good\s*(morning|evening|night)\s*$",
    r"^(hi|hello|hey|ok|okay|تمام|ماشي)\s*$",
    r"^\?\s*$",
]
BLOCKLIST_RE = re.compile("|".join(_BLOCKLIST_PATTERNS), re.IGNORECASE | re.MULTILINE)

# ── Gate 3: allowlist ─────────────────────────────────────────────────────────
# Must match at least one term from Arabic, English, or Franco-Arab keyword sets.

_KW_AR = [
    # Transaction
    "للبيع", "للإيجار", "للايجار", "للاستثمار", "إيجار", "ايجار", "بيع",
    "إيجار يومي", "يومي", "شهري", "سنوي",
    # Property types
    "شقة", "شقه", "فيلا", "فيللا", "دوبلكس", "دوبليكس", "بنتهاوس", "ستوديو",
    "تاون هاوس", "تاونهاوس", "توين هاوس", "وحدة", "وحده",
    "أرض", "ارض", "قطعة أرض", "محل", "مكتب", "عيادة", "مخزن", "مستودع",
    "بناية", "عمارة", "روف", "شاليه",
    # Specs
    "غرفة", "غرفه", "غرف", "حمام", "حمامات", "مساحة", "مساحه", "متر", "م2",
    "دور", "طابق", "أدوار", "بدروم", "ريسيبشن", "صالة", "صاله",
    # Finishing / condition
    "مفروش", "مفروشة", "تشطيب", "سوبر لوكس", "لوكس", "نص تشطيب",
    "كور آند شيل", "تشطيب كامل", "الترا سوبر",
    # Financial
    "سعر", "مقدم", "قسط", "أقساط", "تقسيط", "دفعة",
    "مليون", "ألف", "الف", "مليار",
    # Features
    "جاردن", "حديقة", "بركة سباحة", "حمام سباحة", "بلكونة", "تراس",
    "أسانسير", "جراج", "موقف", "أمن", "بوابة", "كمبوند",
    # Egyptian locations & compound names
    "التجمع", "الرحاب", "مدينتي", "الشيخ زايد", "العاصمة الإدارية",
    "الساحل", "العين السخنة", "أكتوبر", "المهندسين", "الدقي", "المعادي",
    "مصر الجديدة", "هليوبوليس", "النزهة", "الزمالك", "وسط البلد",
    "القاهرة الجديدة", "بدر", "الإسكندرية", "الغردقة",
    "شرم الشيخ", "الجونة", "سيدي عبد الرحمن", "العلمين",
    "هايد بارك", "ميفيدا", "ماونتن فيو", "ذا ادرس", "بالم هيلز", "ايستاون",
]

_KW_EN = [
    # Transaction
    "for sale", "for rent", "resale", "lease",
    # Property types
    "apartment", "villa", "studio", "duplex", "penthouse", "chalet",
    "townhouse", "twin house", "standalone", "office", "warehouse", "land",
    "flat", "unit", "roof", "shop", "clinic", "building",
    # Specs
    "bedroom", "bathroom", "sqm", "sq m", "sq.m", "m2", "ground floor", "reception",
    # Finishing
    "furnished", "unfurnished", "semi finished",
    "core & shell", "core and shell", "super lux", "super luxury", "finished",
    # Financial
    "cash", "installment", "down payment", "negotiable",
    # Features
    "garden", "pool", "balcony", "terrace", "parking", "garage", "security",
    "elevator", "compound",
    # Locations
    "new cairo", "sheikh zayed", "new capital", "ain sokhna", "north coast",
    "maadi", "heliopolis", "zamalek", "nasr city",
    "mivida", "hyde park", "palm hills", "mountain view", "east town",
    "el rehab", "madinaty",
]

_KW_FRANCO = [
    # Romanised Egyptian Arabic
    "sha2a", "she2a", "2otda", "otda", "ghorf", "hamam",
    "ll bai3", "lel bai3", "ll egar", "lel egar",
    "mafroush", "super lux", "teshteeb",
]

# Sort longest-first so longer phrases match before their substrings
_kw_all = sorted(set(_KW_AR + _KW_EN + _KW_FRANCO), key=len, reverse=True)
ALLOWLIST_RE = re.compile(
    "|".join(re.escape(kw) for kw in _kw_all),
    re.IGNORECASE,
)

MIN_BODY_LEN = 20  # characters — anything shorter is noise


def filter_ads(messages: list[dict]) -> tuple[list[dict], dict]:
    """
    Apply the 3-gate filter. Returns (ads, stats) where stats breaks down
    how many messages were dropped at each gate.
    """
    stats = {"system": 0, "too_short": 0, "blocklist": 0, "no_keywords": 0, "passed": 0}
    ads   = []

    for msg in messages:
        body = msg["body"].strip()

        if SYSTEM_RE.search(body):
            stats["system"] += 1
            continue

        if len(body) < MIN_BODY_LEN:
            stats["too_short"] += 1
            continue

        if BLOCKLIST_RE.search(body):
            stats["blocklist"] += 1
            continue

        if not ALLOWLIST_RE.search(body):
            stats["no_keywords"] += 1
            continue

        stats["passed"] += 1
        ads.append(msg)

    return ads, stats


def get_recent_days(messages: list[dict], days: int = 2) -> list[dict]:
    """
    Return messages from the N most recent full days in the export.
    Excludes the very last date (may be incomplete) and takes the `days`
    dates before it. If the export has fewer dates than requested, returns
    whatever is available.
    """
    if not messages:
        return []
    dates = sorted(set(m["datetime"].date() for m in messages))
    # Drop the last date (potentially incomplete), then take last `days` dates
    full_dates = dates[:-1] if len(dates) > 1 else dates
    target_dates = set(full_dates[-days:])
    return [m for m in messages if m["datetime"].date() in target_dates]


# ─── 3. Gemini API Extraction ────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a real estate data extraction engine. You receive property advertisement texts from Egyptian real estate groups.

Extract structured data from each ad. Return a JSON array where each element corresponds to one ad.

SCHEMA — every field is nullable (use null if not determinable):

{
  "property_type": "apartment|villa|studio|duplex|penthouse|chalet|townhouse|twin_house|standalone|i_villa|land|office|shop|warehouse|building|loft|other",
  "transaction_type": "sale|rent|daily_rent",
  "price": <number, no commas, normalize "4.5M" to 4500000, "25k" to 25000>,
  "currency": "EGP|USD|EUR",
  "price_negotiable": <bool>,
  "area_sqm": <number, BUA/built-up area in sqm>,
  "land_area_sqm": <number, land area if different from BUA>,
  "bedrooms": <int, studio=0>,
  "bathrooms": <int>,
  "floor_number": <int, ground=0>,
  "total_floors": <int>,
  "furnished": "furnished|semi_furnished|unfurnished",
  "finishing": "shell|core_and_shell|semi_finished|finished|luxury",
  "has_elevator": <bool>,
  "has_garden": <bool>,
  "garden_area_sqm": <number>,
  "has_pool": <bool>,
  "has_balcony": <bool>,
  "has_security": <bool>,
  "has_parking": <bool>,
  "amenities": [<strings: AC, smart home, kitchen, dressing, shutters, gas, etc.>],
  "city": "<string>",
  "district": "<string>",
  "compound_name": "<string>",
  "landmark_proximity": "<string>",
  "payment_method": "cash|installment|both",
  "down_payment": <number>,
  "installment_years": <number>,
  "installment_amount": <number>,
  "advertiser_type": "owner|broker|developer",
  "phone_numbers": [<strings, preserve original format>],
  "reference_id": "<string, any code like U926440 or HPs160>",
  "confidence_score": <float 0-1, your confidence in the extraction>,
  "language": "ar|en|mixed",
  "view": "<string, e.g. pool, fountain, garden>"
}

RULES:
- Default currency is EGP unless stated otherwise.
- Default city is Cairo / New Cairo for compounds like Hyde Park, Sodic East, etc.
- "super lux" or "الترا سوبر لوكس" = luxury finishing.
- "core and shell" or "core & shell" = core_and_shell finishing.
- "لوكس" alone = finished.
- Prices with commas like "35.000" in rental context mean 35,000 (not 35).
- "مطبخ" = kitchen in amenities.
- "تكيفات" = AC in amenities.
- "شاتر" = shutters in amenities.
- BUA = Built-Up Area = the main area field.
- Return ONLY valid JSON. No markdown, no explanation."""


def build_extraction_prompt(ads: list[dict]) -> str:
    parts = []
    for i, ad in enumerate(ads, 1):
        parts.append(f"--- AD {i} (from: {ad['sender']}, date: {ad['datetime'].isoformat()}) ---")
        parts.append(ad["body"])
        parts.append("")
    return "\n".join(parts)


def call_gemini(ads: list[dict]) -> tuple[list[dict], dict]:
    """Call Gemini to extract structured data. Returns (results, timing_info)."""
    from google import genai
    from google.genai import types

    client      = genai.Client(api_key=GEMINI_API_KEY)
    user_prompt = build_extraction_prompt(ads)
    timing      = {"api_call_s": None, "json_parse_s": None, "attempts": 0}

    for attempt in range(MAX_RETRIES):
        timing["attempts"] = attempt + 1
        t_parse = None
        try:
            t_api = _ts()
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            timing["api_call_s"] = _elapsed(t_api)

            t_parse = _ts()
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
            parsed = json.loads(raw)
            timing["json_parse_s"] = _elapsed(t_parse)

            if isinstance(parsed, dict):
                parsed = [parsed]
            return parsed, timing

        except json.JSONDecodeError as e:
            timing["json_parse_s"] = _elapsed(t_parse) if t_parse else None
            print(f"  [!] JSON parse error (attempt {attempt+1}): {e}")
        except Exception as e:
            print(f"  [!] API error (attempt {attempt+1}): {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)

    print("  [!] Failed after all retries, skipping batch.")
    return [], timing


# ─── 4. Database ─────────────────────────────────────────────────────────────

def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_type TEXT,
            transaction_type TEXT,
            price REAL,
            currency TEXT DEFAULT 'EGP',
            price_negotiable INTEGER,
            area_sqm REAL,
            land_area_sqm REAL,
            bedrooms INTEGER,
            bathrooms INTEGER,
            floor_number INTEGER,
            total_floors INTEGER,
            furnished TEXT,
            finishing TEXT,
            has_elevator INTEGER,
            has_garden INTEGER,
            garden_area_sqm REAL,
            has_pool INTEGER,
            has_balcony INTEGER,
            has_security INTEGER,
            has_parking INTEGER,
            amenities TEXT,
            city TEXT,
            district TEXT,
            compound_name TEXT,
            landmark_proximity TEXT,
            payment_method TEXT,
            down_payment REAL,
            installment_years REAL,
            installment_amount REAL,
            advertiser_type TEXT,
            phone_numbers TEXT,
            reference_id TEXT,
            confidence_score REAL,
            language TEXT,
            view TEXT,
            original_message TEXT,
            sender TEXT,
            ad_date TEXT,
            extracted_at TEXT DEFAULT (datetime('now')),
            extraction_method TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_property_type    ON listings(property_type);
        CREATE INDEX IF NOT EXISTS idx_transaction_type ON listings(transaction_type);
        CREATE INDEX IF NOT EXISTS idx_city_district    ON listings(city, district);
        CREATE INDEX IF NOT EXISTS idx_compound         ON listings(compound_name);
        CREATE INDEX IF NOT EXISTS idx_price            ON listings(price);
        CREATE INDEX IF NOT EXISTS idx_bedrooms         ON listings(bedrooms);
        CREATE INDEX IF NOT EXISTS idx_area             ON listings(area_sqm);
        CREATE INDEX IF NOT EXISTS idx_ad_date          ON listings(ad_date);
    """)
    conn.commit()
    return conn


def insert_listing(conn: sqlite3.Connection, data: dict,
                   original_msg: str, sender: str, ad_date: str):
    amenities = json.dumps(data.get("amenities")     or [], ensure_ascii=False)
    phones    = json.dumps(data.get("phone_numbers") or [], ensure_ascii=False)
    conn.execute("""
        INSERT INTO listings (
            property_type, transaction_type, price, currency, price_negotiable,
            area_sqm, land_area_sqm, bedrooms, bathrooms,
            floor_number, total_floors, furnished, finishing,
            has_elevator, has_garden, garden_area_sqm, has_pool,
            has_balcony, has_security, has_parking,
            amenities, city, district, compound_name, landmark_proximity,
            payment_method, down_payment, installment_years, installment_amount,
            advertiser_type, phone_numbers, reference_id,
            confidence_score, language, view,
            original_message, sender, ad_date, extraction_method
        ) VALUES (
            ?,?,?,?,?, ?,?,?,?, ?,?,?,?,
            ?,?,?,?, ?,?,?,
            ?,?,?,?,?, ?,?,?,?,
            ?,?,?, ?,?,?,
            ?,?,?,?
        )
    """, (
        data.get("property_type"),      data.get("transaction_type"),
        data.get("price"),              data.get("currency", "EGP"),
        _b(data.get("price_negotiable")),
        data.get("area_sqm"),           data.get("land_area_sqm"),
        data.get("bedrooms"),           data.get("bathrooms"),
        data.get("floor_number"),       data.get("total_floors"),
        data.get("furnished"),          data.get("finishing"),
        _b(data.get("has_elevator")),   _b(data.get("has_garden")),
        data.get("garden_area_sqm"),    _b(data.get("has_pool")),
        _b(data.get("has_balcony")),    _b(data.get("has_security")),
        _b(data.get("has_parking")),
        amenities,                      data.get("city"),
        data.get("district"),           data.get("compound_name"),
        data.get("landmark_proximity"),
        data.get("payment_method"),     data.get("down_payment"),
        data.get("installment_years"),  data.get("installment_amount"),
        data.get("advertiser_type"),    phones,
        data.get("reference_id"),
        data.get("confidence_score"),   data.get("language"),
        data.get("view"),
        original_msg, sender, ad_date, GEMINI_MODEL,
    ))


def _b(val) -> Optional[int]:
    return None if val is None else (1 if val else 0)


# ─── 5. Main Pipeline ────────────────────────────────────────────────────────

def run_pipeline(chat_file: str, days: int = 2):
    run_start = _ts()
    run_ts    = datetime.now().isoformat(timespec="seconds")

    print(f"{'='*60}")
    print(f"  Real Estate Ad Extraction Pipeline")
    print(f"  Started: {run_ts}  |  Model: {GEMINI_MODEL}  |  Batch: {BATCH_SIZE}  |  Days: {days}")
    print(f"{'='*60}\n")

    timings = {}

    # ── Step 1: Parse ──────────────────────────────────────────
    print("[1/5] Parsing WhatsApp export...", end=" ", flush=True)
    t = _ts()
    messages = parse_whatsapp_export(chat_file)
    timings["parse_s"] = _elapsed(t)
    print(f"({_fmt(timings['parse_s'])})")
    print(f"      Total messages parsed: {len(messages)}")

    if not messages:
        print("      No messages found. Check file format.")
        return

    dates = sorted(set(m["datetime"].date() for m in messages))
    print(f"      Date range: {dates[0]} → {dates[-1]}")

    # ── Step 2: Select target days ─────────────────────────────
    print(f"\n[2/5] Selecting {days} most recent full day(s)...", end=" ", flush=True)
    t = _ts()
    day_messages = get_recent_days(messages, days)
    timings["day_filter_s"] = _elapsed(t)
    print(f"({_fmt(timings['day_filter_s'])})")

    target_dates = sorted(set(m["datetime"].date() for m in day_messages))
    target_date  = f"{target_dates[0]} → {target_dates[-1]}" if target_dates else "N/A"
    print(f"      Target dates: {target_date}  ({len(day_messages)} messages)")

    # ── Step 3: 3-gate ad filter ───────────────────────────────
    print(f"\n[3/5] Filtering ads (3-gate)...", end=" ", flush=True)
    t = _ts()
    ads, fstats = filter_ads(day_messages)
    timings["ad_filter_s"] = _elapsed(t)
    total_dropped = len(day_messages) - fstats["passed"]
    print(f"({_fmt(timings['ad_filter_s'])})")
    print(f"      Dropped {total_dropped} / {len(day_messages)}:")
    print(f"        system msgs   : {fstats['system']}")
    print(f"        too short     : {fstats['too_short']}")
    print(f"        blocklist     : {fstats['blocklist']}  (requests, spam, greetings)")
    print(f"        no RE keyword : {fstats['no_keywords']}")
    print(f"      Ads to process  : {fstats['passed']}")

    if not ads:
        print("      No ads found after filtering.")
        return

    # ── Step 4: Gemini extraction ──────────────────────────────
    print(f"\n[4/5] Extracting via {GEMINI_MODEL}...")
    conn          = init_db()
    total_inserted = 0
    total_batches  = (len(ads) + BATCH_SIZE - 1) // BATCH_SIZE
    batch_timings  = []

    t_extraction = _ts()
    for batch_idx in range(0, len(ads), BATCH_SIZE):
        batch     = ads[batch_idx : batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1
        print(f"      Batch {batch_num}/{total_batches} ({len(batch)} ads)...", end=" ", flush=True)

        t_batch  = _ts()
        results, bt = call_gemini(batch)
        batch_total = _elapsed(t_batch)

        t_db = _ts()
        for i, result in enumerate(results):
            if i < len(batch):
                ad = batch[i]
                insert_listing(conn, result,
                               original_msg=ad["body"],
                               sender=ad["sender"],
                               ad_date=ad["datetime"].isoformat())
                total_inserted += 1
        conn.commit()
        db_s = _elapsed(t_db)

        bt.update(batch_num=batch_num, ads_in=len(batch), ads_out=len(results),
                  db_insert_s=db_s, batch_total_s=batch_total)
        batch_timings.append(bt)

        api_s   = _fmt(bt["api_call_s"])   if bt["api_call_s"]   else "err"
        parse_s = _fmt(bt["json_parse_s"]) if bt["json_parse_s"] else "err"
        print(f"OK ({len(results)} extracted) | total={_fmt(batch_total)} api={api_s} json={parse_s} db={_fmt(db_s)}")

        if batch_idx + BATCH_SIZE < len(ads):
            time.sleep(1)

    timings["extraction_s"] = _elapsed(t_extraction)
    timings["total_s"]      = _elapsed(run_start)

    # ── Step 5: Summary ────────────────────────────────────────
    print(f"\n[5/5] Done!")
    print(f"      Listings saved : {total_inserted}")
    print(f"      Database       : {os.path.abspath(DB_PATH)}")
    print(f"\n  ── Timings ──────────────────────────────────────────")
    print(f"      Parse          : {_fmt(timings['parse_s'])}")
    print(f"      Day select     : {_fmt(timings['day_filter_s'])}")
    print(f"      Ad filter      : {_fmt(timings['ad_filter_s'])}")
    print(f"      Gemini total   : {_fmt(timings['extraction_s'])}  ({total_batches} batches)")
    if batch_timings:
        valid = [b for b in batch_timings if b["api_call_s"]]
        if valid:
            print(f"      Avg API/batch  : {_fmt(sum(b['api_call_s'] for b in valid) / len(valid))}")
        print(f"      Avg total/batch: {_fmt(sum(b['batch_total_s'] for b in batch_timings) / len(batch_timings))}")
    print(f"      TOTAL          : {_fmt(timings['total_s'])}")
    print(f"  ─────────────────────────────────────────────────────")

    cursor = conn.execute("""
        SELECT property_type, COUNT(*) FROM listings
        WHERE property_type IS NOT NULL
        GROUP BY property_type ORDER BY 2 DESC
    """)
    prop_types = {r[0]: r[1] for r in cursor}
    print(f"\n      Property types:")
    for k, v in prop_types.items():
        print(f"        {k}: {v}")

    cursor   = conn.execute("SELECT AVG(confidence_score) FROM listings")
    avg_conf = cursor.fetchone()[0]
    if avg_conf:
        print(f"      Avg confidence : {avg_conf:.2f}")

    conn.close()

    # ── Log run ────────────────────────────────────────────────
    _log({
        "run_at": run_ts,
        "model": GEMINI_MODEL,
        "batch_size": BATCH_SIZE,
        "input_file": chat_file,
        "days_requested": days,
        "target_dates": [str(d) for d in target_dates],
        "total_messages": len(messages),
        "day_messages": len(day_messages),
        "filter_stats": fstats,
        "ads_processed": len(ads),
        "listings_inserted": total_inserted,
        "avg_confidence": round(avg_conf, 4) if avg_conf else None,
        "property_type_counts": prop_types,
        "timings": {k: round(v, 3) for k, v in timings.items()},
        "batches": [{
            "batch":         b["batch_num"],
            "ads_in":        b["ads_in"],
            "ads_out":       b["ads_out"],
            "api_call_s":    round(b["api_call_s"],   3) if b["api_call_s"]   else None,
            "json_parse_s":  round(b["json_parse_s"], 4) if b["json_parse_s"] else None,
            "db_insert_s":   round(b["db_insert_s"],  4),
            "batch_total_s": round(b["batch_total_s"],3),
            "attempts":      b["attempts"],
        } for b in batch_timings],
    })
    print(f"\n      Run logged → {os.path.abspath(LOG_PATH)}")


# ─── Entry point ─────────────────────────────────────────────────────────────

chat_file="WhatsApp Chat with SELL & RENT.txt"
# run_pipeline(chat_file,1)
# crop_chat_by_date(chat_file, 28, 9, 2024, 28, 9, 2024)

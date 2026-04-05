"""
Real Estate Ad Extraction Pipeline
===================================
1. Parses a WhatsApp chat export (.txt)          ← filter_chat.py
2. Filters to a target day of messages
3. Removes non-ad messages using a 3-gate filter ← filter_chat.py
4. Sends ads to Gemini for structured extraction
5. Stores results in SQLite

"""

import re
import os
import json
import sqlite3
import time
from datetime import datetime
from typing import Literal, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# ── All parsing + filtering comes from filter_chat ───────────────────────────
from filter_chat import (
    parse_whatsapp_export,  # .txt → list[dict]  (datetime is a real datetime obj)
    classify,  # msg → "pass" | "system" | "too_short" | "blocklist" | "no_keywords"
    WA_MSG_PATTERN,  # regex used by crop_chat_by_date
)
from batch_messages import build_batches, compute_ads_avg
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


load_dotenv()

# ─── Configuration ───────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
GEMINI_MODEL = "gemini-2.5-flash-lite"
DB_PATH = "test_listings.db"
BATCH_SIZE = 10
MAX_RETRIES = 3
DEBUG_MODEL   = False   # prints thinking + raw response and halts; set False to run full pipeline


# ─── Date-range Crop Utility ─────────────────────────────────────────────────

def crop_chat_by_date(
    filepath: str,
    start_day: int,
    start_month: int,
    start_year: int,
    end_day: int,
    end_month: int,
    end_year: int,
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
    end_date = _date(end_year, end_month, end_day)
    if start_date > end_date:
        raise ValueError(f"start_date {start_date} is after end_date {end_date}")

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    out_lines: list[str] = []
    current_block: list[str] = []
    in_range: bool | None = None

    def flush():
        if in_range:
            out_lines.extend(current_block)

    for line in lines:
        m = WA_MSG_PATTERN.match(line)
        if m:
            flush()
            current_block = [line]
            try:
                combined = f"{m.group(1)}, {m.group(2)}".strip()
                clean = re.sub(r"[aApP][mM]", lambda x: x.group().upper(), combined)
                dt = None
                for fmt in [
                    "%d/%m/%Y, %I:%M %p",
                    "%d/%m/%Y, %I:%M%p",
                    "%d/%m/%y, %I:%M %p",
                    "%d/%m/%y, %I:%M%p",
                    "%m/%d/%Y, %I:%M %p",
                    "%m/%d/%y, %I:%M %p",
                    "%d/%m/%Y, %I:%M:%S %p",
                ]:
                    try:
                        dt = datetime.strptime(clean, fmt)
                        break
                    except ValueError:
                        continue
                in_range = (start_date <= dt.date() <= end_date) if dt else False
            except Exception:
                in_range = False
        else:
            current_block.append(line)
    flush()

    base, ext = os.path.splitext(filepath)
    tag = f"{start_day:02d}{start_month:02d}{start_year}-{end_day:02d}{end_month:02d}{end_year}"
    out_path = f"{base}_cropped_{tag}{ext}"

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(out_lines)

    n = sum(1 for l in out_lines if WA_MSG_PATTERN.match(l))
    print(f"Cropped {n} messages ({start_date} → {end_date}) → {out_path}")
    return out_path


# ─── 2. Date filtering ───────────────────────────────────────────────────────


def get_recent_days(messages: list[dict], days: int = 2) -> list[dict]:
    """
    Return messages from the N most recent full days in the export.
    (Last date is NOT excluded — matches original MODIFIED behaviour.)
    """
    if not messages:
        return []
    dates = sorted(set(m["datetime"].date() for m in messages))
    target_dates = set(dates[-days:])
    return [m for m in messages if m["datetime"].date() in target_dates]


# ─── 3. Ad filter — delegates to filter_chat.classify ────────────────────────


def filter_ads(messages: list[dict]) -> tuple[list[dict], dict]:
    """
    Apply the 3-gate filter via filter_chat.classify().
    Returns (ads, stats) — identical interface to the original pipeline.
    """
    stats = {"system": 0, "too_short": 0, "blocklist": 0, "no_keywords": 0, "passed": 0}
    ads = []

    for msg in messages:
        result = classify(msg)
        if result == "pass":
            stats["passed"] += 1
            ads.append(msg)
        else:
            stats[result] += 1

    return ads, stats


# ─── 4. Gemini API Extraction ────────────────────────────────────────────────


class ListingExtraction(BaseModel):
    property_type: Optional[
        Literal[
            "apartment",
            "villa",
            "studio",
            "duplex",
            "penthouse",
            "chalet",
            "townhouse",
            "twin_house",
            "standalone",
            "i_villa",
            "land",
            "office",
            "shop",
            "warehouse",
            "building",
            "loft",
            "other",
        ]
    ] = Field(default=None, description="Category of the property being advertised. If not explicitly stated, set to null and if mentioned in text but not in the fields available, set to 'other'.")
    transaction_type: Optional[Literal["sale", "rent", "daily_rent"]] = Field(
        default=None,
        description="Whether the property is for sale, long-term rent, or nightly/daily rent.",
    )
    price: Optional[float] = Field(
        default=None,
        description="Asking price as a plain number. Normalize shorthand: '4.5M' → 4500000, '25k' → 25000. "
        "Prices written with a period as thousands separator (e.g. '35.000' in a rental context) mean 35000.",
    )
    currency: Optional[Literal["EGP", "USD", "EUR"]] = Field(
        default=None,
        description="Currency of the price. Default to EGP when not explicitly stated.",
    )
    area_sqm: Optional[float] = Field(
        default=None,
        description="Built-up area (BUA) in square metres — the main usable floor area of the unit.",
    )
    land_area_sqm: Optional[float] = Field(
        default=None,
        description="Total land/plot area in square metres, only when it differs from the built-up area "
        "(common for villas, twin houses, and land listings).",
    )
    bedrooms: Optional[int] = Field(
        default=None, description="Number of bedrooms. Use 0 for studios."
    )
    bathrooms: Optional[int] = Field(default=None, description="Number of bathrooms.")
    floor_number: Optional[int] = Field(
        default=None, description="Floor on which the unit sits. Ground floor = 0."
    )
    total_floors: Optional[int] = Field(
        default=None, description="Total number of floors in the building."
    )
    furnished: Optional[Literal["furnished", "semi_furnished", "unfurnished"]] = Field(
        default=None, description="Furnishing status of the unit."
    )
    finishing: Optional[
        Literal["shell", "core_and_shell", "semi_finished", "finished", "luxury"]
    ] = Field(
        default=None,
        description="Interior finishing level. "
        "'super lux' or 'الترا سوبر لوكس' → luxury. "
        "'لوكس' alone → finished. "
        "Unfinished/skeleton units → shell.",
    )
    has_garden: Optional[bool] = Field(
        default=None, description="True if the unit includes a private garden."
    )
    garden_area_sqm: Optional[float] = Field(
        default=None,
        description="Area of the private garden in square metres, if stated.",
    )
    has_pool: Optional[bool] = Field(
        default=None, description="True if the unit or compound has a swimming pool."
    )
    has_balcony: Optional[bool] = Field(
        default=None, description="True if the unit has a balcony."
    )
    city: Optional[str] = Field(
        default=None,
        description="City or governorate where the property is located (e.g. Cairo, Alexandria, New Cairo).",
    )
    district: Optional[str] = Field(
        default=None,
        description="Neighbourhood, district, or zone within the city (e.g. Maadi, Zamalek, Sheikh Zayed).",
    )
    compound_name: Optional[str] = Field(
        default=None,
        description="Name of the compound or gated community, if the property is inside one.",
    )
    landmark_proximity: Optional[str] = Field(
        default=None,
        description="Nearby landmark, road, or area mentioned to describe the location "
        "(e.g. 'near City Stars', 'Ring Road exit 5').",
    )
    down_payment: Optional[float] = Field(
        default=None,
        description="Initial down-payment amount in the stated currency, if an installment plan is offered.",
    )
    installment_years: Optional[float] = Field(
        default=None, description="Duration of the installment plan in years."
    )
    installment_amount: Optional[float] = Field(
        default=None,
        description="Periodic installment payment amount (monthly unless stated otherwise).",
    )
    phone_numbers: Optional[list[str]] = Field(
        default=None,
        description="All phone/WhatsApp numbers found in the ad. Preserve the original format exactly.",
    )
    reference_id: Optional[str] = Field(
        default=None,
        description="Any internal listing code or reference number found in the ad (e.g. 'U926440', 'HPs160').",
    )
    view: Optional[str] = Field(
        default=None,
        description="What the unit overlooks or faces, as stated in the ad (e.g. 'pool view', 'garden', 'sea view').",
    )
    ad_snippet: Optional[str] = Field(
        default=None,
        description="Clean, standalone text of this specific listing only — no repeated contact lines, "
        "no other listings that appeared in the same message.",
    )
    original_message: Optional[str] = Field(
        default=None,
        description="The full, unmodified original message text that this listing was extracted from.",
    )

'''
Temporarily removed from prompt!!!

SCHEMA — every field is nullable (use null if not explicitly determinable):

{
  "property_type": "apartment|villa|studio|duplex|penthouse|chalet|townhouse|twin_house|standalone|i_villa|land|office|shop|warehouse|building|loft|other",
  "transaction_type": "sale|rent|daily_rent",
  "price": <number, EXPLICITLY stated total price. DO NOT calculate or add numbers together. No commas.>,
  "currency": "EGP|USD|EUR",
  "area_sqm": <number, BUA/built-up area in sqm>,
  "land_area_sqm": <number, land area if different from BUA>,
  "bedrooms": <int, studio=0>,
  "bathrooms": <int>,
  "floor_number": <int, ground=0>,
  "total_floors": <int>,
  "furnished": "furnished|semi_furnished|unfurnished",
  "finishing": "shell|core_and_shell|semi_finished|finished|luxury",
  "has_garden": <bool>,
  "garden_area_sqm": <number>,
  "has_pool": <bool>,
  "has_balcony": <bool>,
  "city": "<string>",
  "district": "<string, only if explicitly stated>",
  "compound_name": "<string, extract the project name exactly as written>",
  "landmark_proximity": "<string>",
  "down_payment": <number>,
  "installment_years": <number>,
  "installment_amount": <number>,
  "phone_numbers": [<strings, preserve original format>],
  "reference_id": "<string, any code like U926440 or HPs160>",
  "view": "<string, e.g. pool, garden, sea>",
  "ad_snippet": "<string, the clean ad text only, no duplicate contact lines or other ads from the same message>",
  "original_message": "<string, the full original message text>"
}

'''



SYSTEM_PROMPT = """You are a strict data extraction engine for Egyptian real estate advertisements. Your job is to extract text exactly as it appears. 

Extract structured data from each ad. Return a JSON array where each element corresponds to one ad.


STRICT ZERO-ASSUMPTION POLICY (CRITICAL RULES):
1. NO MATH OR CALCULATIONS: If a total price is not explicitly written, set "price" to null. DO NOT add "down payment" and "remaining" together to guess the price.
2. NO PROPERTY TYPE INFERENCE: Having a "land area", "BUA", "nanny room", or "Type M" does NOT automatically mean the property is a villa, standalone, or townhouse. If the specific word (e.g., "villa") is not in the text, you MUST set "property_type" to null.
3. NO GEOGRAPHICAL ASSUMPTIONS: Do not use external knowledge to guess the city or district. If the text says "Badya PalmHills", map it to "compound_name" and leave "district" and "city" as null unless explicitly stated in the text.
4. NO IMPLICIT FEATURES: A "Land: 275" does not automatically mean "has_garden": true. Only mark true if the word garden is mentioned.
5. If a single AD block contains multiple distinct listings, return one JSON object per listing.
6. Default currency is EGP unless stated otherwise.
7. "super lux" or "الترا سوبر لوكس" = luxury finishing. "لوكس" alone = finished.
8. Prices with commas like "35.000" in a rental context mean 35,000 (not 35).

Return ONLY valid JSON. No markdown, no explanation, no thinking output."""


def build_extraction_prompt(ads: list[dict]) -> str:
    parts = []
    for i, ad in enumerate(ads, 1):
        parts.append(
            f"--- AD {i} (from: {ad['sender']}, date: {ad['datetime'].isoformat()}) ---"
        )
        parts.append(ad["body"])
        parts.append("")
    return "\n".join(parts)


def call_gemini(ads: list[dict]) -> tuple[list[dict], dict]:
    """Call Gemini to extract structured data. Returns (results, timing_info)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    user_prompt = build_extraction_prompt(ads)
    timing = {"api_call_s": None, "json_parse_s": None, "attempts": 0}

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
                    response_schema=list[ListingExtraction],
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=-1,
                        include_thoughts=True,
                    ),
                ),
            )
            timing["api_call_s"] = _elapsed(t_api)

            if DEBUG_MODEL:
                for part in response.candidates[0].content.parts:
                    if getattr(part, "thought", False):
                        print(f"\n── Thinking {'─'*50}\n{part.text}\n{'─'*60}")
                    else:
                        print(f"\n── Response {'─'*50}\n{part.text}\n{'─'*60}")
                return [], timing  # halt — do not parse or insert

            t_parse = _ts()
            parsed: list[ListingExtraction] = response.parsed
            timing["json_parse_s"] = _elapsed(t_parse)

            if isinstance(parsed, ListingExtraction):
                parsed = [parsed]
            return [p.model_dump() for p in parsed], timing

        except Exception as e:
            print(f"  [!] API error (attempt {attempt+1}): {e}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(2**attempt)

    print("  [!] Failed after all retries, skipping batch.")
    return [], timing



# ─── 5. Database ─────────────────────────────────────────────────────────────


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        """
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
            ad_snippet TEXT,
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
    """
    )
    conn.commit()
    # Migrate existing databases that predate ad_snippet
    try:
        conn.execute("ALTER TABLE listings ADD COLUMN ad_snippet TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists
    return conn


def insert_listing(
    conn: sqlite3.Connection, data: dict, original_msg: str, sender: str, ad_date: str
):
    phones = json.dumps(data.get("phone_numbers") or [], ensure_ascii=False)
    conn.execute(
        """
        INSERT INTO listings (
            property_type, transaction_type, price, currency,
            area_sqm, land_area_sqm, bedrooms, bathrooms,
            floor_number, total_floors, furnished, finishing,
            has_garden, garden_area_sqm, has_pool, has_balcony,
            city, district, compound_name, landmark_proximity,
            down_payment, installment_years, installment_amount,
            phone_numbers, reference_id,
            confidence_score, language, view,
            original_message, ad_snippet, sender, ad_date, extraction_method
        ) VALUES (
            ?,?,?,?,  ?,?,?,?,  ?,?,?,?,
            ?,?,?,?,
            ?,?,?,?,  ?,?,?,
            ?,?,  ?,?,?,
            ?,?,?,?,?
        )
    """,
        (
            data.get("property_type"),
            data.get("transaction_type"),
            data.get("price"),
            data.get("currency", "EGP"),
            data.get("area_sqm"),
            data.get("land_area_sqm"),
            data.get("bedrooms"),
            data.get("bathrooms"),
            data.get("floor_number"),
            data.get("total_floors"),
            data.get("furnished"),
            data.get("finishing"),
            _b(data.get("has_garden")),
            data.get("garden_area_sqm"),
            _b(data.get("has_pool")),
            _b(data.get("has_balcony")),
            data.get("city"),
            data.get("district"),
            data.get("compound_name"),
            data.get("landmark_proximity"),
            data.get("down_payment"),
            data.get("installment_years"),
            data.get("installment_amount"),
            phones,
            data.get("reference_id"),
            data.get("confidence_score"),
            data.get("language"),
            data.get("view"),
            original_msg,
            data.get("ad_snippet"),
            sender,
            ad_date,
            GEMINI_MODEL,
        ),
    )


def _b(val) -> Optional[int]:
    return None if val is None else (1 if val else 0)


# ─── 6. Main Pipeline ────────────────────────────────────────────────────────


def run_pipeline(chat_file: str, days: int = 2):
    run_start = _ts()
    run_ts = datetime.now().isoformat(timespec="seconds")

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
    target_date = f"{target_dates[0]} → {target_dates[-1]}" if target_dates else "N/A"
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

    # ── Build batches ──────────────────────────────────────────
    ads_avg       = compute_ads_avg(ads)
    batches       = build_batches(ads, ads_avg)
    total_batches = len(batches)
    oversized_cnt = sum(1 for b in batches if b.is_oversized)
    print(f"\n      Batches built : {total_batches}  ({oversized_cnt} oversized)")

    # ── Step 4: Gemini extraction ──────────────────────────────
    print(f"\n[4/5] Extracting via {GEMINI_MODEL}...")
    conn          = init_db()
    total_inserted = 0
    batch_timings  = []

    t_extraction = _ts()
    for batch_num, batch_obj in enumerate(batches, 1):
        batch = batch_obj.messages

        # ── Batch header line ──────────────────────────────────
        oversized_flag = "  ⚠ OVERSIZED" if batch_obj.is_oversized else ""
        print(
            f"      Batch {batch_num}/{total_batches} "
            f"({len(batch)} msg(s), ~{batch_obj.estimated_ads} ads, "
            f"{batch_obj.total_chars} chars, "
            f"~{batch_obj.estimated_tokens} tokens)"
            f"{oversized_flag}...",
            end=" ", flush=True
        )

        t_batch = _ts()
        results, bt = call_gemini(batch)
        batch_total = _elapsed(t_batch)

        t_db = _ts()
        for result in results:
            orig = result.get("original_message") or ""
            ad = next((a for a in batch if a["body"].strip() == orig.strip()), None)
            insert_listing(
                conn,
                result,
                original_msg=orig,
                sender=ad["sender"] if ad else None,
                ad_date=ad["datetime"].isoformat() if ad else None,
            )
            total_inserted += 1
        conn.commit()
        db_s = _elapsed(t_db)

        bt.update(
            batch_num=batch_num,
            ads_in=len(batch),
            ads_out=len(results),
            db_insert_s=db_s,
            batch_total_s=batch_total,
        )
        batch_timings.append(bt)

        api_s = _fmt(bt["api_call_s"]) if bt["api_call_s"] else "err"
        parse_s = _fmt(bt["json_parse_s"]) if bt["json_parse_s"] else "err"
        print(
            f"OK ({len(results)} extracted) | total={_fmt(batch_total)} api={api_s} json={parse_s} db={_fmt(db_s)}"
        )

        if batch_num < total_batches:
            time.sleep(1)

    timings["extraction_s"] = _elapsed(t_extraction)
    timings["total_s"] = _elapsed(run_start)

    # ── Step 5: Summary ────────────────────────────────────────
    print(f"\n[5/5] Done!")
    print(f"      Listings saved : {total_inserted}")
    print(f"      Database       : {os.path.abspath(DB_PATH)}")
    print(f"\n  ── Timings ──────────────────────────────────────────")
    print(f"      Parse          : {_fmt(timings['parse_s'])}")
    print(f"      Day select     : {_fmt(timings['day_filter_s'])}")
    print(f"      Ad filter      : {_fmt(timings['ad_filter_s'])}")
    print(
        f"      Gemini total   : {_fmt(timings['extraction_s'])}  ({total_batches} batches)"
    )
    if batch_timings:
        valid = [b for b in batch_timings if b["api_call_s"]]
        if valid:
            print(
                f"      Avg API/batch  : {_fmt(sum(b['api_call_s'] for b in valid) / len(valid))}"
            )
        print(
            f"      Avg total/batch: {_fmt(sum(b['batch_total_s'] for b in batch_timings) / len(batch_timings))}"
        )
    print(f"      TOTAL          : {_fmt(timings['total_s'])}")
    print(f"  ─────────────────────────────────────────────────────")

    cursor = conn.execute(
        """
        SELECT property_type, COUNT(*) FROM listings
        WHERE property_type IS NOT NULL
        GROUP BY property_type ORDER BY 2 DESC
    """
    )
    prop_types = {r[0]: r[1] for r in cursor}
    print(f"\n      Property types:")
    for k, v in prop_types.items():
        print(f"        {k}: {v}")

    cursor = conn.execute("SELECT AVG(confidence_score) FROM listings")
    avg_conf = cursor.fetchone()[0]
    if avg_conf:
        print(f"      Avg confidence : {avg_conf:.2f}")

    conn.close()

    # ── Log run ────────────────────────────────────────────────
    _log({
        "run_at": run_ts,
        "model": GEMINI_MODEL,
        "input_file": chat_file,
        "days_requested": days,
        "target_dates": [str(d) for d in target_dates],
        "total_messages": len(messages),
        "day_messages": len(day_messages),
        "filter_stats": fstats,
        "ads_processed": len(ads),
        "batches_total": total_batches,
        "batches_oversized": oversized_cnt,
        "listings_inserted": total_inserted,
        "avg_confidence": round(avg_conf, 4) if avg_conf else None,
        "property_type_counts": prop_types,
        "timings": {k: round(v, 3) for k, v in timings.items()},
        "batches": [{
            "batch":            b["batch_num"],
            "ads_in":           b["ads_in"],
            "ads_out":          b["ads_out"],
            "api_call_s":       round(b["api_call_s"],   3) if b["api_call_s"]   else None,
            "json_parse_s":     round(b["json_parse_s"], 4) if b["json_parse_s"] else None,
            "db_insert_s":      round(b["db_insert_s"],  4),
            "batch_total_s":    round(b["batch_total_s"],3),
            "attempts":         b["attempts"],
        } for b in batch_timings],
    })
    print(f"\n      Run logged → {os.path.abspath(LOG_PATH)}")
# ─── Entry point ─────────────────────────────────────────────────────────────

chat_file = "Backupz/2days_53_messages.txt"
run_pipeline(chat_file, 3)
# crop_chat_by_date(chat_file, 28, 9, 2024, 28, 9, 2024)

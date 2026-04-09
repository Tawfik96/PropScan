"""
Improved System Prompt + Pipeline Optimizations
================================================
Drop-in replacements for CompactExtractFromChatTest.py

Changes:
  1. Expanded SYSTEM_PROMPT with few-shot examples (~1200-1500 tokens)
     → improves extraction accuracy on edge cases
     → long enough to trigger implicit caching (min 1024 tokens for 2.5 Flash-Lite)
  2. Implicit cache monitoring — logs cached_content_token_count per batch
  3. Better Pydantic schema with tighter field descriptions
  4. Hardened call_gemini with usage/cost tracking per batch
  5. No explicit caching needed (implicit is free + automatic)

Cost impact:
  Old prompt ~500 tokens  → $0.00005 / batch at $0.10/1M
  New prompt ~1400 tokens → $0.00014 / batch at $0.10/1M
  Delta: $0.00009 / batch — effectively free, but quality improves significantly.
"""

import re
import os
import json
import sqlite3
import time
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from analysis import open_analysis_log

DB_PATH = "DBwithSenderadDate_Taw_Generated2.db"

# ══════════════════════════════════════════════════════════════════════════════
#  IMPROVED PYDANTIC SCHEMA
# ══════════════════════════════════════════════════════════════════════════════
# Key changes:
#   - Tighter descriptions that act as mini-instructions for the model
#   - price description explicitly forbids computing totals
#   - ad_snippet description clarifies what to include/exclude
#   - compound_name description lists common Egyptian formats


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
            "i_villa",
            "land",
            "office",
            "shop",
            "warehouse",
            "building",
            "loft",
            "other",
        ]
    ] = Field(
        default=None,
        description=(
            "The property type word MUST appear explicitly in the ad text. "
            "If no property type word is found, return null. "
            "If a word appears but is not in the enum, return 'other'."
        ),
    )
    transaction_type: Optional[Literal["sale", "rent"]] = Field(
        default="sale",
        description=(
            "Whether the property is for sale or rent. "
            "Keywords: بيع/sale/for sale/resale → 'sale'. "
            "إيجار/rent/for rent/monthly → 'rent'. "
            "If unclear, return null."
        ),
    )
    price: Optional[float] = Field(
        default=None,
        description=(
            "Total asking price. Compute in this priority order:\n"
            "1. Explicit total stated → use it directly.\n"
            "2. Deposit (مقدم) + remaining lump sum (متبقي) both stated → price = deposit + remaining.\n"
            "3. Deposit + installment amount + installment count both stated → price = deposit + (amount × count). "
            "Convert years to months (× 12): '10 سنوات' = 120 months, '5 سنين' = 60 months.\n"
            "4. Installment amount + installment count stated (no deposit) → price = amount × count.\n"
            "5. Deposit only, or installment amount with NO count/period → null.\n"
            "Normalize: '4.5M' / '4.5 مليون' → 4500000. '800k' → 800000. "
            "'35.000' in rent context → 35000 (period = thousands separator)."
        ),
    )
    down_payment: Optional[float] = Field(
        default=None,
        description=(
            "The initial deposit / down payment only, as a plain number. "
            "Keywords: مقدم / down payment / DP / advance. "
            "Normalize the same way as price. "
            "Return null if no deposit is mentioned separately from the total price."
        ),
    )
    currency: Literal["EGP", "USD", "EUR", "other"] = Field(
        default="EGP",
        description=(
            "Currency of the price. "
            "جنيه/EGP/ج.م → 'EGP'. دولار/USD/$ → 'USD'. يورو/EUR/€ → 'EUR'. "
            "ALWAYS output 'EGP' when no currency symbol is mentioned. Never output null."
        ),
    )

    @field_validator("currency", mode="before")
    @classmethod
    def _coerce_currency(cls, v):
        return v if v is not None else "EGP"


    bedrooms: Optional[int] = Field(
        default=None,
        description=(
            "Number of bedrooms. Use 0 for studios. "
            "Extract from patterns like '3 غرف', '2BR', '3 bedrooms', '3 نوم'. "
            "If not stated, return null."
        ),
    )
    compound_name: Optional[str] = Field(
        default=None,
        description=(
            "Name of the compound, gated community, or development project in English. "
            "Common formats: 'Madinaty', 'Palm Hills', 'Mountain View', 'Hyde Park', etc.. "
            "Translate arabic compound names to English (e.g. 'مدينتي' → 'Madinaty', 'هايد بارك' → 'Hyde Park'). "
            "If the property is not in a compound, return null."
        ),
    )
    city: Optional[str] = Field(
        default=None,
        description=(
            "The city where the property is located, always in English. "
            "If its explicitly mentioned, extract directly and translate it in English"
            "If not explicitly mentioned, predict from context when possible "
            "Examples: Cairo, Alexandria, New Cairo, 6th of October City, North Coast, etc. "
            "Return null only if truly uninferable."
        ),
    )
    district: Optional[str] = Field(
        default=None,
        description=(
            "The district, neighborhood, or sub-area within the city, always in English. "
            "Extract directly if explicitly mentioned"
            "If not stated, infer from compound/context"
            "Examples: 5th Settlement, Maadi, Zamalek, Nasr City, Misr El-Gedida, etc. "
            "Return null if uninferable."
        ),
    )
    ad_snippet: Optional[str] = Field(
        default=None,
        description=(
            "A clean, standalone excerpt of THIS specific listing only. "
            "Include: property details, location, price, size. "
            "Exclude: phone numbers, repeated contact lines, other listings "
            "from the same message, emojis, decorative characters."
        ),
    )
    ad_index: int = Field(
        description=(
            "The integer N from the '--- AD N ---' header this listing was "
            "extracted from. If one AD contains multiple listings, all share "
            "the same ad_index."
        ),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  IMPROVED SYSTEM PROMPT — with few-shot examples
# ══════════════════════════════════════════════════════════════════════════════
# Design principles:
#   1. Role + task in first sentence (prefix stays constant → implicit caching)
#   2. Rules ordered by frequency of violation
#   3. Few-shot examples cover the hardest edge cases:
#      - Price normalization (millions, thousands separator)
#      - Multi-listing in one AD block
#      - Missing fields → null (not guessed)
#      - Down payment only → price null
#   4. ~1400 tokens → above the 1024 implicit caching threshold

SYSTEM_PROMPT = """You are a strict data-extraction engine for Egyptian real estate ads from WhatsApp group chats.

<task>
For each AD block in the user prompt, extract structured listings. Return a JSON array where each element is one listing. If a single AD contains multiple distinct properties, return one object per property, all sharing the same ad_index.
</task>

<rules>
1. EXTRACT ONLY WHAT IS WRITTEN. Never infer or assume.
2. NO TYPE GUESSING: If no property-type word appears in the text, set property_type to null.
3. ad_index must match the integer N from "--- AD N ---".
4. CURRENCY: ALWAYS output "EGP" unless another currency (USD, EUR, etc.) is explicitly stated. Return null ONLY if two or more different currencies appear in the same ad making it ambiguous which applies to the price.
5. PRICE COMPUTATION — compute total price whenever possible:
   a. Explicit total stated → use directly.
   b. مقدم (lump) + متبقي (lump) both stated → price = مقدم + متبقي.
   c. مقدم + installment amount + installment count/period all stated → price = مقدم + (amount × months). Convert years × 12 (e.g. "10 سنوات" = 120 months, "5 سنين" = 60 months).
   d. Installment amount + count/period (no مقدم) → price = amount × months.
   e. Only مقدم with no other info, or installment with NO count/period → price = null.
   Examples: مقدم 500,000 + 15,000/month × 8 years → price = 500000 + (15000 × 96) = 1940000. 10,000/month × 5 years → price = 600000.
6. Prices with period as thousands separator (e.g. "35.000" for rent) → 35000.
7. Normalize shorthand: "4.5M" or "4.5 مليون" → 4500000. "800k" → 800000.
8. For bedrooms: "استوديو" or "studio" → 0. "3 غرف" → 3.
9. COMPOUND NAME — MUST always be in English. NEVER output Arabic characters in compound_name. Translate: "مدينتي" → "Madinaty", "هايد بارك" → "Hyde Park", "بالم هيلز" → "Palm Hills", "ماونتن فيو" → "Mountain View", "الرحاب" → "Rehab City", "ميفيدا" → "Mivida", "تاج سيتي" → "Taj City". For any other Arabic name, transliterate to English characters. If no compound, return null.
10. CITY: Extract the city if explicitly mentioned (القاهرة/Cairo → "Cairo", الإسكندرية → "Alexandria", 6 أكتوبر → "6th of October City"). If not stated, predict from context: Madinaty/Hyde Park/Rehab/التجمع/الرحاب → "New Cairo"; Palm Hills October/Badya/الشيخ زايد → "6th of October City"; الساحل الشمالي/North Coast → "North Coast". Always in English. Return null only if truly cannot be determined.
11. DISTRICT: Extract the district/neighborhood if explicitly mentioned (التجمع الخامس → "5th Settlement", المعادي → "Maadi", الزمالك → "Zamalek", مدينة نصر → "Nasr City"). If not stated, infer from compound/area: Madinaty/Hyde Park/Rehab → "5th Settlement". Always in English. Return null if cannot be determined.
12. Return ONLY the JSON array. No markdown, no explanation.
</rules>

<examples>

INPUT:
--- AD 1 (from: Ahmed, date: 2025-03-01T10:00:00) ---
شقه للبيع في مدينتي B12
3 غرف 150 متر
السعر 4.5 مليون

OUTPUT:
[{"property_type": "apartment", "transaction_type": "sale", "price": 4500000, "currency": "EGP", "bedrooms": 3, "compound_name": "Madinaty", "city": "New Cairo", "district": "5th Settlement", "ad_snippet": "شقه للبيع في مدينتي B12 3 غرف 150 متر السعر 4.5 مليون", "ad_index": 1}]

INPUT:
--- AD 2 (from: Sara, date: 2025-03-01T11:00:00) ---
للإيجار فيلا توين هاوس هايد بارك التجمع
4 غرف + حديقه
الإيجار 35.000 شهري

OUTPUT:
[{"property_type": "twin_house", "transaction_type": "rent", "price": 35000, "currency": "EGP", "bedrooms": 4, "compound_name": "Hyde Park", "city": "New Cairo", "district": "5th Settlement", "ad_snippet": "للإيجار فيلا توين هاوس هايد بارك التجمع 4 غرف + حديقه الإيجار 35.000 شهري", "ad_index": 2}]

NOTE on AD 2: city predicted from "التجمع" (5th Settlement area = New Cairo). district extracted directly from "التجمع".

INPUT:
--- AD 3 (from: Broker, date: 2025-03-01T12:00:00) ---
مقدم 500 الف وقسط 15 الف
بالم هيلز أكتوبر
استلام فوري

OUTPUT:
[{"property_type": null, "transaction_type": "sale", "price": null, "currency": "EGP", "bedrooms": null, "compound_name": "Palm Hills", "city": "6th of October City", "district": null, "ad_snippet": "مقدم 500 الف وقسط 15 الف بالم هيلز أكتوبر استلام فوري", "ad_index": 3}]

NOTE on AD 3: price is null — installment amount given (15,000) but NO time period/count stated, so total cannot be computed. property_type is null because no type word appears.

INPUT:
--- AD 4 (from: Ali, date: 2025-03-01T13:00:00) ---
متاح شقه 120م بادية بالم هيلز 2 غرف بسعر 3.2M
وفيلا standalone 300م ب 12 مليون في نفس المشروع

OUTPUT:
[{"property_type": "apartment", "transaction_type": null, "price": 3200000, "currency": "EGP", "bedrooms": 2, "compound_name": "Badya Palm Hills", "city": "6th of October City", "district": null, "ad_snippet": "شقه 120م بادية بالم هيلز 2 غرف بسعر 3.2M", "ad_index": 4}, {"property_type": "standalone", "transaction_type": null, "price": 12000000, "currency": "EGP", "bedrooms": null, "compound_name": "Badya Palm Hills", "city": "6th of October City", "district": null, "ad_snippet": "فيلا standalone 300م ب 12 مليون في نفس المشروع", "ad_index": 4}]

NOTE on AD 4: Two listings from one AD block — both share ad_index 4. transaction_type is null because neither "بيع" nor "إيجار" appears. city predicted from "بادية بالم هيلز" (Badya is in 6th of October City).

INPUT:
--- AD 5 (from: Agent, date: 2025-03-01T14:00:00) ---
تاون هاوس باديا بالم هيلز استلام فوري
3 غرف نوم
مقدم: 9,000,000 شامل الصيانة
متبقي: 640,000

OUTPUT:
[{"property_type": "townhouse", "transaction_type": "sale", "price": 9640000, "down_payment": 9000000, "currency": "EGP", "bedrooms": 3, "compound_name": "Badya Palm Hills", "city": "6th of October City", "district": null, "ad_snippet": "تاون هاوس باديا بالم هيلز استلام فوري 3 غرف نوم مقدم: 9,000,000 شامل الصيانة متبقي: 640,000", "ad_index": 5}]

NOTE on AD 5: Both deposit and remaining are plain lump sums → price = 9,000,000 + 640,000 = 9,640,000. down_payment = 9,000,000. currency defaults to EGP because no currency symbol appears.

INPUT:
--- AD 6 (from: Hana, date: 2025-03-01T15:00:00) ---
شقة للإيجار في الزمالك، القاهرة
2 غرف + صالة 110م
الإيجار 18000 جنيه شهري

OUTPUT:
[{"property_type": "apartment", "transaction_type": "rent", "price": 18000, "currency": "EGP", "bedrooms": 2, "compound_name": null, "city": "Cairo", "district": "Zamalek", "ad_snippet": "شقة للإيجار في الزمالك، القاهرة 2 غرف + صالة 110م الإيجار 18000 جنيه شهري", "ad_index": 6}]

NOTE on AD 6: city "Cairo" extracted directly from "القاهرة". district "Zamalek" extracted directly from "الزمالك". No compound mentioned → null.

INPUT:
--- AD 7 (from: Karim, date: 2025-03-01T16:00:00) ---
شقة للبيع التجمع الخامس بدون كمباوند
3 نوم 160م
السعر 5.2M

OUTPUT:
[{"property_type": "apartment", "transaction_type": "sale", "price": 5200000, "currency": "EGP", "bedrooms": 3, "compound_name": null, "city": "New Cairo", "district": "5th Settlement", "ad_snippet": "شقة للبيع التجمع الخامس بدون كمباوند 3 نوم 160م السعر 5.2M", "ad_index": 7}]

NOTE on AD 7: district "5th Settlement" extracted directly from "التجمع الخامس". city "New Cairo" predicted from that district. compound_name is null — text explicitly says "بدون كمباوند" (no compound).

INPUT:
--- AD 8 (from: Sales, date: 2025-03-01T17:00:00) ---
شقة في بالم هيلز أكتوبر
2 غرف 110م
مقدم 600,000
وقسط 12,000 شهري لمدة 8 سنوات

OUTPUT:
[{"property_type": "apartment", "transaction_type": "sale", "price": 1752000, "down_payment": 600000, "currency": "EGP", "bedrooms": 2, "compound_name": "Palm Hills", "city": "6th of October City", "district": null, "ad_snippet": "شقة في بالم هيلز أكتوبر 2 غرف 110م مقدم 600,000 وقسط 12,000 شهري لمدة 8 سنوات", "ad_index": 8}]

NOTE on AD 8: price = مقدم + (installment × months) = 600,000 + (12,000 × 96) = 600,000 + 1,152,000 = 1,752,000. 8 سنوات = 8 × 12 = 96 months. down_payment = 600,000.

INPUT:
--- AD 9 (from: Dev, date: 2025-03-01T18:00:00) ---
وحدة تجارية ميفيدا القاهرة الجديدة
أقساط 25,000 شهري على 5 سنوات بدون مقدم

OUTPUT:
[{"property_type": "shop", "transaction_type": "sale", "price": 1500000, "down_payment": null, "currency": "EGP", "bedrooms": null, "compound_name": "Mivida", "city": "New Cairo", "district": "5th Settlement", "ad_snippet": "وحدة تجارية ميفيدا القاهرة الجديدة أقساط 25,000 شهري على 5 سنوات بدون مقدم", "ad_index": 9}]

NOTE on AD 9: price = installment × months = 25,000 × 60 = 1,500,000. No مقدم → down_payment null. "ميفيدا" → "Mivida" (compound_name must be English).

</examples>"""


# ══════════════════════════════════════════════════════════════════════════════
#  IMPROVED build_extraction_prompt
# ══════════════════════════════════════════════════════════════════════════════
# Change: cleaner separator, no trailing blank line


def build_extraction_prompt(ads: list[dict]) -> str:
    parts = []
    for i, ad in enumerate(ads, 1):
        parts.append(
            f"--- AD {i} (from: {ad['sender']}, date: {ad['datetime'].isoformat()}) ---"
        )
        parts.append(ad["body"])
    return "\n".join(parts)


# Helper to update progress
def update_progress_file(current, total, status="Processing", reset=False):
    if reset:
        progress_data = {"current": 0, "total": 0, "percentage": 0, "status": "", "done": False}
    else:
        done = (total > 0 and current >= total)
        progress_data = {
            "current": current,
            "total": total,
            "percentage": round((current / total) * 100) if total > 0 else 0,
            "status": status,
            "done": done
        }
    with open("progress.json", "w") as f:
        json.dump(progress_data, f)


# ══════════════════════════════════════════════════════════════════════════════
#  IMPROVED call_gemini — with usage tracking & implicit cache monitoring
# ══════════════════════════════════════════════════════════════════════════════


GEMINI_MODEL = "gemini-2.5-flash-lite"

# Pricing per 1M tokens
PRICE_INPUT = 0.10
PRICE_CACHED_READ = 0.01  # 90% off input for cached tokens
PRICE_OUTPUT = 0.40  # includes thinking
MAX_RETRIES = 3


def call_gemini(
    ads: list[dict], client, debug: bool = False
) -> tuple[list[dict], dict]:
    """
    Call Gemini to extract structured data.
    Returns (results, info) where info includes timing + token usage + cost.
    """
    from google.genai import types

    user_prompt = build_extraction_prompt(ads)

    info = {
        "api_call_s": None,
        "json_parse_s": None,
        "attempts": 0,
        # Token counts
        "input_tokens": 0,
        "cached_tokens": 0,
        "output_tokens": 0,
        "thinking_tokens": 0,
        "total_tokens": 0,
        # Costs
        "cost_input": 0.0,
        "cost_cached": 0.0,
        "cost_output": 0.0,
        "cost_thinking": 0.0,
        "cost_total": 0.0,
    }

    for attempt in range(MAX_RETRIES):
        info["attempts"] = attempt + 1
        try:
            t_api = time.perf_counter()
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.5, #testing mid range temp
                    response_mime_type="application/json",
                    response_schema=list[ListingExtraction],
                    # thinking_config=types.ThinkingConfig(
                    #     thinking_budget=0,
                    #     include_thoughts=True,
                    # ),
                ),
            )
            info["api_call_s"] = time.perf_counter() - t_api

            # ── Extract usage metadata ─────────────────────────────
            u = response.usage_metadata
            cached = getattr(u, "cached_content_token_count", 0) or 0
            inp = u.prompt_token_count or 0
            out = u.candidates_token_count or 0
            thinking = getattr(u, "thoughts_token_count", 0) or 0
            total = u.total_token_count or 0

            info["input_tokens"] = inp
            info["cached_tokens"] = cached
            info["output_tokens"] = out
            info["thinking_tokens"] = thinking
            info["total_tokens"] = total

            # ── Compute costs ──────────────────────────────────────
            fresh_input = inp - cached
            info["cost_input"] = (fresh_input / 1e6) * PRICE_INPUT
            info["cost_cached"] = (cached / 1e6) * PRICE_CACHED_READ
            info["cost_output"] = (out / 1e6) * PRICE_OUTPUT
            info["cost_thinking"] = (thinking / 1e6) * PRICE_OUTPUT
            info["cost_total"] = (
                info["cost_input"]
                + info["cost_cached"]
                + info["cost_output"]
                + info["cost_thinking"]
            )

            if debug:
                for part in response.candidates[0].content.parts:
                    kind = "THINKING" if getattr(part, "thought", False) else "TEXT"
                    print(f"\n── {kind} {'─'*50}\n{part.text}\n{'─'*60}")
                return [], info, None

            # ── Parse ──────────────────────────────────────────────
            t_parse = time.perf_counter()
            parsed = response.parsed
            info["json_parse_s"] = time.perf_counter() - t_parse

            if isinstance(parsed, ListingExtraction):
                parsed = [parsed]
            return [p.model_dump() for p in parsed], info, response

        except Exception as e:
            print(f"  [!] API error (attempt {attempt+1}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2**attempt)

    print("  [!] Failed after all retries, skipping batch.")
    return [], info, None


# ══════════════════════════════════════════════════════════════════════════════
#  ENHANCED PIPELINE RUNNER  (drop-in replacement for run_pipeline)
# ══════════════════════════════════════════════════════════════════════════════
# Key improvements:
#   - Tracks per-batch token usage and cost
#   - Reports implicit cache hit rates
#   - Prints total cost summary at the end


def run_pipeline_improved(chat_file: str, days: int = 2):
    """
    Enhanced pipeline with per-batch cost tracking and cache monitoring.

    To use: replace the last lines of CompactExtractFromChatTest.py with:
        from improved_prompt import run_pipeline_improved
        run_pipeline_improved("a_custom_test1message_.txt", 8)
    """
    from google import genai
    from filter_chat import parse_whatsapp_export, classify
    from dotenv import load_dotenv

    load_dotenv()

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    run_start = time.perf_counter()
    run_ts = datetime.now().isoformat(timespec="seconds")

    print(f"{'='*70}")
    print(f"  Real Estate Ad Extraction Pipeline (IMPROVED)")
    print(f"  {run_ts}  |  {GEMINI_MODEL}  |  Days: {days}")
    print(f"{'='*70}\n")

    # ── Step 1: Parse ──────────────────────────────────────────
    messages = parse_whatsapp_export(chat_file)
    print(f"[1/5] Parsed {len(messages)} messages")

    if not messages:
        print("      No messages found.")
        return

    dates = sorted(set(m["datetime"].date() for m in messages))
    print(f"      Date range: {dates[0]} → {dates[-1]}")

    # ── Step 2: Select target days ─────────────────────────────
    day_messages = _get_recent_days(messages, days)
    target_dates = sorted(set(m["datetime"].date() for m in day_messages))
    print(
        f"\n[2/5] Target: {target_dates[0]} → {target_dates[-1]}  ({len(day_messages)} msgs)"
    )

    # ── Step 3: Filter ads ─────────────────────────────────────
    ads, fstats = _filter_ads(day_messages)
    print(f"\n[3/5] Filter: {fstats['passed']} ads from {len(day_messages)} messages")
    print(
        f"      Dropped: system={fstats['system']}  short={fstats['too_short']}  "
        f"blocklist={fstats['blocklist']}  no_kw={fstats['no_keywords']}"
    )

    if not ads:
        print("      No ads found.")
        return

    # ── Build batches ──────────────────────────────────────────
    try:
        from batch_messages import build_batches, compute_ads_avg

        ads_avg = compute_ads_avg(ads)
        batches = build_batches(ads, ads_avg)
        
    except ImportError:
        # Fallback: simple fixed-size batching
        BATCH_SIZE = 10
        batches = _simple_batches(ads, BATCH_SIZE)
        total_batches = len(batches)
    update_progress_file(0, len(batches), "Starting batches...")
    logger = open_analysis_log(run_ts, GEMINI_MODEL, len(batches), days, chat_file)
    print(f"      Batches: {len(batches)}")

    # ── Count system prompt tokens ─────────────────────────────
    try:
        count_resp = client.models.count_tokens(
            model=GEMINI_MODEL,
            contents=SYSTEM_PROMPT,
        )
        sys_tokens = count_resp.total_tokens
        print(
            f"\n  📏 System prompt: {sys_tokens:,} tokens "
            f"({'✅ above' if sys_tokens >= 1024 else '⚠️  below'} 1024 implicit cache threshold)"
        )
    except Exception:
        sys_tokens = None
        print(f"\n  📏 System prompt: (could not count tokens)")

    # ── Step 4: Extract ────────────────────────────────────────
    print(f"\n[4/5] Extracting via {GEMINI_MODEL}...")
    print(
        f"      {'Batch':>5}  {'Msgs':>4}  {'Extracted':>9}  "
        f"{'Input':>7}  {'Cached':>7}  {'Output':>7}  {'Think':>7}  "
        f"{'Cost':>10}  {'API Time':>8}"
    )
    print(
        f"      {'─'*5}  {'─'*4}  {'─'*9}  "
        f"{'─'*7}  {'─'*7}  {'─'*7}  {'─'*7}  "
        f"{'─'*10}  {'─'*8}"
    )

    # DB setup — compact schema matching GT format

    conn = _init_db(DB_PATH)
    total_inserted = 0
    all_info = []

    for batch_num, batch_obj in enumerate(batches, 1):
        update_progress_file(batch_num, len(batches), f"Processing batch {batch_num}...")

        # Support both the Batch object from batch_messages and plain lists
        if hasattr(batch_obj, "messages"):
            batch = batch_obj.messages
        else:
            batch = batch_obj

        t_batch = time.perf_counter()
        results, info, api_response = call_gemini(batch, client)
        batch_total=time.perf_counter()-t_batch

        all_info.append(info)

        # Insert results
        for result in results:
            idx = result.get("ad_index", 1) - 1
            ad = batch[idx] if 0 <= idx < len(batch) else None
            _insert_listing(
                conn,
                result,
                original_msg=ad["body"] if ad else "",
                sender=ad.get("sender") if ad else None,
                date=ad["datetime"].isoformat() if ad and ad.get("datetime") else None,
            )
            total_inserted += 1
        conn.commit()

        # Print row
        api_ms = f"{info['api_call_s']*1000:.0f}ms" if info["api_call_s"] else "err"
        cache_flag = " 💾" if info["cached_tokens"] > 0 else ""
        print(
            f"      {batch_num:>5}  {len(batch):>4}  {len(results):>9}  "
            f"{info['input_tokens']:>7,}  {info['cached_tokens']:>7,}  "
            f"{info['output_tokens']:>7,}  {info['thinking_tokens']:>7,}  "
            f"${info['cost_total']:>9.6f}  {api_ms}{cache_flag}"
        )

        if batch_num < len(batches):
            time.sleep(1)

        logger.log_batch(
        batch_num=batch_num,
        total_batches=len(batches),
        batch=batch,
        results=results,
        batch_total_s=batch_total,
        api_response=api_response,
        api_s=info["api_call_s"] or 0.0, 
        estimated_ads=batch_obj.estimated_ads  
        )

    conn.close()
    update_progress_file(len(batches), len(batches), "Complete")


    # ── Step 5: Summary ────────────────────────────────────────
    total_time = time.perf_counter() - run_start

    total_input = sum(i["input_tokens"] for i in all_info)
    total_cached = sum(i["cached_tokens"] for i in all_info)
    total_output = sum(i["output_tokens"] for i in all_info)
    total_thinking = sum(i["thinking_tokens"] for i in all_info)
    total_cost = sum(i["cost_total"] for i in all_info)

    cache_pct = (total_cached / total_input * 100) if total_input > 0 else 0

    print(f"\n[5/5] {'='*60}")
    print(f"  Listings saved    : {total_inserted}")
    print(f"  Total time        : {total_time:.1f}s")
    print(f"  Database          : {os.path.abspath(DB_PATH)}")

    print(f"\n  ── Token Summary {'─'*42}")
    print(f"  Total input       : {total_input:>10,}")
    print(f"    of which cached : {total_cached:>10,}  ({cache_pct:.1f}%)")
    print(f"  Total output      : {total_output:>10,}")
    print(f"  Total thinking    : {total_thinking:>10,}")

    print(f"\n  ── Cost Summary {'─'*43}")
    cost_fresh = sum(i["cost_input"] for i in all_info)
    cost_cached = sum(i["cost_cached"] for i in all_info)
    cost_output = sum(i["cost_output"] for i in all_info)
    cost_thinking = sum(i["cost_thinking"] for i in all_info)
    print(f"  Fresh input       : ${cost_fresh:.8f}  (${PRICE_INPUT}/1M)")
    print(f"  Cached input      : ${cost_cached:.8f}  (${PRICE_CACHED_READ}/1M)")
    print(f"  Output            : ${cost_output:.8f}  (${PRICE_OUTPUT}/1M)")
    print(f"  Thinking          : ${cost_thinking:.8f}  (${PRICE_OUTPUT}/1M)")
    print(f"  TOTAL             : ${total_cost:.8f}")

    if total_cached > 0:
        savings = (total_cached / 1e6) * (PRICE_INPUT - PRICE_CACHED_READ)
        print(f"\n  💾 Implicit cache saved: ${savings:.8f}")
    else:
        print(f"\n  ℹ️  No implicit cache hits this run.")
        print(f"     This is normal for a single run or first run.")
        print(f"     Implicit caching activates when consecutive requests")
        print(f"     share the same prefix within a short time window.")

    # ── Property type breakdown ────────────────────────────────
    conn2 = sqlite3.connect(DB_PATH)
    cursor = conn2.execute(
        """
        SELECT property_type, COUNT(*) FROM listings
        WHERE property_type IS NOT NULL
        GROUP BY property_type ORDER BY 2 DESC
    """
    )
    prop_types = {r[0]: r[1] for r in cursor}
    conn2.close()

    if prop_types:
        print(f"\n  ── Property Types {'─'*41}")
        for k, v in prop_types.items():
            print(f"    {k}: {v}")

    print(f"\n{'='*70}")
    logger.finalize(
    total_inserted=total_inserted,
    fstats=fstats,
        )


# ── Internal helpers ──────────────────────────────────────────────────────────


def _init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS listings (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            property_type    TEXT,
            transaction_type TEXT,
            price            REAL,
            currency         TEXT,
            bedrooms         INTEGER,
            compound_name    TEXT,
            city             TEXT,
            district         TEXT,
            ad_snippet       TEXT,
            original_message TEXT,
            sender           TEXT,
            date             TEXT
        );
        """
    )
    conn.commit()
    return conn


def _insert_listing(conn: sqlite3.Connection, data: dict, original_msg: str, sender: str = None, date: str = None):
    price = data.get("price")
    # Always default to EGP; only null if model explicitly flagged multi-currency ambiguity.
    currency = data.get("currency") or "EGP"
    conn.execute(
        """
        INSERT INTO listings (
            property_type, transaction_type, price, currency,
            bedrooms, compound_name, city, district, ad_snippet, original_message,
            sender, date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("property_type"),
            data.get("transaction_type"),
            price,
            currency,
            data.get("bedrooms"),
            data.get("compound_name"),
            data.get("city"),
            data.get("district"),
            data.get("ad_snippet"),
            original_msg,
            sender,
            date,
        ),
    )


def _get_recent_days(messages, days):
    if not messages:
        return []
    dates = sorted(set(m["datetime"].date() for m in messages))
    target = set(dates[-days:])
    return [m for m in messages if m["datetime"].date() in target]


def _filter_ads(messages):
    from filter_chat import classify

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


class _SimpleBatch:
    def __init__(self, msgs):
        self.messages = msgs


def _simple_batches(ads, size):
    return [_SimpleBatch(ads[i : i + size]) for i in range(0, len(ads), size)]







if __name__ == "__main__":

    run_pipeline_improved(
        "SampleTextFiles/New50DayGTSample.txt",
        8,
    )

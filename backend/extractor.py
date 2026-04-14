"""
extractor.py
------------
Gemini API wrapper for structured real estate ad extraction.

Exports:
    GEMINI_MODEL       : model name string
    SYSTEM_PROMPT      : the full system prompt with few-shot examples
    build_extraction_prompt(ads) -> str
    call_gemini(ads, client, debug=False) -> (results, info, response)
"""

import time
from models import ListingExtraction
from config import GEMINI_MODEL, MAX_RETRIES, TEMPERATURE, PRICE_INPUT, PRICE_CACHED_READ, PRICE_OUTPUT


# ── System prompt ─────────────────────────────────────────────────────────────
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


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_extraction_prompt(ads: list[dict]) -> str:
    parts = []
    for i, ad in enumerate(ads, 1):
        parts.append(
            f"--- AD {i} (from: {ad['sender']}, date: {ad['datetime'].isoformat()}) ---"
        )
        parts.append(ad["body"])
    return "\n".join(parts)


# ── Gemini caller ─────────────────────────────────────────────────────────────

def call_gemini(
    ads: list[dict], client, debug: bool = False
) -> tuple[list[dict], dict, object]:
    """
    Call Gemini to extract structured listings from a batch of ads.

    Returns:
        results  : list of listing dicts (empty on failure)
        info     : timing, token counts, and cost breakdown
        response : raw Gemini response object (or None on failure)
    """
    from google.genai import types

    user_prompt = build_extraction_prompt(ads)

    info = {
        "api_call_s":      None,
        "json_parse_s":    None,
        "attempts":        0,
        "input_tokens":    0,
        "cached_tokens":   0,
        "output_tokens":   0,
        "thinking_tokens": 0,
        "total_tokens":    0,
        "cost_input":      0.0,
        "cost_cached":     0.0,
        "cost_output":     0.0,
        "cost_thinking":   0.0,
        "cost_total":      0.0,
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
                    temperature=TEMPERATURE,
                    response_mime_type="application/json",
                    response_schema=list[ListingExtraction],
                ),
            )
            info["api_call_s"] = time.perf_counter() - t_api

            # ── Extract usage metadata ─────────────────────────────────────
            u = response.usage_metadata
            cached   = getattr(u, "cached_content_token_count", 0) or 0
            inp      = u.prompt_token_count or 0
            out      = u.candidates_token_count or 0
            thinking = getattr(u, "thoughts_token_count", 0) or 0
            total    = u.total_token_count or 0

            info["input_tokens"]    = inp
            info["cached_tokens"]   = cached
            info["output_tokens"]   = out
            info["thinking_tokens"] = thinking
            info["total_tokens"]    = total

            # ── Compute costs ──────────────────────────────────────────────
            fresh_input = inp - cached
            info["cost_input"]    = (fresh_input / 1e6) * PRICE_INPUT
            info["cost_cached"]   = (cached     / 1e6) * PRICE_CACHED_READ
            info["cost_output"]   = (out        / 1e6) * PRICE_OUTPUT
            info["cost_thinking"] = (thinking   / 1e6) * PRICE_OUTPUT
            info["cost_total"]    = (
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

            # ── Parse ──────────────────────────────────────────────────────
            t_parse = time.perf_counter()
            parsed  = response.parsed
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

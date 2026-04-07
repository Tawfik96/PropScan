"""
filter_chat.py
--------------
Takes a WhatsApp .txt export and splits messages into:
  - Filtering_Ouput_Folder/<basename>_ads.txt      : messages that passed the filter
  - Filtering_Ouput_Folder/<basename>_filtered.txt : messages that were dropped and why

Usage:
    python filter_chat.py               (uses hardcoded filename at bottom)

Also importable by the pipeline:
    from filter_chat import parse_whatsapp_export, classify, WA_MSG_PATTERN
"""

import re
import os
from datetime import datetime

import batch_messages
# import batch_messages

# ─── WhatsApp message parser ──────────────────────────────────────────────────

WA_MSG_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+"
    r"(\d{1,2}:\d{2}(?::\d{2})?\s*[aApP][mM])"
    r"\s*-\s+"
    r"(.+?):\s+"
    r"([\s\S]*?)$"
)
WA_SYSTEM_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),?\s+"
    r"(\d{1,2}:\d{2}(?::\d{2})?\s*[aApP][mM])"
    r"\s*-\s+"
    r"([\s\S]*?)$"
)

# Datetime formats tried in order
_DT_FORMATS = [
    "%d/%m/%Y, %I:%M %p",  "%d/%m/%Y, %I:%M%p",
    "%d/%m/%y, %I:%M %p",  "%d/%m/%y, %I:%M%p",
    "%m/%d/%Y, %I:%M %p",  "%m/%d/%y, %I:%M %p",
    "%d/%m/%Y, %I:%M:%S %p",
]


def _parse_datetime(date_str: str, time_str: str) -> datetime:
    """Parse date + time strings into a real datetime object."""
    combined = f"{date_str}, {time_str}".strip()
    clean    = re.sub(r'[aApP][mM]', lambda x: x.group().upper(), combined)
    for fmt in _DT_FORMATS:
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {combined!r}")


def parse_whatsapp_export(filepath: str) -> list[dict]:
    """
    Parse a WhatsApp .txt export into a list of message dicts.

    Each dict has:
        datetime  : real datetime object  (needed by pipeline for date arithmetic)
        sender    : str
        body      : str
    """
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
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
            current = {
                "datetime": dt,
                "sender":   sender.strip(),
                "body":     body.strip(),
            }
        else:
            # System message line (timestamp but no "sender: body")
            s = WA_SYSTEM_PATTERN.match(line)
            if s:
                if current:
                    messages.append(current)
                date_str, time_str, body = s.groups()
                dt = _parse_datetime(date_str, time_str)
                current = {
                    "datetime": dt,
                    "sender":   "__system__",
                    "body":     body.strip(),
                }
            elif current:
                current["body"] += "\n" + line

    if current:
        messages.append(current)
    return messages


# ─── Filters ──────────────────────────────────────────────────────────────────

SYSTEM_RE = re.compile("|".join([
    r"Messages and calls are end-to-end encrypted",
    r"\badded\s+\+?\d", r"\bleft$", r"\bremoved\s+\+?\d",
    r"changed the subject", r"changed this group", r"changed the group",
    r"created group", r"joined using this group", r"security code changed",
    r"Your security code with", r"<[Mm]edia omitted>",
    r"image omitted", r"video omitted", r"audio omitted",
    r"sticker omitted", r"document omitted", r"Contact card omitted",
    r"GIF omitted", r"location:?\s*https?://",
    r"This message was deleted", r"You deleted this message",
    r"Missed voice call", r"Missed video call", r"^null$",
]), re.IGNORECASE)

BLOCKLIST_RE = re.compile("|".join([
    r"أبحث\s*عن|ابحث\s*عن", r"بدور\s*على|بدوّر\s*على",
    r"urgent\s*request",r"sale\s*request",
    r"محتاج\s*(شقة|شقه|فيلا|وحدة|وحده|أرض|ارض|محل)",
    r"محتاجة\s*(شقة|شقه|فيلا|وحدة|وحده|أرض|ارض|محل)",
    r"عايز\s*(أشتري|اشتري|اجار|ايجار|ايجاره)",
    r"عايزة\s*(أشتري|اشتري|اجار|ايجار|ايجاره)",
    r"urgent\s*request", r"\blooking\s+for\b",
    r"\bwanted\b.{0,40}\b(apartment|villa|flat|unit|land|office)\b",
    r"\b(3ayez|3ayz)\b",
    r"تمويلات?\s*بنكي", r"قرض\s*شخصي", r"كاش\s*باك",
    r"#.*تمويل", r"\busdt\b", r"\bbitcoin\b|\bcrypto\b|\berc20\b",
    r"we\s*are\s*hiring", r"sales\s*team\s*leader",
    r"chat\.whatsapp\.com", r"not\s*spam\s*please",
    r"ممنوع\s*الصور", r"سيتم\s*الحذف",
    r"^(السلام\s*عليكم|وعليكم\s*السلام|صباح\s*الخير|صباح\s*النور|مساء\s*الخير)\s*$",
    r"^good\s*(morning|evening|night)\s*$",
    r"^(hi|hello|hey|ok|okay|تمام|ماشي)\s*$",
    r"^\?\s*$",
]), re.IGNORECASE | re.MULTILINE)

STRONG_AD_RE = re.compile("|".join([
    r"\bfor\s*sale\b", r"\bfor\s*rent\b",
    r"للبيع", r"للايجار", r"للإيجار",
    r"\bresale\b", r"\blease\b",

    # price indicators
    r"\d+\s*(million|m|k|الف|مليون)",
    
    # property specs (strong signal it's an ad)
    r"\d+\s*(bed|bedroom|غرف|غرفة)",
    r"\d+\s*(sqm|m2|متر)",

]), re.IGNORECASE)

REQUEST_INTENT_RE = re.compile("|".join([
    r"مطلوب", r"المطلوب", r"محتاج", r"محتاجة", r"محتاجه",
    r"عايز", r"عايزة", r"عاوزه", r"عاوزة", r"عايزه", r"عاوز",
    r"اريد", r"أبحث\s*عن", r"ابحث\s*عن", r"بدور\s*على", r"بدوّر\s*على",
    r"need", r"looking\s*for", r"\bwanted\b",
    r"matloob", r"matloub", r"mtlob", r"matlob", r"2matlob", r"mtlb", "anyone", "any one", "ay had",
    "yb3tli", "send me", "looking for"
]), re.IGNORECASE)

_mataloub_terms = r"(?:مطلوب|المطلوب|محتاج|عايز|عايزةعاوزه|عاوزة|عايزه|عاوزه|عاوز|محتاجة|محتاجه|matloob|matloub|mtlob|matlob|2matlob|mtlb)"

# 2. Matches "Cash" or "Installments" (Taseet) in Arabic and Franco
_payment_terms = r"(?:\s+(?:كاش|cash|تقسيط|مقدم|downpayment|قسط|taseet|t2seet|3al\s+sneen))?"

# 3. Matches Numbers: Handles 1,234, 1.234, 1 234, and Arabic numerals ٦.٧٥٠.٠٠٠
# Also handles suffixes like "مليون" (million) or "الف" (thousand)
# Updated to catch "Mataloub Million"
_number_pattern = r"(?:\s*[:\-])?\s*(?:[\d\u0660-\u0669][\d\u0660-\u0669\s.,]*|مليون|الف)\s*(?:مليون|m|الف|k|egp|جنيه|ج\.م)?"

# Combine into a final pattern
PRICE_CONTEXT_RE = re.compile(
    rf"{_mataloub_terms}{_payment_terms}{_number_pattern}",
    re.IGNORECASE | re.UNICODE
)

_kw_all = sorted(set([
    "للبيع","للإيجار","للايجار","للاستثمار","إيجار","ايجار","بيع",
    "إيجار يومي","يومي","شهري","سنوي",
    "شقة","شقه","فيلا","فيللا","دوبلكس","دوبليكس","بنتهاوس","ستوديو",
    "تاون هاوس","تاونهاوس","توين هاوس","وحدة","وحده",
    "أرض","ارض","قطعة أرض","محل","مكتب","عيادة","مخزن","مستودع",
    "بناية","عمارة","روف","شاليه",
    "غرفة","غرفه","غرف","حمام","حمامات","مساحة","مساحه","متر","م2",
    "دور","طابق","أدوار","بدروم","ريسيبشن","صالة","صاله",
    "مفروش","مفروشة","تشطيب","سوبر لوكس","لوكس","نص تشطيب",
    "كور آند شيل","تشطيب كامل","الترا سوبر",
    "سعر","مقدم","قسط","أقساط","تقسيط","دفعة",
    "مليون","ألف","الف","مليار",
    "جاردن","حديقة","بركة سباحة","حمام سباحة","بلكونة","تراس",
    "أسانسير","جراج","موقف","أمن","بوابة","كمبوند",
    "التجمع","الرحاب","مدينتي","الشيخ زايد","العاصمة الإدارية",
    "الساحل","العين السخنة","أكتوبر","المهندسين","الدقي","المعادي",
    "مصر الجديدة","هليوبوليس","النزهة","الزمالك","وسط البلد",
    "القاهرة الجديدة","بدر","الإسكندرية","الغردقة",
    "شرم الشيخ","الجونة","سيدي عبد الرحمن","العلمين",
    "هايد بارك","ميفيدا","ماونتن فيو","ذا ادرس","بالم هيلز","ايستاون",
    "for sale","for rent","resale","lease",
    "apartment","villa","studio","duplex","penthouse","chalet",
    "townhouse","twin house","standalone","office","warehouse","land",
    "flat","unit","roof","shop","clinic","building",
    "bedroom","bathroom","sqm","sq m","sq.m","m2","ground floor","reception",
    "furnished","unfurnished","semi finished",
    "core & shell","core and shell","super lux","super luxury","finished",
    "cash","installment","down payment","negotiable",
    "garden","pool","balcony","terrace","parking","garage","security",
    "elevator","compound",
    "new cairo","sheikh zayed","new capital","ain sokhna","north coast",
    "maadi","heliopolis","zamalek","nasr city",
    "mivida","hyde park","palm hills","mountain view","east town",
    "el rehab","madinaty",
    "sha2a","she2a","2otda","otda","ghorf","hamam",
    "ll bai3","lel bai3","ll egar","lel egar",
    "mafroush","super lux","teshteeb",
]), key=len, reverse=True)

ALLOWLIST_RE = re.compile("|".join(re.escape(kw) for kw in _kw_all), re.IGNORECASE)

MIN_BODY_LEN = 20

# Updated to include "code" in multiple languages/formats
AD_DIVIDER_MARKERS = [
    r"كود", r"كود رقم", r"code", r"kd", r"ref", # <--- "code" keywords    
]

DIVIDER_RE = re.compile("|".join(AD_DIVIDER_MARKERS), re.IGNORECASE)

# def classify(msg: dict) -> str:
#     """
#     Classify a single message through the 3 gates.
#     Returns "pass" or one of: "system", "too_short", "blocklist", "no_keywords".
#     """
#     body = msg["body"].strip()
#     if SYSTEM_RE.search(body):
#         return "system"
#     if len(body) < MIN_BODY_LEN:
#         return "too_short"
#     if BLOCKLIST_RE.search(body):
#         return "blocklist"
#     if not ALLOWLIST_RE.search(body):
#         return "no_keywords"
#     return "pass"

def classify(msg: dict) -> str:
    body = msg["body"].strip()

    if SYSTEM_RE.search(body):
        return "system"

    if len(body) < MIN_BODY_LEN:
        return "too_short"

    has_ad_div= DIVIDER_RE.search(body)
    has_request_intent = REQUEST_INTENT_RE.search(body)
    has_price_context  = PRICE_CONTEXT_RE.search(body)
    has_block = BLOCKLIST_RE.search(body)
    has_ad = ALLOWLIST_RE.search(body)
    strong_ad = STRONG_AD_RE.search(body)
    mataloub_match = REQUEST_INTENT_RE.search(body)
    
    is_early_mataloub = False
    if mataloub_match:
        # If "مطلوب" starts within the first 20 characters, it's likely a Buyer Request
        if mataloub_match.start() < 20:
            is_early_mataloub = True

    #has code => must be ad 
    if has_ad_div:
        return "pass"

    if is_early_mataloub:
        return "blocklist"

    if has_block:
        return "blocklist"

    # normal flow
    if not has_ad:
        return "no_keywords"

    return "pass"



# ─── Formatting ───────────────────────────────────────────────────────────────

SEPARATOR = "-" * 60
from collections import Counter

def get_size_and_count(body: str, avg_len: float):
    body = body.strip()
    body_len = len(body)

    if avg_len > 0 and body_len > avg_len * 1.15:
        marker_matches = DIVIDER_RE.findall(body)

        if marker_matches:
            normalized = []
            for m in marker_matches:
                m_lower = m.lower()
                if m_lower in ['code', 'كود', 'kd', 'ref']:
                    normalized.append("unit_code_marker")
                else:
                    normalized.append(m_lower)

            counts = Counter(normalized).values()
            max_repeats = max(counts)

            if max_repeats >= 2:
                return f"multiple(~{max_repeats})", max_repeats
            else:
                est_ads = int(body_len // avg_len)
                return f"multiple(~{est_ads})", est_ads

        else:
            est_ads = int(body_len // avg_len)
            return f"multiple(~{est_ads})", est_ads

    return "single", 1



def format_message(msg: dict, avg_len: float, reason: str = None) -> str:
    body = msg["body"].strip()

    size, _ = get_size_and_count(body, avg_len)

    dt_display = msg["datetime"].strftime("%d/%m/%Y, %I:%M %p") \
        if isinstance(msg["datetime"], datetime) else msg["datetime"]

    lines = [
        SEPARATOR,
        f"From : {msg['sender']}",
        f"Date : {dt_display}",
        f"Size: {size}",
    ]
    if reason:
        lines.append(f"Drop : {reason}")
    lines += ["", body, ""]
    return "\n".join(lines)
# ─── Main ─────────────────────────────────────────────────────────────────────

def main(filepath: str):
    base_name  = os.path.splitext(os.path.basename(filepath))[0]
    output_dir = "Filtering_Ouput_Folder"
    os.makedirs(output_dir, exist_ok=True)

    ads_path      = os.path.join(output_dir, f"{base_name}_ads.txt")
    filtered_path = os.path.join(output_dir, f"{base_name}_filtered.txt")

    messages = parse_whatsapp_export(filepath)
    if not messages:
        print("No messages found. Check file format.")
        return

    # Classify all messages first so we can compute per-group averages
    results = []
    for msg in messages:
        body_len = len(msg["body"].strip())
        reason   = classify(msg)
        results.append((msg, body_len, reason))

    ads_lengths      = [l for _, l, r in results if r == "pass"]
    filtered_lengths = [l for _, l, r in results if r != "pass"]

    def avg(lst):
        return sum(lst) / len(lst) if lst else 0

    ads_avg      = avg(ads_lengths)
    filtered_avg = avg(filtered_lengths)

    ads_count      = len(ads_lengths)
    filtered_count = len(filtered_lengths)

    ads_big = 0

    for msg, body_len, reason in results:
        if reason != "pass":
            continue

        size, count = get_size_and_count(msg["body"], ads_avg)

        if size.startswith("multiple") and count > 1:
            ads_big += 1

    with open(ads_path, "w", encoding="utf-8") as ads_f, \
         open(filtered_path, "w", encoding="utf-8") as filt_f:

        for msg, body_len, reason in results:
            if reason == "pass":
                ads_f.write(format_message(msg, ads_avg) + "\n")
            else:
                filt_f.write(format_message(msg, filtered_avg, reason) + "\n")

    print(f"Parsed messages: {len(messages)}")

    print("\n--- ADS STATS ---")
    print(f"Total: {ads_count}")
    print(f"Average length: {ads_avg:.2f}")
    print(f"Big ads (multiple only): {ads_big}")

    print("\n--- FILTERED STATS ---")
    print(f"Total: {filtered_count}")
    print(f"Average length: {filtered_avg:.2f}")


if __name__ == "__main__":
    file_path = "350_sampled_messages.txt"
    main(file_path)
    batch_messages.main(file_path)
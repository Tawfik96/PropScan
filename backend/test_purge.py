"""
test_purge.py
=============
Seeds a fresh SQLite DB directly from test_chat_purge.txt (no Gemini, no API),
injects 5 artificially old rows, then runs purge_old_listings() and validates.

Run from your backend/ folder:
    python test_purge.py

Expected result with FORCE_OLD_ROWS = True:
    Batch earliest   : 2024-09-28  (first real message in the chat file)
    Cutoff           : 2024-08-28  (1 month before)
    Rows deleted     : 5           (the injected 2023 rows)
    Rows remaining   : 43          (all real chat messages)
"""

import sqlite3
import re
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ── Config ────────────────────────────────────────────────────────────────────

CHAT_FILE      = "test_chat_purge.txt"
DB_FILE        = "test_purge.db"
FORCE_OLD_ROWS = True   # inject 5 rows from 2023 so purge has something to delete

# ── WhatsApp line parser ──────────────────────────────────────────────────────

WA_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)\s*-\s*([^:]+):\s*(.*)",
    re.IGNORECASE,
)
DATE_FORMATS = [
    "%d/%m/%Y, %I:%M %p", "%d/%m/%Y, %I:%M%p",
    "%d/%m/%y, %I:%M %p", "%d/%m/%y, %I:%M%p",
    "%d/%m/%Y, %H:%M",    "%d/%m/%y, %H:%M",
]

def parse_datetime(date_str, time_str):
    combined = f"{date_str}, {time_str}".strip()
    combined = re.sub(r'\s*(am|pm)\s*', lambda m: f" {m.group(1).upper()}", combined, flags=re.IGNORECASE)
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(combined, fmt)
        except ValueError:
            continue
    return None

def parse_chat(filepath):
    rows, current = [], None
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        m = WA_PATTERN.match(line)
        if m:
            if current:
                rows.append(current)
            dt = parse_datetime(m.group(1), m.group(2))
            current = {"sender": m.group(3).strip(), "body": m.group(4).strip(),
                       "ad_date": dt.isoformat()} if dt else None
        elif current:
            current["body"] += "\n" + line.rstrip()
    if current:
        rows.append(current)
    return [r for r in rows if r["body"] and "end-to-end encrypted" not in r["body"]]

# ── DB helpers ────────────────────────────────────────────────────────────────

def init_db(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT, ad_date TEXT, body TEXT
        )
    """)
    conn.commit()
    return conn

def seed_db(conn, rows):
    conn.executemany(
        "INSERT INTO listings (sender, ad_date, body) VALUES (?, ?, ?)",
        [(r["sender"], r["ad_date"], r["body"]) for r in rows],
    )
    conn.commit()

# ── Purge (inline — mirrors purge_old_listings.py) ───────────────────────────

def purge_old_listings(db_path, batch_earliest=None):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    cur = conn.cursor()

    if batch_earliest:
        earliest_str = batch_earliest
    else:
        cur.execute("SELECT MIN(ad_date) FROM listings WHERE ad_date IS NOT NULL")
        row = cur.fetchone()
        if not row or not row[0]:
            conn.close()
            return {}
        earliest_str = row[0]

    cutoff_dt  = datetime.fromisoformat(earliest_str) - relativedelta(months=1)
    cutoff_str = cutoff_dt.isoformat()

    cur.execute("SELECT COUNT(*) FROM listings WHERE ad_date < ?", (cutoff_str,))
    delete_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM listings WHERE ad_date >= ? OR ad_date IS NULL", (cutoff_str,))
    keep_count = cur.fetchone()[0]

    cur.execute("DELETE FROM listings WHERE ad_date < ?", (cutoff_str,))
    conn.commit()
    conn.execute("VACUUM;")
    conn.close()

    return {"earliest_date": earliest_str, "cutoff_date": cutoff_str,
            "deleted_count": delete_count, "remaining_count": keep_count}

# ── Main test ─────────────────────────────────────────────────────────────────

def run_test():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    print("=" * 55)
    print("  PropScan — Purge Logic Test (no API)")
    print("=" * 55)

    # 1. Parse
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rows = parse_chat(os.path.join(script_dir, CHAT_FILE))
    dates = sorted(set(r["ad_date"][:10] for r in rows))
    print(f"\n[1] Parsed {len(rows)} messages from {CHAT_FILE}")
    print(f"    Date range : {dates[0]} → {dates[-1]}")

    # batch_earliest = what the pipeline would pass in (min of THIS batch)
    batch_earliest = min(r["ad_date"] for r in rows)
    print(f"    Batch earliest : {batch_earliest}")

    # 2. Seed
    conn = init_db(DB_FILE)
    seed_db(conn, rows)

    old_rows = []
    if FORCE_OLD_ROWS:
        old_rows = [
            ("Old Seller A", "2023-07-15T10:00:00", "Apartment for sale in Rehab 3BR 2M"),
            ("Old Seller B", "2023-07-20T11:00:00", "Villa for sale in Mivida 5BR 8M"),
            ("Old Seller C", "2023-08-01T09:00:00", "Penthouse for rent Eastown 55k"),
            ("Old Seller D", "2023-08-10T14:00:00", "Standalone Mountain View 15M"),
            ("Old Seller E", "2023-08-25T16:30:00", "Duplex Hyde Park 7M"),
        ]
        conn.executemany(
            "INSERT INTO listings (sender, ad_date, body) VALUES (?, ?, ?)", old_rows
        )
        conn.commit()
    conn.close()

    total_seeded = len(rows) + len(old_rows)
    print(f"\n[2] Seeded {len(rows)} real rows" +
          (f" + {len(old_rows)} forced-old rows (2023)" if old_rows else "") +
          f" → {total_seeded} total")

    # 3. Before snapshot
    conn = sqlite3.connect(DB_FILE)
    before = conn.execute("SELECT COUNT(*), MIN(ad_date), MAX(ad_date) FROM listings").fetchone()
    conn.close()
    print(f"\n[3] DB BEFORE purge")
    print(f"    Rows     : {before[0]}")
    print(f"    Min date : {before[1]}")
    print(f"    Max date : {before[2]}")

    # 4. Purge — pass batch_earliest so anchor = first real message, not 2023
    print(f"\n[4] Running purge_old_listings(batch_earliest='{batch_earliest}')...")
    result = purge_old_listings(DB_FILE, batch_earliest=batch_earliest)
    print(f"    Anchor date      : {result['earliest_date']}")
    print(f"    Cutoff (−1 month): {result['cutoff_date']}")
    print(f"    Rows deleted     : {result['deleted_count']}")
    print(f"    Rows remaining   : {result['remaining_count']}")

    # 5. After snapshot
    conn = sqlite3.connect(DB_FILE)
    after = conn.execute("SELECT COUNT(*), MIN(ad_date), MAX(ad_date) FROM listings").fetchone()
    conn.close()
    print(f"\n[5] DB AFTER purge")
    print(f"    Rows     : {after[0]}")
    print(f"    Min date : {after[1]}")
    print(f"    Max date : {after[2]}")

    # 6. Assertions
    print(f"\n[6] Assertions")
    passed = True
    expected_deleted = len(old_rows)

    def check(cond, msg_ok, msg_fail):
        nonlocal passed
        if cond:
            print(f"    ✓ {msg_ok}")
        else:
            print(f"    ✗ {msg_fail}")
            passed = False

    check(result["deleted_count"] == expected_deleted,
          f"Deleted count = {expected_deleted}  (correct)",
          f"Expected {expected_deleted} deleted, got {result['deleted_count']}")

    check(after[0] == len(rows),
          f"Remaining = {len(rows)}  (all real rows kept)",
          f"Expected {len(rows)} remaining, got {after[0]}")

    cutoff_dt = datetime.fromisoformat(result["cutoff_date"])
    if after[1]:
        oldest_remaining = datetime.fromisoformat(after[1])
        check(oldest_remaining >= cutoff_dt,
              f"Oldest remaining ({after[1][:10]}) >= cutoff ({result['cutoff_date'][:10]})",
              f"Oldest remaining row is BEFORE cutoff — purge didn't work!")

    check(after[2] == before[2],
          "Newest row unchanged (max date preserved)",
          "Max date changed unexpectedly")

    print(f"\n{'='*55}")
    print(f"  Result: {'ALL PASSED ✓' if passed else 'SOME FAILED ✗'}")
    print(f"{'='*55}")

    os.remove(DB_FILE)
    print(f"\n  Temp DB {DB_FILE} cleaned up.")


if __name__ == "__main__":
    run_test()

"""
purge_old_listings.py
---------------------
After inserting a batch of messages, computes the cutoff as:
    cutoff = earliest_date_in_BATCH - 1 month
...and deletes all DB rows with ad_date < cutoff.

Example:
    Batch spans Jan 3 → Mar 4 2025
    Earliest in batch = Jan 3 2025
    Cutoff            = Dec 3 2024
    Deleted           = all rows with ad_date < Dec 3 2024

Usage:
    # Standalone (anchors to DB MIN — for maintenance runs):
    python purge_old_listings.py
    python purge_old_listings.py path/to/listings.db

    # From pipeline (pass the batch's earliest date for correct behaviour):
    from purge_old_listings import purge_old_listings
    purge_old_listings("listings.db", batch_earliest="2025-01-03T09:00:00")
"""

import sqlite3
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

DB_PATH = sys.argv[1] if len(sys.argv) > 1 else "listings.db"


def purge_old_listings(db_path: str = DB_PATH, batch_earliest: str = None) -> dict:
    """
    batch_earliest : ISO datetime string for the earliest message in the
                     batch just inserted, e.g. "2025-01-03T09:00:00".
                     Pass this from the pipeline so the cutoff anchors to
                     the new batch, not to old rows already in the DB.
                     If omitted, falls back to MIN(ad_date) in the DB.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    cur = conn.cursor()

    # --- 1. Determine anchor date ---
    if batch_earliest:
        earliest_str = batch_earliest
        print(f"Anchor (from batch)  : {earliest_str}")
    else:
        cur.execute("SELECT MIN(ad_date) FROM listings WHERE ad_date IS NOT NULL")
        row = cur.fetchone()
        if row is None or row[0] is None:
            conn.close()
            print("No listings with ad_date found — nothing to purge.")
            return {}
        earliest_str = row[0]
        print(f"Anchor (DB MIN)      : {earliest_str}")

    earliest_dt = datetime.fromisoformat(earliest_str)

    # --- 2. Cutoff = anchor - 1 calendar month ---
    cutoff_dt  = earliest_dt - relativedelta(months=1)
    cutoff_str = cutoff_dt.isoformat()
    print(f"Cutoff (−1 month)    : {cutoff_str}")

    # --- 3. Count rows to delete ---
    cur.execute("SELECT COUNT(*) FROM listings WHERE ad_date < ?", (cutoff_str,))
    delete_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM listings WHERE ad_date >= ? OR ad_date IS NULL", (cutoff_str,))
    keep_count = cur.fetchone()[0]

    print(f"Rows to delete       : {delete_count}")
    print(f"Rows to keep         : {keep_count}")

    # --- 4. Delete & commit ---
    cur.execute("DELETE FROM listings WHERE ad_date < ?", (cutoff_str,))
    conn.commit()

    # --- 5. VACUUM ---
    conn.execute("VACUUM;")
    conn.close()

    print("Purge complete.")
    return {
        "earliest_date":   earliest_str,
        "cutoff_date":     cutoff_str,
        "deleted_count":   delete_count,
        "remaining_count": keep_count,
    }


# ── Integration snippet for extractFromChatExport.py ─────────────────────────
# At the end of run_pipeline(), after all inserts, add:
#
#   from purge_old_listings import purge_old_listings
#   batch_earliest = min(ad["datetime"].isoformat() for ad in ads)
#   purge_old_listings("listings.db", batch_earliest=batch_earliest)
#
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = purge_old_listings()
    if result:
        print(result)
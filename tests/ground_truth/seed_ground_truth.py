"""
seed_ground_truth.py
====================
Creates ground_truth.db — a hand-annotated SQLite database whose rows
represent the CORRECT extraction output for the messages in
fixtures/gt_chat.txt.

Every field in every row was set by a human reviewer, not by Gemini.
This is the reference used by compare_to_ground_truth.py.

Run once (or re-run to reset):
    python ground_truth/seed_ground_truth.py
"""

import sqlite3
import json
import os

GT_DB = os.path.join(os.path.dirname(__file__), "ground_truth.db")

# ── Schema (mirrors listings table exactly) ───────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    property_type       TEXT,
    transaction_type    TEXT,
    price               REAL,
    currency            TEXT DEFAULT 'EGP',
    area_sqm            REAL,
    land_area_sqm       REAL,
    bedrooms            INTEGER,
    bathrooms           INTEGER,
    floor_number        INTEGER,
    furnished           TEXT,
    finishing           TEXT,
    has_garden          INTEGER,
    garden_area_sqm     REAL,
    has_pool            INTEGER,
    has_balcony         INTEGER,
    city                TEXT,
    district            TEXT,
    compound_name       TEXT,
    down_payment        REAL,
    installment_years   REAL,
    installment_amount  REAL,
    phone_numbers       TEXT,
    reference_id        TEXT,
    view                TEXT,
    sender              TEXT,
    ad_date             TEXT
);
"""

# ── Ground truth rows — hand-annotated ───────────────────────────────────────
# Each dict maps to one expected listing extracted from fixtures/gt_chat.txt.
# MSG_ID in the comment ties back to the message number in gt_chat.txt.

GT_ROWS = [

    # MSG_01 — Rehab apartment for rent
    {
        "property_type":      "apartment",
        "transaction_type":   "rent",
        "price":              35000,
        "currency":           "EGP",
        "area_sqm":           110,
        "land_area_sqm":      None,
        "bedrooms":           2,
        "bathrooms":          2,
        "floor_number":       0,          # ground floor
        "furnished":          "furnished",
        "finishing":          "finished",
        "has_garden":         1,
        "garden_area_sqm":    40,
        "has_pool":           0,
        "has_balcony":        0,
        "city":               "Cairo",
        "district":           "Rehab",
        "compound_name":      None,
        "down_payment":       None,
        "installment_years":  None,
        "installment_amount": None,
        "phone_numbers":      json.dumps(["+201102043283"]),
        "reference_id":       "rehab96",
        "view":               "garden",
        "sender":             "+20 11 02043283",
        "ad_date":            "2024-09-28T13:31:00",
    },

    # MSG_02 — Eastown apartment for rent
    {
        "property_type":      "apartment",
        "transaction_type":   "rent",
        "price":              55000,
        "currency":           "EGP",
        "area_sqm":           156,
        "land_area_sqm":      None,
        "bedrooms":           3,
        "bathrooms":          4,
        "floor_number":       3,
        "furnished":          "unfurnished",
        "finishing":          "finished",
        "has_garden":         0,
        "garden_area_sqm":    None,
        "has_pool":           0,
        "has_balcony":        0,
        "city":               "Cairo",
        "district":           "New Cairo",
        "compound_name":      "Eastown",
        "down_payment":       None,
        "installment_years":  None,
        "installment_amount": None,
        "phone_numbers":      json.dumps(["+201102043283"]),
        "reference_id":       "ESr164",
        "view":               None,
        "sender":             "+20 11 02043283",
        "ad_date":            "2024-09-28T13:36:00",
    },

    # MSG_03 — Mivida apartment for sale
    {
        "property_type":      "apartment",
        "transaction_type":   "sale",
        "price":              19500000,
        "currency":           "EGP",
        "area_sqm":           200,
        "land_area_sqm":      None,
        "bedrooms":           3,
        "bathrooms":          4,
        "floor_number":       1,
        "furnished":          "unfurnished",
        "finishing":          "finished",
        "has_garden":         0,
        "garden_area_sqm":    None,
        "has_pool":           0,
        "has_balcony":        0,
        "city":               "Cairo",
        "district":           "New Cairo",
        "compound_name":      "Mivida",
        "down_payment":       None,
        "installment_years":  None,
        "installment_amount": None,
        "phone_numbers":      json.dumps([]),
        "reference_id":       "MIVs134",
        "view":               "landscape",
        "sender":             "+20 11 02043283",
        "ad_date":            "2024-09-28T13:42:00",
    },

    # MSG_04 — Rehab furnished apartment for rent
    {
        "property_type":      "apartment",
        "transaction_type":   "rent",
        "price":              45000,
        "currency":           "EGP",
        "area_sqm":           134,
        "land_area_sqm":      None,
        "bedrooms":           2,
        "bathrooms":          2,
        "floor_number":       0,
        "furnished":          "furnished",
        "finishing":          "luxury",
        "has_garden":         0,
        "garden_area_sqm":    None,
        "has_pool":           0,
        "has_balcony":        1,
        "city":               "Cairo",
        "district":           "Rehab",
        "compound_name":      None,
        "down_payment":       None,
        "installment_years":  None,
        "installment_amount": None,
        "phone_numbers":      json.dumps(["+201020802909"]),
        "reference_id":       None,
        "view":               "garden",
        "sender":             "+20 10 20802909",
        "ad_date":            "2024-09-28T13:44:00",
    },

    # MSG_05 — Mivida apartment for sale (USD)
    {
        "property_type":      "apartment",
        "transaction_type":   "sale",
        "price":              336000,
        "currency":           "USD",
        "area_sqm":           138,
        "land_area_sqm":      None,
        "bedrooms":           2,
        "bathrooms":          2,
        "floor_number":       None,
        "furnished":          "unfurnished",
        "finishing":          "luxury",
        "has_garden":         0,
        "garden_area_sqm":    None,
        "has_pool":           0,
        "has_balcony":        0,
        "city":               "Cairo",
        "district":           "New Cairo",
        "compound_name":      "Mivida",
        "down_payment":       None,
        "installment_years":  None,
        "installment_amount": None,
        "phone_numbers":      json.dumps(["+201028354877", "+201116086804"]),
        "reference_id":       "MIVs45",
        "view":               None,
        "sender":             "+20 10 28354877",
        "ad_date":            "2024-09-28T13:52:00",
    },

    # MSG_06 — Mountain View Hyde Park penthouse for sale
    {
        "property_type":      "penthouse",
        "transaction_type":   "sale",
        "price":              13000000,
        "currency":           "EGP",
        "area_sqm":           190,
        "land_area_sqm":      None,
        "bedrooms":           3,
        "bathrooms":          3,
        "floor_number":       None,
        "furnished":          "unfurnished",
        "finishing":          "finished",
        "has_garden":         0,
        "garden_area_sqm":    None,
        "has_pool":           0,
        "has_balcony":        0,
        "city":               "Cairo",
        "district":           "New Cairo",
        "compound_name":      "Mountain View Hyde Park",
        "down_payment":       None,
        "installment_years":  None,
        "installment_amount": None,
        "phone_numbers":      json.dumps(["+201028354877", "+201116086804"]),
        "reference_id":       "MVHPs107",
        "view":               None,
        "sender":             "+20 10 28354877",
        "ad_date":            "2024-09-28T13:52:00",
    },

    # MSG_07 — Zed East apartment for sale (installment)
    {
        "property_type":      "apartment",
        "transaction_type":   "sale",
        "price":              14005000,
        "currency":           "EGP",
        "area_sqm":           132,
        "land_area_sqm":      None,
        "bedrooms":           2,
        "bathrooms":          3,
        "floor_number":       2,
        "furnished":          "unfurnished",
        "finishing":          "finished",
        "has_garden":         0,
        "garden_area_sqm":    None,
        "has_pool":           0,
        "has_balcony":        0,
        "city":               "Cairo",
        "district":           "New Cairo",
        "compound_name":      "Zed East",
        "down_payment":       2000000,
        "installment_years":  None,
        "installment_amount": None,
        "phone_numbers":      json.dumps(["+201028742556"]),
        "reference_id":       None,
        "view":               None,
        "sender":             "+20 10 28742556",
        "ad_date":            "2024-09-28T14:36:00",
    },

    # MSG_08 — Tag Sultan furnished rental
    {
        "property_type":      "apartment",
        "transaction_type":   "rent",
        "price":              30000,
        "currency":           "EGP",
        "area_sqm":           220,
        "land_area_sqm":      None,
        "bedrooms":           3,
        "bathrooms":          3,
        "floor_number":       None,
        "furnished":          "furnished",
        "finishing":          "finished",
        "has_garden":         0,
        "garden_area_sqm":    None,
        "has_pool":           0,
        "has_balcony":        0,
        "city":               "Cairo",
        "district":           "New Cairo",
        "compound_name":      "Tag Sultan",
        "down_payment":       None,
        "installment_years":  None,
        "installment_amount": None,
        "phone_numbers":      json.dumps(["+201021055591"]),
        "reference_id":       None,
        "view":               None,
        "sender":             "+20 10 21055591",
        "ad_date":            "2024-09-28T15:17:00",
    },

    # MSG_09 — Trio Gardens penthouse for sale
    {
        "property_type":      "penthouse",
        "transaction_type":   "sale",
        "price":              9000000,
        "currency":           "EGP",
        "area_sqm":           160,
        "land_area_sqm":      None,
        "bedrooms":           3,
        "bathrooms":          3,
        "floor_number":       None,
        "furnished":          "unfurnished",
        "finishing":          "finished",
        "has_garden":         0,
        "garden_area_sqm":    None,
        "has_pool":           0,
        "has_balcony":        0,
        "city":               "Cairo",
        "district":           "New Cairo",
        "compound_name":      "Trio Gardens",
        "down_payment":       None,
        "installment_years":  None,
        "installment_amount": None,
        "phone_numbers":      json.dumps(["+201102043283"]),
        "reference_id":       "BHs1050",
        "view":               None,
        "sender":             "+20 11 02043283",
        "ad_date":            "2024-09-28T14:30:00",
    },

    # MSG_10 — Galleria Moon Valley apartment with garden
    {
        "property_type":      "apartment",
        "transaction_type":   "sale",
        "price":              7687500,
        "currency":           "EGP",
        "area_sqm":           128,
        "land_area_sqm":      None,
        "bedrooms":           2,
        "bathrooms":          1,
        "floor_number":       0,
        "furnished":          "furnished",
        "finishing":          "finished",
        "has_garden":         1,
        "garden_area_sqm":    80,
        "has_pool":           0,
        "has_balcony":        0,
        "city":               "Cairo",
        "district":           "New Cairo",
        "compound_name":      "Galleria Moon Valley",
        "down_payment":       None,
        "installment_years":  None,
        "installment_amount": None,
        "phone_numbers":      json.dumps(["+201050969861"]),
        "reference_id":       "cs950",
        "view":               None,
        "sender":             "+20 10 50969861",
        "ad_date":            "2024-09-28T15:22:00",
    },
]

# ─────────────────────────────────────────────────────────────────────────────

def seed():
    if os.path.exists(GT_DB):
        os.remove(GT_DB)

    conn = sqlite3.connect(GT_DB)
    conn.executescript(SCHEMA)

    cols = [c for c in GT_ROWS[0].keys()]
    placeholders = ", ".join("?" * len(cols))
    col_names    = ", ".join(cols)

    for row in GT_ROWS:
        conn.execute(
            f"INSERT INTO listings ({col_names}) VALUES ({placeholders})",
            [row[c] for c in cols],
        )

    conn.commit()
    conn.close()
    print(f"Ground truth DB created: {GT_DB}  ({len(GT_ROWS)} rows)")


if __name__ == "__main__":
    seed()

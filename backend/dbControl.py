import sqlite3
import json
import os

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "listings.db"))

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def has_listings_table():
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='listings'"
        ).fetchone()
        return row is not None
    finally:
        conn.close()

def init_db():
    conn = get_conn()
    try:
        if has_listings_table():
            return conn
        
        conn.execute("""
            CREATE TABLE listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_type TEXT,
                transaction_type TEXT,
                price REAL,
                currency TEXT DEFAULT 'EGP',
                area_sqm REAL,
                bedrooms INTEGER,
                bathrooms INTEGER,
                city TEXT,
                district TEXT,
                compound_name TEXT,
                phone_numbers TEXT,
                reference_id TEXT,
                ad_date TEXT,
                ad_snippet TEXT,
                original_message TEXT,
                sender TEXT,
                amenities TEXT DEFAULT '[]',
                price_negotiable INTEGER DEFAULT 0,
                has_elevator INTEGER DEFAULT 0,
                has_garden INTEGER DEFAULT 0,
                has_pool INTEGER DEFAULT 0,
                has_balcony INTEGER DEFAULT 0,
                has_security INTEGER DEFAULT 0,
                has_parking INTEGER DEFAULT 0,
                extracted_at DATETIME DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        return conn
    finally:
        if not has_listings_table():
            conn.close()

def get_listings(
    price_min=None, price_max=None, bedrooms=None,
    city=None, transaction_type=None, property_type=None,
    limit=100, offset=0
):
    if not has_listings_table():
        return []

    conn = get_conn()
    query = "SELECT * FROM listings WHERE 1=1"
    params = []

    if price_min is not None:
        query += " AND price >= ?"
        params.append(price_min)
    if price_max is not None:
        query += " AND price <= ?"
        params.append(price_max)
    if bedrooms is not None:
        query += " AND bedrooms = ?"
        params.append(bedrooms)
    if city:
        query += " AND LOWER(city) = LOWER(?)"
        params.append(city)
    if transaction_type:
        query += " AND transaction_type = ?"
        params.append(transaction_type)
    if property_type:
        query += " AND property_type = ?"
        params.append(property_type)

    query += " ORDER BY ad_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()

    result = []
    for row in rows:
        d = dict(row)
        try:
            d["amenities"] = json.loads(d.get("amenities", "[]"))
        except:
            d["amenities"] = []
        try:
            d["phone_numbers"] = json.loads(d.get("phone_numbers", "[]"))
        except:
            d["phone_numbers"] = []
        d["price_negotiable"] = bool(d.get("price_negotiable", False))
        d["has_elevator"] = bool(d.get("has_elevator", False))
        d["has_garden"] = bool(d.get("has_garden", False))
        d["has_pool"] = bool(d.get("has_pool", False))
        d["has_balcony"] = bool(d.get("has_balcony", False))
        d["has_security"] = bool(d.get("has_security", False))
        d["has_parking"] = bool(d.get("has_parking", False))
        result.append(d)
    return result


def get_distinct_cities():
    if not has_listings_table():
        return []

    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT city FROM listings WHERE city IS NOT NULL AND city != '' ORDER BY city"
    ).fetchall()
    conn.close()
    return [r["city"] for r in rows]

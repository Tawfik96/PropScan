import sqlite3
import json
import os
import extractFromChatExport

DB_PATH = os.path.join(os.path.dirname(__file__), extractFromChatExport.DB_PATH)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    has_listings_table()


def has_listings_table():
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='listings'"
        ).fetchone()
        return row is not None
    finally:
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
        d["amenities"] = json.loads(d["amenities"] or "[]")
        d["phone_numbers"] = json.loads(d["phone_numbers"] or "[]")
        d["price_negotiable"] = bool(d["price_negotiable"])
        d["has_elevator"] = bool(d["has_elevator"])
        d["has_garden"] = bool(d["has_garden"])
        d["has_pool"] = bool(d["has_pool"])
        d["has_balcony"] = bool(d["has_balcony"])
        d["has_security"] = bool(d["has_security"])
        d["has_parking"] = bool(d["has_parking"])
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
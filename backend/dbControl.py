import sqlite3

try:
    from .paths import DB_PATH
except ImportError:
    from paths import DB_PATH

DEFAULT_LIMIT = 100


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    return has_listings_table()


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
    limit=DEFAULT_LIMIT, offset=0
):
    if not has_listings_table():
        return []

    conn = get_conn()
    try:
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

        query += " ORDER BY date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_distinct_cities():
    if not has_listings_table():
        return []

    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT DISTINCT city FROM listings WHERE city IS NOT NULL AND city != '' ORDER BY city"
        ).fetchall()
        return [r["city"] for r in rows]
    finally:
        conn.close()

"""
db.py
-----
All database operations for the Real Estate extraction pipeline.

Covers:
  - DB path configuration
  - Schema creation (listings table)
  - Inserting extracted listings
  - Querying listings with filters
  - Listing distinct cities
"""

import sqlite3
from config import DB_PATH


# ── Connection helper ─────────────────────────────────────────────────────────

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ── Schema ────────────────────────────────────────────────────────────────────

def init_schema(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create the listings table if it doesn't exist. Returns an open connection."""
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


# ── Write operations ──────────────────────────────────────────────────────────

def insert_listing(
    conn: sqlite3.Connection,
    data: dict,
    original_msg: str,
    sender: str = None,
    date: str = None,
) -> None:
    """Insert a single extracted listing into the database."""
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
            data.get("price"),
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


# ── Read operations ───────────────────────────────────────────────────────────

def init_db() -> None:
    """Called on server startup to verify the DB is accessible."""
    has_listings_table()


def has_listings_table() -> bool:
    """Return True if the listings table exists."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='listings'"
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def get_listings(
    price_min: float = None,
    price_max: float = None,
    bedrooms: int = None,
    city: str = None,
    transaction_type: str = None,
    property_type: str = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """Return listings matching the given filters."""
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

    query += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_distinct_cities() -> list[str]:
    """Return all distinct city values present in the listings table."""
    if not has_listings_table():
        return []

    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT city FROM listings WHERE city IS NOT NULL AND city != '' ORDER BY city"
    ).fetchall()
    conn.close()
    return [r["city"] for r in rows]

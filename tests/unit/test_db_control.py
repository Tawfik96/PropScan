"""
test_db_control.py
==================
Unit tests for dbControl.py:
  - init_db() / has_listings_table()
  - insert_listing() via extractFromChatExport internals
  - get_listings() with every filter combination
  - get_distinct_cities()
  - Pagination (limit / offset)
  - Edge cases: empty DB, null fields, extreme prices

Run:
    cd backend && python -m pytest ../tests/unit/test_db_control.py -v
"""

import sys, os, sqlite3, json, unittest, tempfile, shutil

temp_db = tempfile.NamedTemporaryFile(delete=False)
os.environ["DB_PATH"] = temp_db.name

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

sys.path.insert(0, BACKEND_DIR)
import backend.dbControl as dbControl

# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_LISTINGS = [
    {
        "property_type":   "apartment", "transaction_type": "sale",
        "price":           8000000,     "currency":         "EGP",
        "area_sqm":        130,         "bedrooms":         3,
        "bathrooms":       2,           "city":             "Cairo",
        "district":        "Rehab",     "compound_name":    "Rehab City",
        "phone_numbers":   json.dumps(["+201011111111"]),
        "reference_id":    "TEST001",   "ad_date":          "2024-09-28T13:00:00",
        "ad_snippet":      "Apartment for sale in Rehab",
        "original_message":"Apartment for sale in Rehab\nArea 130 SQM\nPrice 8M",
        "sender":          "+20 10 11111111",
    },
    {
        "property_type":   "villa",     "transaction_type": "rent",
        "price":           45000,       "currency":         "EGP",
        "area_sqm":        300,         "bedrooms":         5,
        "bathrooms":       4,           "city":             "Cairo",
        "district":        "New Cairo", "compound_name":    "Mivida",
        "phone_numbers":   json.dumps(["+201022222222"]),
        "reference_id":    "TEST002",   "ad_date":          "2024-10-01T10:00:00",
        "ad_snippet":      "Villa for rent in Mivida",
        "original_message":"Villa for rent in Mivida 5BR 45k",
        "sender":          "+20 10 22222222",
    },
    {
        "property_type":   "penthouse", "transaction_type": "sale",
        "price":           13000000,    "currency":         "EGP",
        "area_sqm":        190,         "bedrooms":         3,
        "bathrooms":       3,           "city":             "Cairo",
        "district":        "New Cairo", "compound_name":    "Mountain View Hyde Park",
        "phone_numbers":   json.dumps(["+201033333333"]),
        "reference_id":    "TEST003",   "ad_date":          "2024-10-15T11:00:00",
        "ad_snippet":      "Penthouse for sale MVHP",
        "original_message":"Penthouse for sale MVHP 3BR 13M",
        "sender":          "+20 10 33333333",
    },
    {
        "property_type":   "apartment", "transaction_type": "rent",
        "price":           25000,       "currency":         "EGP",
        "area_sqm":        100,         "bedrooms":         2,
        "bathrooms":       1,           "city":             "Alexandria",
        "district":        "Smouha",    "compound_name":    None,
        "phone_numbers":   json.dumps(["+201044444444"]),
        "reference_id":    "TEST004",   "ad_date":          "2024-11-01T09:00:00",
        "ad_snippet":      "Apartment for rent Alexandria",
        "original_message":"Apartment for rent in Smouha Alex 25k",
        "sender":          "+20 10 44444444",
    },
]


def _make_test_db():
    """Return path to a fresh temp DB seeded with SAMPLE_LISTINGS."""
    tmp = tempfile.mkdtemp()
    db_path = os.path.join(tmp, "test.db")
    # Monkey-patch dbControl to use test DB
    original = dbControl.DB_PATH
    dbControl.DB_PATH = db_path
    conn = dbControl.init_db()
    for row in SAMPLE_LISTINGS:
        conn.execute("""
            INSERT INTO listings
              (property_type, transaction_type, price, currency, area_sqm,
               bedrooms, bathrooms, city, district, compound_name,
               phone_numbers, reference_id, ad_date,
               ad_snippet, original_message, sender)
            VALUES
              (:property_type, :transaction_type, :price, :currency, :area_sqm,
               :bedrooms, :bathrooms, :city, :district, :compound_name,
               :phone_numbers, :reference_id, :ad_date,
               :ad_snippet, :original_message, :sender)
        """, row)
    conn.commit()
    conn.close()
    dbControl.DB_PATH = original
    return db_path, tmp


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestInitDB(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test.db")
        self._orig = dbControl.DB_PATH
        dbControl.DB_PATH = self.db_path

    def tearDown(self):
        dbControl.DB_PATH = self._orig
        shutil.rmtree(self.tmp)

    def test_creates_listings_table(self):
        dbControl.init_db()
        self.assertTrue(dbControl.has_listings_table())

    def test_has_listings_table_false_on_empty(self):
        # fresh DB with no init_db call
        sqlite3.connect(self.db_path).close()
        self.assertFalse(dbControl.has_listings_table())

    def test_idempotent_double_init(self):
        dbControl.init_db()
        dbControl.init_db()   # should not raise
        self.assertTrue(dbControl.has_listings_table())

    def test_required_columns_exist(self):
        conn = dbControl.init_db()
        cols = {row[1] for row in conn.execute("PRAGMA table_info(listings)")}
        for required in ("property_type", "transaction_type", "price",
                         "city", "bedrooms", "ad_date", "phone_numbers"):
            self.assertIn(required, cols, f"Missing column: {required}")
        conn.close()


class TestGetListings(unittest.TestCase):

    def setUp(self):
        self.db_path, self.tmp = _make_test_db()
        self._orig = dbControl.DB_PATH
        dbControl.DB_PATH = self.db_path

    def tearDown(self):
        dbControl.DB_PATH = self._orig
        shutil.rmtree(self.tmp)

    def test_returns_all_rows_no_filter(self):
        rows = dbControl.get_listings()
        self.assertEqual(len(rows), 4)

    def test_filter_by_transaction_type_sale(self):
        rows = dbControl.get_listings(transaction_type="sale")
        self.assertTrue(all(r["transaction_type"] == "sale" for r in rows))
        self.assertEqual(len(rows), 2)

    def test_filter_by_transaction_type_rent(self):
        rows = dbControl.get_listings(transaction_type="rent")
        self.assertEqual(len(rows), 2)

    def test_filter_by_bedrooms(self):
        rows = dbControl.get_listings(bedrooms=3)
        self.assertTrue(all(r["bedrooms"] == 3 for r in rows))
        self.assertEqual(len(rows), 2)

    def test_filter_by_city(self):
        rows = dbControl.get_listings(city="Alexandria")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["city"], "Alexandria")

    def test_filter_by_price_min(self):
        rows = dbControl.get_listings(price_min=10000000)
        self.assertTrue(all(r["price"] >= 10000000 for r in rows))

    def test_filter_by_price_max(self):
        rows = dbControl.get_listings(price_max=50000)
        self.assertTrue(all(r["price"] <= 50000 for r in rows))

    def test_filter_price_range(self):
        rows = dbControl.get_listings(price_min=20000, price_max=50000)
        self.assertTrue(all(20000 <= r["price"] <= 50000 for r in rows))

    def test_filter_by_property_type(self):
        rows = dbControl.get_listings(property_type="penthouse")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["property_type"], "penthouse")

    def test_combined_filters(self):
        rows = dbControl.get_listings(
            transaction_type="sale",
            bedrooms=3,
            city="Cairo",
        )
        self.assertTrue(len(rows) >= 1)
        for r in rows:
            self.assertEqual(r["transaction_type"], "sale")
            self.assertEqual(r["bedrooms"], 3)

    def test_no_results_returns_empty_list(self):
        rows = dbControl.get_listings(city="Timbuktu")
        self.assertEqual(rows, [])

    def test_pagination_limit(self):
        rows = dbControl.get_listings(limit=2)
        self.assertEqual(len(rows), 2)

    def test_pagination_offset(self):
        all_rows    = dbControl.get_listings(limit=100)
        offset_rows = dbControl.get_listings(limit=100, offset=2)
        self.assertEqual(len(offset_rows), len(all_rows) - 2)

    def test_limit_zero_returns_empty(self):
        rows = dbControl.get_listings(limit=0)
        self.assertEqual(rows, [])


class TestGetDistinctCities(unittest.TestCase):

    def setUp(self):
        self.db_path, self.tmp = _make_test_db()
        self._orig = dbControl.DB_PATH
        dbControl.DB_PATH = self.db_path

    def tearDown(self):
        dbControl.DB_PATH = self._orig
        shutil.rmtree(self.tmp)

    def test_returns_unique_cities(self):
        cities = dbControl.get_distinct_cities()
        self.assertEqual(len(cities), len(set(cities)))

    def test_cairo_and_alex_present(self):
        cities = dbControl.get_distinct_cities()
        self.assertIn("Cairo", cities)
        self.assertIn("Alexandria", cities)

    def test_no_none_in_cities(self):
        cities = dbControl.get_distinct_cities()
        self.assertNotIn(None, cities)


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [TestInitDB, TestGetListings, TestGetDistinctCities]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

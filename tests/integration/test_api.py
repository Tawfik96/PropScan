"""
test_api.py
===========
Integration tests for the FastAPI app (main.py).
Uses TestClient — no live server needed.
The DB is isolated to a temp file per test.

Run:
    cd backend && python -m pytest ../tests/integration/test_api.py -v

Requirements:
    pip install httpx pytest
"""

import sys, os, json, tempfile, shutil, sqlite3, unittest
import tempfile

temp_db = tempfile.NamedTemporaryFile(delete=False)
os.environ["DB_PATH"] = temp_db.name

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

sys.path.insert(0, BACKEND_DIR)

# Patch DB_PATH before importing the app
import backend.dbControl as dbControl
_TMP_DIR = tempfile.mkdtemp()
_TEST_DB  = os.path.join(_TMP_DIR, "test_api.db")
dbControl.DB_PATH = _TEST_DB

from fastapi.testclient import TestClient
import backend.main as app_module
client = TestClient(app_module.app)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _seed_db(rows):
    """Insert rows directly so tests don't depend on Gemini."""
    dbControl.DB_PATH = _TEST_DB
    conn = dbControl.init_db()
    for r in rows:
        cols = ", ".join(r.keys())
        vals = ", ".join("?" * len(r))
        conn.execute(f"INSERT INTO listings ({cols}) VALUES ({vals})", list(r.values()))
    conn.commit()
    conn.close()

def _reset_db():
    if os.path.exists(_TEST_DB):
        os.remove(_TEST_DB)

SAMPLE_ROWS = [
    {
        "property_type": "apartment", "transaction_type": "sale",
        "price": 8000000, "currency": "EGP", "area_sqm": 130,
        "bedrooms": 3, "bathrooms": 2, "city": "Cairo",
        "district": "Rehab", "compound_name": "Rehab City",
        "phone_numbers": json.dumps(["+201011111111"]),
        "reference_id": "TEST001", "ad_date": "2024-09-28T13:00:00",
        "ad_snippet": "Apartment for sale in Rehab",
        "original_message": "Apartment for sale Rehab 3BR 8M",
        "sender": "+20 10 11111111",
    },
    {
        "property_type": "villa", "transaction_type": "rent",
        "price": 45000, "currency": "EGP", "area_sqm": 300,
        "bedrooms": 5, "bathrooms": 4, "city": "Cairo",
        "district": "New Cairo", "compound_name": "Mivida",
        "phone_numbers": json.dumps(["+201022222222"]),
        "reference_id": "TEST002", "ad_date": "2024-10-01T10:00:00",
        "ad_snippet": "Villa for rent in Mivida",
        "original_message": "Villa for rent Mivida 5BR 45k",
        "sender": "+20 10 22222222",
    },
    {
        "property_type": "apartment", "transaction_type": "rent",
        "price": 25000, "currency": "EGP", "area_sqm": 100,
        "bedrooms": 2, "bathrooms": 1, "city": "Alexandria",
        "district": "Smouha", "compound_name": None,
        "phone_numbers": json.dumps(["+201044444444"]),
        "reference_id": "TEST004", "ad_date": "2024-11-01T09:00:00",
        "ad_snippet": "Apartment for rent Alexandria",
        "original_message": "Apartment rent Smouha 25k",
        "sender": "+20 10 44444444",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
#  1. /health
# ─────────────────────────────────────────────────────────────────────────────

class TestHealth(unittest.TestCase):

    def test_health_returns_ok(self):
        r = client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")


# ─────────────────────────────────────────────────────────────────────────────
#  2. /listings — empty state
# ─────────────────────────────────────────────────────────────────────────────

class TestListingsEmpty(unittest.TestCase):

    def setUp(self):
        _reset_db()

    def test_listings_empty_db_returns_empty(self):
        r = client.get("/listings")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["listings"], [])
        self.assertEqual(body["count"], 0)
        self.assertIn("message", body)


# ─────────────────────────────────────────────────────────────────────────────
#  3. /listings — with data and filters
# ─────────────────────────────────────────────────────────────────────────────

class TestListingsFilters(unittest.TestCase):

    def setUp(self):
        _reset_db()
        _seed_db(SAMPLE_ROWS)

    def test_returns_all_listings(self):
        r = client.get("/listings")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["count"], 3)

    def test_filter_transaction_type_sale(self):
        r = client.get("/listings?transaction_type=sale")
        data = r.json()
        self.assertTrue(all(l["transaction_type"] == "sale" for l in data["listings"]))

    def test_filter_transaction_type_rent(self):
        r = client.get("/listings?transaction_type=rent")
        data = r.json()
        self.assertEqual(data["count"], 2)

    def test_filter_bedrooms(self):
        r = client.get("/listings?bedrooms=3")
        data = r.json()
        self.assertTrue(all(l["bedrooms"] == 3 for l in data["listings"]))

    def test_filter_city(self):
        r = client.get("/listings?city=Alexandria")
        data = r.json()
        self.assertEqual(data["count"], 1)

    def test_filter_price_min(self):
        r = client.get("/listings?price_min=5000000")
        data = r.json()
        self.assertTrue(all(l["price"] >= 5000000 for l in data["listings"]))

    def test_filter_price_max(self):
        r = client.get("/listings?price_max=50000")
        data = r.json()
        self.assertTrue(all(l["price"] <= 50000 for l in data["listings"]))

    def test_filter_property_type(self):
        r = client.get("/listings?property_type=villa")
        data = r.json()
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["listings"][0]["property_type"], "villa")

    def test_combined_filters(self):
        r = client.get("/listings?transaction_type=rent&city=Cairo")
        data = r.json()
        for l in data["listings"]:
            self.assertEqual(l["transaction_type"], "rent")
            self.assertEqual(l["city"], "Cairo")

    def test_no_match_returns_empty_with_message(self):
        r = client.get("/listings?city=Timbuktu")
        data = r.json()
        self.assertEqual(data["listings"], [])
        self.assertIn("message", data)

    def test_pagination_limit(self):
        r = client.get("/listings?limit=2")
        data = r.json()
        self.assertEqual(len(data["listings"]), 2)

    def test_pagination_offset(self):
        r1 = client.get("/listings?limit=10&offset=0")
        r2 = client.get("/listings?limit=10&offset=1")
        ids1 = [l["id"] for l in r1.json()["listings"]]
        ids2 = [l["id"] for l in r2.json()["listings"]]
        self.assertEqual(ids1[1:], ids2[:len(ids1)-1])

    def test_listings_include_expected_fields(self):
        r = client.get("/listings?limit=1")
        listing = r.json()["listings"][0]
        for field in ("id", "property_type", "transaction_type",
                      "price", "city", "bedrooms"):
            self.assertIn(field, listing)


# ─────────────────────────────────────────────────────────────────────────────
#  4. /cities
# ─────────────────────────────────────────────────────────────────────────────

class TestCities(unittest.TestCase):

    def setUp(self):
        _reset_db()
        _seed_db(SAMPLE_ROWS)

    def test_cities_endpoint_returns_list(self):
        r = client.get("/cities")
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.json()["cities"], list)

    def test_cities_are_unique(self):
        cities = client.get("/cities").json()["cities"]
        self.assertEqual(len(cities), len(set(cities)))

    def test_known_cities_present(self):
        cities = client.get("/cities").json()["cities"]
        self.assertIn("Cairo", cities)
        self.assertIn("Alexandria", cities)

    def test_no_null_in_cities(self):
        cities = client.get("/cities").json()["cities"]
        self.assertNotIn(None, cities)


# ─────────────────────────────────────────────────────────────────────────────
#  5. /upload — format validation (no Gemini call)
# ─────────────────────────────────────────────────────────────────────────────

class TestUploadValidation(unittest.TestCase):

    def test_upload_wrong_extension_returns_error_or_400(self):
        """Uploading a non-.txt file should fail gracefully."""
        r = client.post(
            "/upload",
            files={"file": ("data.pdf", b"%PDF fake content", "application/pdf")},
        )
        # Accept either a 400/422 or a 500 with error detail — not a 200
        self.assertNotEqual(r.status_code, 200)

    def test_upload_empty_file_does_not_crash(self):
        r = client.post(
            "/upload",
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        # Should return a response — not hang or 500 with unhandled exception
        self.assertIn(r.status_code, (200, 400, 422, 500))
        if r.status_code == 500:
            self.assertIn("detail", r.json())


# ─────────────────────────────────────────────────────────────────────────────

def teardown_module():
    shutil.rmtree(_TMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [TestHealth, TestListingsEmpty, TestListingsFilters,
                TestCities, TestUploadValidation]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

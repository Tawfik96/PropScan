"""
test_preprocessing.py
=====================
Unit tests for the preprocessing steps in extractFromChatExport.py:
  - get_recent_days()      — selects N most recent full days
  - crop_chat_by_date()    — date-range crop to a new file
  - build_extraction_prompt() — assembles Gemini prompt from ad list
  - filter_ads()           — wraps classify(), returns (ads, stats)
  - purge_old_listings()   — purge by batch anchor date

Run:
    cd backend && python -m pytest ../tests/unit/test_preprocessing.py -v
"""

import sys, os, unittest, tempfile, shutil, sqlite3
from datetime import datetime, date

temp_db = tempfile.NamedTemporaryFile(delete=False)
os.environ["DB_PATH"] = temp_db.name

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

sys.path.insert(0, BACKEND_DIR)
from backend.extractFromChatExport import (
    get_recent_days,
    filter_ads,
    build_extraction_prompt,
    crop_chat_by_date,
)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
# purge lives alongside
from backend.purge_old_listings import purge_old_listings

# ── Helpers ───────────────────────────────────────────────────────────────────

def _msg(body, dt):
    return {"sender": "+20 10 11111111", "body": body, "datetime": dt}

def _dt(year, month, day, hour=12, minute=0):
    return datetime(year, month, day, hour, minute)

# ─────────────────────────────────────────────────────────────────────────────
#  1. get_recent_days
# ─────────────────────────────────────────────────────────────────────────────

class TestGetRecentDays(unittest.TestCase):

    def _make_msgs(self, dates_and_bodies):
        return [_msg(b, d) for d, b in dates_and_bodies]

    def test_returns_last_1_day(self):
        msgs = self._make_msgs([
            (_dt(2025, 1, 1), "Ad from Jan 1"),
            (_dt(2025, 1, 2), "Ad from Jan 2"),
            (_dt(2025, 1, 3), "Ad from Jan 3"),
        ])
        result = get_recent_days(msgs, days=1)
        self.assertTrue(all(m["datetime"].date() == date(2025, 1, 3) for m in result))
        self.assertEqual(len(result), 1)

    def test_returns_last_2_days(self):
        msgs = self._make_msgs([
            (_dt(2025, 1, 1),  "Old"),
            (_dt(2025, 1, 2),  "Day 2 msg 1"),
            (_dt(2025, 1, 2, 15), "Day 2 msg 2"),
            (_dt(2025, 1, 3),  "Day 3"),
        ])
        result = get_recent_days(msgs, days=2)
        dates_in_result = {m["datetime"].date() for m in result}
        self.assertEqual(dates_in_result, {date(2025, 1, 2), date(2025, 1, 3)})
        self.assertNotIn(date(2025, 1, 1), dates_in_result)

    def test_empty_input_returns_empty(self):
        self.assertEqual(get_recent_days([], days=2), [])

    def test_single_day_export(self):
        msgs = self._make_msgs([
            (_dt(2025, 3, 4, 9),  "Morning ad"),
            (_dt(2025, 3, 4, 14), "Afternoon ad"),
        ])
        result = get_recent_days(msgs, days=2)
        # Only 1 day available — should return all
        self.assertEqual(len(result), 2)

    def test_days_gt_available_returns_all(self):
        msgs = self._make_msgs([
            (_dt(2025, 1, 1), "Ad 1"),
            (_dt(2025, 1, 2), "Ad 2"),
        ])
        result = get_recent_days(msgs, days=30)
        self.assertEqual(len(result), 2)

    def test_preserves_message_order(self):
        msgs = self._make_msgs([
            (_dt(2025, 1, 3, 8),  "Early"),
            (_dt(2025, 1, 3, 12), "Mid"),
            (_dt(2025, 1, 3, 18), "Late"),
        ])
        result = get_recent_days(msgs, days=1)
        self.assertEqual(result[0]["body"], "Early")
        self.assertEqual(result[-1]["body"], "Late")

    def test_multiple_msgs_same_minute_all_kept(self):
        msgs = [_msg(f"Ad {i}", _dt(2025, 1, 3, 10, 0)) for i in range(5)]
        result = get_recent_days(msgs, days=1)
        self.assertEqual(len(result), 5)


# ─────────────────────────────────────────────────────────────────────────────
#  2. filter_ads
# ─────────────────────────────────────────────────────────────────────────────

class TestFilterAds(unittest.TestCase):

    def test_stats_keys_present(self):
        ads, stats = filter_ads([])
        for key in ("system", "too_short", "blocklist", "no_keywords", "passed"):
            self.assertIn(key, stats)

    def test_valid_ads_pass(self):
        msgs = [
            _msg("Apartment for sale in Mivida 200 SQM 3BR Price 19,500,000", _dt(2024, 9, 28)),
            _msg("Villa for rent in Rehab 5 bedrooms Price 60k", _dt(2024, 9, 28)),
        ]
        ads, stats = filter_ads(msgs)
        self.assertEqual(stats["passed"], 2)
        self.assertEqual(len(ads), 2)

    def test_requests_dropped(self):
        msgs = [
            _msg("مطلوب شقه ايجار داخل كمبوند بادچيت 25 مساحه 180م", _dt(2024, 9, 28)),
        ]
        ads, stats = filter_ads(msgs)
        self.assertEqual(len(ads), 0)
        self.assertEqual(stats["passed"], 0)

    def test_mixed_batch(self):
        msgs = [
            _msg("Apartment for sale Mivida 200 SQM 19,500,000", _dt(2024, 9, 28)),  # pass
            _msg("صباح الخير", _dt(2024, 9, 28)),                                    # dropped
            _msg("null", _dt(2024, 9, 28)),                                           # dropped
            _msg("Villa for rent Rehab 5BR 60k fully furnished", _dt(2024, 9, 28)),  # pass
        ]
        ads, stats = filter_ads(msgs)
        self.assertEqual(stats["passed"], 2)
        total_dropped = stats["system"] + stats["too_short"] + stats["blocklist"] + stats["no_keywords"]
        self.assertEqual(total_dropped, 2)

    def test_stats_sum_equals_input(self):
        msgs = [_msg(f"test message {i}", _dt(2024, 9, 28)) for i in range(10)]
        ads, stats = filter_ads(msgs)
        total = stats["passed"] + stats["system"] + stats["too_short"] + stats["blocklist"] + stats["no_keywords"]
        self.assertEqual(total, 10)


# ─────────────────────────────────────────────────────────────────────────────
#  3. build_extraction_prompt
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildExtractionPrompt(unittest.TestCase):

    def _make_ad(self, body, n=1):
        return {"sender": f"+20 10 {n:08d}", "body": body,
                "datetime": _dt(2024, 9, 28)}

    def test_prompt_contains_ad_body(self):
        ads = [self._make_ad("Apartment for sale Mivida 3BR 19.5M")]
        prompt = build_extraction_prompt(ads)
        self.assertIn("Apartment for sale Mivida", prompt)

    def test_prompt_numbers_ads(self):
        ads = [self._make_ad(f"Ad body {i}", i) for i in range(3)]
        prompt = build_extraction_prompt(ads)
        self.assertIn("AD 1", prompt)
        self.assertIn("AD 2", prompt)
        self.assertIn("AD 3", prompt)

    def test_prompt_includes_sender(self):
        ads = [self._make_ad("Some ad body")]
        prompt = build_extraction_prompt(ads)
        self.assertIn("+20 10", prompt)

    def test_prompt_includes_date(self):
        ads = [self._make_ad("Some ad body")]
        prompt = build_extraction_prompt(ads)
        self.assertIn("2024-09-28", prompt)

    def test_batch_of_10_all_included(self):
        ads = [self._make_ad(f"Apartment for sale compound_{i} 3BR 10M", i) for i in range(10)]
        prompt = build_extraction_prompt(ads)
        for i in range(1, 11):
            self.assertIn(f"AD {i}", prompt)

    def test_empty_batch_returns_string(self):
        prompt = build_extraction_prompt([])
        self.assertIsInstance(prompt, str)


# ─────────────────────────────────────────────────────────────────────────────
#  4. crop_chat_by_date
# ─────────────────────────────────────────────────────────────────────────────

class TestCropChatByDate(unittest.TestCase):

    CHAT_CONTENT = (
        "28/09/2024, 1:31 pm - +20 11 00000001: September ad price 5M\n"
        "15/10/2024, 9:00 am - +20 11 00000002: October ad price 8M\n"
        "01/11/2024, 10:00 am - +20 11 00000003: November ad price 12M\n"
        "15/01/2025, 9:30 am - +20 11 00000004: January 2025 ad price 9M\n"
    )

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.chat_path = os.path.join(self.tmp, "chat.txt")
        with open(self.chat_path, "w", encoding="utf-8") as f:
            f.write(self.CHAT_CONTENT)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_crops_to_single_day(self):
        out = crop_chat_by_date(self.chat_path, 15, 10, 2024, 15, 10, 2024)
        with open(out) as f:
            content = f.read()
        self.assertIn("October ad", content)
        self.assertNotIn("September ad", content)
        self.assertNotIn("November ad", content)

    def test_crops_to_date_range(self):
        out = crop_chat_by_date(self.chat_path, 15, 10, 2024, 1, 11, 2024)
        with open(out) as f:
            content = f.read()
        self.assertIn("October ad", content)
        self.assertIn("November ad", content)
        self.assertNotIn("September ad", content)

    def test_output_filename_contains_dates(self):
        out = crop_chat_by_date(self.chat_path, 1, 10, 2024, 31, 10, 2024)
        self.assertIn("01102024", out)
        self.assertIn("31102024", out)

    def test_empty_range_produces_empty_file(self):
        out = crop_chat_by_date(self.chat_path, 1, 6, 2023, 30, 6, 2023)
        with open(out) as f:
            content = f.read().strip()
        self.assertEqual(content, "")

    def test_raises_on_inverted_dates(self):
        with self.assertRaises(ValueError):
            crop_chat_by_date(self.chat_path, 31, 12, 2024, 1, 1, 2024)


# ─────────────────────────────────────────────────────────────────────────────
#  5. purge_old_listings
# ─────────────────────────────────────────────────────────────────────────────

class TestPurgeOldListings(unittest.TestCase):

    def setUp(self):
        self.tmp    = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test_purge.db")
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT, ad_date TEXT, body TEXT
            )
        """)
        conn.commit()
        conn.close()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _insert(self, rows):
        conn = sqlite3.connect(self.db_path)
        conn.executemany(
            "INSERT INTO listings (sender, ad_date, body) VALUES (?, ?, ?)", rows
        )
        conn.commit()
        conn.close()

    def _count(self):
        conn = sqlite3.connect(self.db_path)
        n = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
        conn.close()
        return n

    def test_deletes_rows_before_cutoff(self):
        self._insert([
            ("A", "2023-07-01T10:00:00", "old ad"),
            ("B", "2024-09-28T13:00:00", "new ad"),
        ])
        # batch_earliest = Sept 2024 → cutoff = Aug 2024 → July 2023 gets deleted
        purge_old_listings(self.db_path, batch_earliest="2024-09-28T13:00:00")
        self.assertEqual(self._count(), 1)

    def test_keeps_rows_within_window(self):
        self._insert([
            ("A", "2024-09-01T10:00:00", "just outside?"),
            ("B", "2024-09-28T13:00:00", "batch start"),
            ("C", "2025-01-01T10:00:00", "future row"),
        ])
        purge_old_listings(self.db_path, batch_earliest="2024-09-28T13:00:00")
        # cutoff = 2024-08-28 → all 3 rows are >= 2024-09-01 so all kept
        self.assertEqual(self._count(), 3)

    def test_empty_db_returns_empty_dict(self):
        result = purge_old_listings(self.db_path)
        self.assertEqual(result, {})

    def test_returns_correct_counts(self):
        self._insert([
            ("A", "2023-06-01T10:00:00", "old 1"),
            ("B", "2023-06-15T10:00:00", "old 2"),
            ("C", "2024-09-28T13:00:00", "new"),
        ])
        result = purge_old_listings(self.db_path, batch_earliest="2024-09-28T13:00:00")
        self.assertEqual(result["deleted_count"],   2)
        self.assertEqual(result["remaining_count"], 1)

    def test_cutoff_is_exactly_one_month_before(self):
        result = purge_old_listings.__wrapped__ if hasattr(purge_old_listings, "__wrapped__") else None
        # Verify via returned dict
        self._insert([("A", "2025-03-04T09:00:00", "ad")])
        result = purge_old_listings(self.db_path, batch_earliest="2025-03-04T09:00:00")
        cutoff = result.get("cutoff_date", "")
        self.assertTrue(cutoff.startswith("2025-02-04"), f"Expected 2025-02-04, got {cutoff}")

    def test_batch_earliest_overrides_db_min(self):
        # DB has a 2020 row — without batch_earliest it would anchor to 2020
        self._insert([
            ("A", "2020-01-01T00:00:00", "very old"),
            ("B", "2024-09-28T13:00:00", "new batch"),
        ])
        result = purge_old_listings(self.db_path, batch_earliest="2024-09-28T13:00:00")
        # cutoff = 2024-08-28; 2020 row should be deleted
        self.assertEqual(result["deleted_count"], 1)
        self.assertEqual(self._count(), 1)


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [TestGetRecentDays, TestFilterAds,
                TestBuildExtractionPrompt, TestCropChatByDate,
                TestPurgeOldListings]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

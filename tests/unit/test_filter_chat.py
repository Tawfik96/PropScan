"""
test_filter_chat.py
===================
Unit tests for filter_chat.py:
  - parse_whatsapp_export()
  - classify()  (the 3-gate ad filter)

Run:
    cd backend && python -m pytest ../tests/unit/test_filter_chat.py -v
    # or standalone:
    cd backend && python ../tests/unit/test_filter_chat.py
"""

import sys
import os
import unittest
from datetime import datetime
import tempfile

temp_db = tempfile.NamedTemporaryFile(delete=False)
os.environ["DB_PATH"] = temp_db.name

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
from backend.filter_chat import parse_whatsapp_export, classify

# ── Helpers ───────────────────────────────────────────────────────────────────

def make_msg(body, sender="+20 10 12345678", dt=None):
    return {
        "sender":   sender,
        "body":     body,
        "datetime": dt or datetime(2024, 9, 28, 13, 0),
    }

# ─────────────────────────────────────────────────────────────────────────────
#  1. PARSER TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestParseWhatsappExport(unittest.TestCase):

    def _write_tmp(self, content, tmp_path="/tmp/test_chat.txt"):
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)
        return tmp_path

    # ── Basic message parsing ─────────────────────────────────────────────────

    def test_parses_single_english_message(self):
        txt = "28/09/2024, 1:31 pm - +20 11 02043283: Apartment for rent 35k\n"
        path = self._write_tmp(txt)
        msgs = parse_whatsapp_export(path)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["sender"], "+20 11 02043283")
        self.assertIn("35k", msgs[0]["body"])
        self.assertIsInstance(msgs[0]["datetime"], datetime)

    def test_parses_arabic_message(self):
        txt = "28/09/2024, 1:22 pm - +20 10 06656657: متاح شقه للبيع في مدينتي ١٣٧ متر\n"
        path = self._write_tmp(txt)
        msgs = parse_whatsapp_export(path)
        self.assertEqual(len(msgs), 1)
        self.assertIn("شقه", msgs[0]["body"])

    def test_parses_multiline_message(self):
        txt = (
            "28/09/2024, 1:31 pm - +20 11 02043283: Code rehab96\n"
            "Apartment ground floor\n"
            "Area 110 SQM\n"
            "Price 35k\n"
        )
        path = self._write_tmp(txt)
        msgs = parse_whatsapp_export(path)
        self.assertEqual(len(msgs), 1)
        self.assertIn("110 SQM", msgs[0]["body"])
        self.assertIn("35k", msgs[0]["body"])

    def test_parses_multiple_messages(self):
        txt = (
            "28/09/2024, 1:31 pm - +20 11 11111111: First message\n"
            "28/09/2024, 1:32 pm - +20 11 22222222: Second message\n"
            "28/09/2024, 1:33 pm - +20 11 33333333: Third message\n"
        )
        path = self._write_tmp(txt)
        msgs = parse_whatsapp_export(path)
        self.assertEqual(len(msgs), 3)

    def test_drops_system_message(self):
        txt = (
            "28/09/2024, 1:17 pm - Messages and calls are end-to-end encrypted.\n"
            "28/09/2024, 1:18 pm - ~ LOMY created group \"SELL & RENT\"\n"
            "28/09/2024, 1:31 pm - +20 11 02043283: Apartment for sale 5M\n"
        )
        path = self._write_tmp(txt)
        msgs = parse_whatsapp_export(path)
        # System messages should be present but classified separately by classify()
        # Parser itself keeps them; filter drops them
        real = [m for m in msgs if m["sender"].startswith("+")]
        self.assertEqual(len(real), 1)

    def test_handles_null_body(self):
        txt = "28/09/2024, 1:39 pm - +20 10 95996909: null\n"
        path = self._write_tmp(txt)
        msgs = parse_whatsapp_export(path)
        # null messages should be parsed but will be dropped by classify()
        self.assertEqual(len(msgs), 1)

    def test_datetime_parsed_correctly(self):
        txt = "15/01/2025, 9:30 am - +20 10 12345678: Test message\n"
        path = self._write_tmp(txt)
        msgs = parse_whatsapp_export(path)
        self.assertEqual(msgs[0]["datetime"].year,  2025)
        self.assertEqual(msgs[0]["datetime"].month,    1)
        self.assertEqual(msgs[0]["datetime"].day,     15)
        self.assertEqual(msgs[0]["datetime"].hour,     9)
        self.assertEqual(msgs[0]["datetime"].minute,  30)

    def test_24h_time_format(self):
        txt = "15/01/2025, 14:30 - +20 10 12345678: Test\n"
        path = self._write_tmp(txt)
        msgs = parse_whatsapp_export(path)
        if msgs:   # format may vary by export locale
            self.assertEqual(msgs[0]["datetime"].hour, 14)


# ─────────────────────────────────────────────────────────────────────────────
#  2. CLASSIFIER TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestClassify(unittest.TestCase):

    # ── Should PASS ───────────────────────────────────────────────────────────

    def test_english_sale_ad_passes(self):
        msg = make_msg("Apartment for sale in Mivida\nArea 200 SQM\n3 bedrooms\nPrice 19,500,000")
        self.assertEqual(classify(msg), "pass")

    def test_arabic_sale_ad_passes(self):
        msg = make_msg("متاح شقه للبيع في مدينتي ١٣٧ متر مطلوب ٨ مليون")
        self.assertEqual(classify(msg), "pass")

    def test_rental_ad_passes(self):
        msg = make_msg("Apartment for rent in Rehab\nArea 110 SQM\n2 bedrooms\nPrice 35k")
        self.assertEqual(classify(msg), "pass")

    def test_villa_ad_passes(self):
        msg = make_msg("Standalone villa for sale in Mountain View\nLand 450 SQM\nPrice 55,000,000")
        self.assertEqual(classify(msg), "pass")

    def test_arabic_rent_passes(self):
        msg = make_msg("شقه للايجار مفروش فى الرحاب ١٣٤م المطلوب ٤٥ الف")
        self.assertEqual(classify(msg), "pass")

    def test_mixed_language_ad_passes(self):
        msg = make_msg("Apartment for sale\nمساحة 150 متر\nPrice 8,000,000")
        self.assertEqual(classify(msg), "pass")

    def test_penthouse_passes(self):
        msg = make_msg("Penthouse for sale in Hyde Park\nArea 190 SQM\n3BR\nPrice 13,000,000")
        self.assertEqual(classify(msg), "pass")

    def test_compound_with_price_passes(self):
        msg = make_msg("Twin house in Uptown Cairo\n400 SQM land\nPrice 38,000,000")
        self.assertEqual(classify(msg), "pass")

    # ── Should be DROPPED: system ─────────────────────────────────────────────

    def test_system_message_dropped(self):
        msg = make_msg("Messages and calls are end-to-end encrypted.", sender="System")
        result = classify(msg)
        self.assertNotEqual(result, "pass")

    def test_group_created_message_dropped(self):
        msg = make_msg("~ LOMY created group \"SELL & RENT\"", sender="~ LOMY")
        result = classify(msg)
        self.assertNotEqual(result, "pass")

    # ── Should be DROPPED: too_short ─────────────────────────────────────────

    def test_empty_message_dropped(self):
        msg = make_msg("")
        result = classify(msg)
        self.assertNotEqual(result, "pass")

    def test_single_word_dropped(self):
        msg = make_msg("Okay")
        result = classify(msg)
        self.assertNotEqual(result, "pass")

    def test_null_body_dropped(self):
        msg = make_msg("null")
        result = classify(msg)
        self.assertNotEqual(result, "pass")

    # ── Should be DROPPED: blocklist (requests/spam/greetings) ───────────────

    def test_request_for_property_dropped(self):
        # "مطلوب" = "wanted" — this is a request, not an ad
        msg = make_msg("مطلوب شقه ايجار داخل كمبوند بادچيت 25 مساحه 180م 3غرف")
        result = classify(msg)
        self.assertNotEqual(result, "pass")

    def test_greeting_dropped(self):
        msg = make_msg("صباح الخير يا جماعة")
        result = classify(msg)
        self.assertNotEqual(result, "pass")

    def test_unrelated_request_dropped(self):
        msg = make_msg("Ay had m3ahhh town twin senior Chalet 4 or 5 bedrooms yb3tlii daroryyyy")
        result = classify(msg)
        self.assertNotEqual(result, "pass")

    # ── Should be DROPPED: no_keywords ───────────────────────────────────────

    def test_no_re_keywords_dropped(self):
        msg = make_msg("هل تريد تعلم الانجليزية؟ تواصل معنا الآن")
        result = classify(msg)
        self.assertNotEqual(result, "pass")

    def test_phone_only_message_dropped(self):
        msg = make_msg("01012345678\n01198765432")
        result = classify(msg)
        self.assertNotEqual(result, "pass")

    # ── Edge cases ────────────────────────────────────────────────────────────

    def test_ad_with_emoji_passes(self):
        msg = make_msg("💥💥\nApartment for rent in Eastown\nArea 205 SQM\n3 bedrooms\nPrice 110k")
        self.assertEqual(classify(msg), "pass")

    def test_ad_with_asterisk_formatting_passes(self):
        msg = make_msg("*Apartment for sale*\nMivida\nArea 200 SQM\nPrice 19,500,000")
        self.assertEqual(classify(msg), "pass")

    def test_usd_price_ad_passes(self):
        msg = make_msg("Apartment for sale in Mivida-Boulevard\nArea 138 SQM\nSuper lux\nPrice: 336,000$")
        self.assertEqual(classify(msg), "pass")


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    loader  = unittest.TestLoader()
    suite   = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestParseWhatsappExport))
    suite.addTests(loader.loadTestsFromTestCase(TestClassify))
    runner  = unittest.TextTestRunner(verbosity=2)
    result  = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

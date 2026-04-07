# PropScan — Complete Testing Plan

## Overview

This document covers the full testing strategy for PropScan. Tests are split into
four layers that build on each other: **Unit → Preprocessing → Integration → Ground Truth**.
All test files live in `tests/` and can be run individually or via the master runner.

---

## Directory Structure

```
tests/
├── run_all_tests.py                   ← master runner
│
├── unit/
│   ├── test_filter_chat.py            ← parser + 3-gate classifier
│   ├── test_db_control.py             ← SQLite CRUD + schema
│   └── test_preprocessing.py         ← pipeline steps + purge
│
├── integration/
│   └── test_api.py                    ← FastAPI endpoints (TestClient)
│
├── ground_truth/
│   ├── seed_ground_truth.py           ← creates ground_truth.db
│   ├── compare_to_ground_truth.py     ← compares LLM output vs GT
│   └── comparison_report.csv         ← auto-generated after each compare run
│
└── fixtures/
    ├── gt_chat.txt                    ← 10 hand-verified messages (GT source)
    └── test_chat_purge.txt            ← 43 messages for purge testing
```

---

## Layer 1 — Unit Tests: Filter & Parser

**File:** `unit/test_filter_chat.py`
**What it tests:** `filter_chat.py` — the WhatsApp parser and 3-gate ad classifier.

### Parser tests (`TestParseWhatsappExport`)

| Test | Checks |
|---|---|
| Single English message | Correct sender, body, datetime |
| Arabic message | Arabic body preserved correctly |
| Multi-line message | Continuation lines joined to body |
| Multiple messages | All messages parsed independently |
| System message handling | System lines don't appear as user messages |
| Null body | `null` string parsed without crashing |
| Datetime accuracy | year, month, day, hour, minute all correct |
| 24h time format | `14:30` parsed as 14:00, not 2:30 AM |

### Classifier tests (`TestClassify`)

**Should PASS (become ads):**
- English sale ad with price + area
- Arabic sale ad with Arabic numerals
- Rental ad in English
- Villa / standalone listing
- Arabic rental with فندقي/مفروش keywords
- Mixed Arabic/English ad
- Penthouse listing
- Ad with compound name + price
- Ad with emoji prefix (`💥💥`)
- Ad with `*bold*` WhatsApp formatting
- Ad with USD price (`336,000$`)

**Should be DROPPED:**
- System message / group created notification → `system`
- Empty body → `too_short`
- Single word ("Okay") → `too_short`
- `null` body → `too_short`
- "مطلوب" requests (wanted ads, not listings) → `blocklist`
- Greetings ("صباح الخير") → `blocklist`
- Random requests ("ay had m3ah chalet yb3tlii") → `blocklist`
- Non-RE message (language school ad) → `no_keywords`
- Phone numbers only → `no_keywords`

---

## Layer 2 — Unit Tests: Preprocessing Pipeline

**File:** `unit/test_preprocessing.py`
**What it tests:** pipeline helper functions in `extractFromChatExport.py` + `purge_old_listings.py`.

### `get_recent_days()`

| Test | Input → Expected |
|---|---|
| 1-day slice | 3-day export → only last day returned |
| 2-day slice | 4-day export → last 2 days returned |
| Empty input | `[]` → `[]` |
| Single-day export | All messages returned regardless of `days` param |
| `days` > available | Returns all messages |
| Message order preserved | Earliest message still first in result |
| Multiple same-minute messages | All kept |

### `filter_ads()` (wraps classify)

- Stats dict always has all 5 keys
- Valid ads pass through
- Requests/greetings dropped
- Mixed batch: counts match exactly
- Total of (passed + dropped) == len(input)

### `build_extraction_prompt()`

- Ad body present in output
- `AD 1`, `AD 2`, `AD 3` labels present
- Sender phone included
- ISO date included
- Batch of 10: all 10 labeled
- Empty batch returns a string (no crash)

### `crop_chat_by_date()`

- Single-day crop: only that day's messages in output
- Date range crop: messages from start and end date both included
- Output filename contains start/end dates
- Empty date range produces empty file
- Inverted dates raise `ValueError`

### `purge_old_listings()`

| Test | Scenario |
|---|---|
| Rows before cutoff deleted | 2023 row + 2024 batch → 2023 row gone |
| Rows within window kept | Sep 2024 row stays when batch anchor = Sep 2024 |
| Empty DB returns `{}` | No crash on empty table |
| Return dict has correct counts | `deleted_count` and `remaining_count` accurate |
| Cutoff is exactly 1 calendar month | `2025-03-04` batch → cutoff `2025-02-04` |
| `batch_earliest` overrides DB MIN | 2020 row purged when batch anchor is 2024 |

---

## Layer 3 — Unit Tests: Database CRUD

**File:** `unit/test_db_control.py`
**What it tests:** `dbControl.py` — init, insert, query, cities.

### Schema / init (`TestInitDB`)

- `listings` table created
- `has_listings_table()` returns False before init
- `init_db()` is idempotent (safe to call twice)
- All required columns exist: `property_type`, `transaction_type`, `price`, `city`, `bedrooms`, `ad_date`, `phone_numbers`

### Filtering (`TestGetListings`)

| Filter | Verifies |
|---|---|
| No filter | All 4 seeded rows returned |
| `transaction_type=sale` | Only sale rows, count=2 |
| `transaction_type=rent` | Only rent rows |
| `bedrooms=3` | Only 3BR listings |
| `city=Alexandria` | Only Alexandria row |
| `price_min=10000000` | All prices ≥ 10M |
| `price_max=50000` | All prices ≤ 50k |
| Price range | Both bounds respected |
| `property_type=penthouse` | Exactly 1 row |
| Combined filters | All active filters applied (AND logic) |
| No match | Returns `[]`, not an error |
| `limit=2` | Exactly 2 rows returned |
| `offset=2` | Row IDs shifted by 2 |
| `limit=0` | Returns `[]` |

### Cities (`TestGetDistinctCities`)

- Returns only unique cities
- Cairo and Alexandria present after seeding
- No `None` in the list

---

## Layer 4 — Integration Tests: API

**File:** `integration/test_api.py`
**What it tests:** `main.py` FastAPI app via `TestClient` (no live server needed).

### `GET /health`
- Returns `200` with `{"status": "ok"}`

### `GET /listings` — empty state
- Returns `200` with `listings: []`, `count: 0`, and a `message` field

### `GET /listings` — with data
Same filters as CRUD tests, verified end-to-end through the HTTP layer:
- All listings returned with no filter
- `transaction_type`, `bedrooms`, `city`, `price_min/max`, `property_type` all filter correctly
- Combined filters work
- No match returns `[]` with `message`
- `limit` and `offset` pagination work
- Response objects contain expected fields: `id`, `property_type`, `transaction_type`, `price`, `city`, `bedrooms`

### `GET /cities`
- Returns `200` with `cities` list
- Cities are unique
- Known cities present
- No `null` in list

### `POST /upload`
- Uploading a non-`.txt` file returns a non-200 status (graceful rejection)
- Uploading an empty `.txt` file returns a structured response (no unhandled 500)

---

## Layer 5 — Ground Truth Comparison

This layer answers: **"How accurately does Gemini extract the structured fields?"**

### How it works

1. `fixtures/gt_chat.txt` contains 10 messages from the real WhatsApp export.
2. `seed_ground_truth.py` creates `ground_truth.db` with hand-annotated correct extractions for all 10 messages. Every field was set by a human reviewer.
3. You run the real PropScan pipeline on `gt_chat.txt` → it produces `llm_output.db` via Gemini.
4. `compare_to_ground_truth.py` matches rows (by `reference_id`, then by compound+bedrooms+area+type as fallback) and scores each field.

### Field comparison types

| Type | Fields | Logic |
|---|---|---|
| `exact` | `property_type`, `transaction_type`, `currency`, `reference_id`, `finishing`, `furnished` | Exact string match (case-insensitive) |
| `numeric` | `price`, `area_sqm`, `bedrooms`, `bathrooms`, `down_payment`, `garden_area_sqm` | ±5% tolerance |
| `bool` | `has_garden`, `has_pool`, `has_balcony` | True/False match |
| `json_list` | `phone_numbers` | Phone numbers normalized then compared as sets |
| `text_loose` | `city`, `district`, `compound_name` | Substring match (GT value must appear in LLM value) |

### Scoring

- Each field scored as `ok`, `fail`, `miss` (field present but wrong), or `skip` (null in both)
- **Critical fields** (`property_type`, `transaction_type`, `price`, `currency`, `bedrooms`, `area_sqm`, `compound_name`) weighted **2×** in the final score
- Overall score: 0–100

### Grade thresholds

| Score | Grade |
|---|---|
| ≥ 90 | EXCELLENT ✓✓ |
| ≥ 75 | GOOD ✓ |
| ≥ 55 | FAIR ⚠ |
| < 55 | POOR ✗ |

### Adding your own GT rows

Edit `seed_ground_truth.py` → add entries to `GT_ROWS`. Add the matching raw message to `fixtures/gt_chat.txt`. Re-run the seeder.

---

## How to Run

### Setup

```bash
cd backend
pip install -r requirements.txt
pip install pytest httpx python-dateutil
```

### Run all unit tests (no API key, no network)

```bash
python tests/run_all_tests.py --unit-only
```

### Run all tests including API integration

```bash
python tests/run_all_tests.py
```

### Run a single test file

```bash
cd backend
python -m pytest ../tests/unit/test_filter_chat.py -v
python -m pytest ../tests/unit/test_preprocessing.py -v
python -m pytest ../tests/unit/test_db_control.py -v
python -m pytest ../tests/integration/test_api.py -v
```

### Run ground truth comparison

```bash
# Step 1: Seed the GT database (run once)
python tests/ground_truth/seed_ground_truth.py

# Step 2: Run PropScan pipeline on the GT fixture (requires GEMINI_API_KEY)
cd backend
python extractFromChatExport.py  # after pointing chat_file to tests/fixtures/gt_chat.txt
# This produces listings.db

# Step 3: Compare
python tests/run_all_tests.py --compare backend/listings.db
# or directly:
python tests/ground_truth/compare_to_ground_truth.py backend/listings.db
```

### Run purge test only

```bash
cd backend
python test_purge.py
```

---

## What Is NOT Tested Here

| Gap | Reason | Suggested approach |
|---|---|---|
| Gemini output quality | Non-deterministic LLM | Covered by GT comparison layer |
| WhatsApp export format variations (iOS vs Android) | Format differs by locale | Add more fixtures per format |
| Concurrent uploads | Requires a live server | Use `locust` or `pytest-asyncio` |
| Frontend UI logic | JavaScript | Add Jest tests for `app.js` |
| Very large files (100k+ messages) | Requires real data | Benchmark test with timing assertions |

---

## Quick Reference

```bash
# All unit tests, fast, no external dependencies:
python tests/run_all_tests.py --unit-only

# Full suite:
python tests/run_all_tests.py

# After a real pipeline run, check Gemini accuracy:
python tests/run_all_tests.py --compare listings.db
```

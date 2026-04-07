# PropScan Test Fix TODO
Status: Started (approved by user)

## Plan Breakdown (Logical Steps):

### Step 1: Fix backend/dbControl.py [COMPLETED]
- [x] Reorder functions (has_listings_table before init_db)
- [x] Implement complete init_db(): CREATE TABLE listings with full schema (16+ columns from test_db_control.py samples)
  - Columns: id, property_type, transaction_type, price (REAL), currency (TEXT), area_sqm (REAL), bedrooms (INT), bathrooms (INT), city (TEXT), district (TEXT), compound_name (TEXT), phone_numbers (TEXT/JSON), reference_id (TEXT), ad_date (TEXT), ad_snippet (TEXT), original_message (TEXT), sender (TEXT)
  - Add optional: amenities (TEXT/JSON), price_negotiable (BOOLEAN), has_elevator/garden/pool/balcony/security/parking (BOOLEAN)
- [x] Fix get_listings(): Safe JSON loads with try/except or defaults, handle missing columns with row.get(), preserve filters/pagination
- [x] Make init_db() return connection for test_db_control.py compatibility

### Step 2: Test DB fixes [COMPLETED]
- [x] Rerun `python tests/run_all_tests.py` 
- [x] test_db_control.py passes (21 tests ✓)
- [x] preprocessing.py passes (29 tests ✓ after fixing extractFromChatExport.py import)

### Step 3: Fix test_preprocessing.py (FileNotFoundError)
- [ ] Identify missing fixture (e.g., create tests/fixtures/sample_chat.txt if absent)
- [ ] [ ] Rerun tests

### Step 4: Fix test_api.py (RuntimeError TestClient)
- [ ] Check if backend/main.py exists and has FastAPI app
- [ ] [ ] Fix imports/app definition
- [ ] Rerun full suite

### Step 5: Final validation
- [ ] All tests pass ✓
- [ ] attempt_completion

Next action: Edit backend/dbControl.py

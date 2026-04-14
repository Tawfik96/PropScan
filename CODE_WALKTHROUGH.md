# PropScan Code Walkthrough And Refactor Notes

This walkthrough explains the main application path: the browser UI, the FastAPI API, the database layer, and the Gemini extraction pipeline entry point.

The project turns a WhatsApp chat export into searchable real estate listing cards.

## Big Picture

1. `frontend/index.html` defines the page: import button, filters, progress overlay, and listing grid.
2. `frontend/app.js` makes the page interactive: uploads files, polls progress, fetches listings, filters results, and renders cards.
3. `backend/main.py` exposes the FastAPI endpoints used by the frontend.
4. `backend/test_ImprovedPromptCompact.py` parses the chat, filters likely ads, batches them, calls Gemini, and writes extracted listings into SQLite.
5. `backend/dbControl.py` reads listings and city values from SQLite for the API.
6. `backend/paths.py` centralizes file paths so the database, progress file, upload file, and cost file are always created in the backend folder.

## `backend/main.py`

| Line(s) | What it does |
| --- | --- |
| 1 | Imports FastAPI tools for building endpoints, accepting uploads, reading uploaded files, and defining query params. |
| 2 | Imports CORS middleware so the frontend can call the backend from another origin. |
| 3 | Imports `JSONResponse` so errors can be returned with custom status codes. |
| 4 | Imports `Optional` for query parameters that may be missing. |
| 5 | Imports `json` for reading `progress.json`. |
| 6 | Imports `JSONDecodeError` so corrupted/empty progress files can be handled safely. |
| 7 | Imports `run_in_threadpool` so the blocking extraction pipeline does not block the async FastAPI event loop. |
| 9-15 | Imports local backend modules. The `try` supports package imports like `backend.main`; the fallback supports running from inside `backend/`. |
| 17 | Creates the FastAPI app and gives it a title. |
| 19-24 | Enables CORS for all origins, methods, and headers. This is permissive and convenient for local development. |
| 26 | Checks whether the listings table exists when the app starts. |
| 30 | Registers the `GET /progress` endpoint. |
| 31 | Defines the progress handler. |
| 32-34 | Opens the progress file and returns its JSON content. |
| 35-36 | If the progress file is missing or invalid, returns a safe empty progress state. |
| 38 | Registers the `POST /reset-progress` endpoint. |
| 39 | Defines the reset handler. |
| 40 | Calls the pipeline helper to reset progress before a new upload starts. |
| 41 | Returns a small success response. |
| 43 | Registers the `POST /upload` endpoint. |
| 44 | Accepts one uploaded file from the request. |
| 45 | Starts error handling for the upload process. |
| 46 | Uses the centralized upload path from `paths.py`. |
| 48-49 | Writes the uploaded chat file to disk. |
| 51 | Runs the extraction pipeline in a worker thread, passing the saved file path and a `days=2` window. |
| 52 | Returns success when the pipeline finishes. |
| 54-55 | Converts unexpected upload/pipeline errors into a JSON 500 response. |
| 57 | Registers the `GET /listings` endpoint. |
| 58-67 | Defines optional filters: price range, bedrooms, city, transaction type, property type, plus validated pagination. |
| 68-73 | If the database table does not exist yet, returns an empty result with a helpful message. |
| 75-84 | Calls `dbControl.get_listings()` with the requested filters. |
| 86-91 | If the query returns no rows, returns an empty result with a message. |
| 93 | Returns the listings plus a count. |
| 96-98 | `GET /cities` returns distinct city names for the city filter dropdown. |
| 101-103 | `GET /health` returns a simple backend health check. |

## `backend/dbControl.py`

| Line(s) | What it does |
| --- | --- |
| 1 | Imports SQLite support. |
| 3-6 | Imports the database path from `paths.py`, supporting both package and script-style imports. |
| 8 | Defines a default maximum number of listing rows. |
| 11 | Defines a helper for opening a database connection. |
| 12 | Connects to the shared SQLite database path. |
| 13 | Makes query rows behave like dictionaries keyed by column name. |
| 14 | Returns the open connection. |
| 17-18 | Initializes database access by checking whether the listings table exists. |
| 21 | Defines a helper that checks for the `listings` table. |
| 22 | Opens the database. |
| 23-27 | Queries SQLite metadata and returns `True` if the table exists. |
| 28-29 | Always closes the connection. |
| 33-37 | Defines `get_listings()` and accepts the same filter values exposed by the API. |
| 38-39 | If no listings table exists, returns an empty list instead of crashing. |
| 41 | Opens the database. |
| 42 | Starts a `try/finally` block so the connection closes even if a query fails. |
| 43 | Starts a SQL query with `WHERE 1=1`, which makes appending `AND` filters simple. |
| 44 | Creates the list of SQL parameters. |
| 46-63 | Adds SQL filters only for values the user supplied. Parameters are used instead of string interpolation, which avoids SQL injection. |
| 65-66 | Adds sorting and pagination. |
| 68-69 | Executes the query and converts SQLite rows into normal dictionaries. |
| 70-71 | Closes the connection. |
| 74 | Defines `get_distinct_cities()`. |
| 75-76 | Returns an empty list when there is no listings table. |
| 78-83 | Reads unique non-empty cities sorted alphabetically. |
| 84-85 | Closes the connection. |

## `frontend/app.js`

| Line(s) | What it does |
| --- | --- |
| 1 | Stores the backend API base URL. |
| 3-15 | Auto-resizes the inquiry textarea as the user types. |
| 17-23 | Stores inline SVG icons used by buttons and empty states. |
| 25-33 | Defines `showToast()`, which displays temporary success/error messages. |
| 35-48 | Defines `copyText()`, copying text to the clipboard and briefly changing the button icon to a checkmark. |
| 50-74 | Defines `applyHighlights()`, which merges overlapping highlight ranges, escapes unsafe HTML, and wraps highlighted text in `<mark>`. |
| 76-78 | Defines `escapeHtml()`, protecting rendered text from being interpreted as HTML. |
| 80-83 | Defines `formatValue()`, showing a dash when values are empty. |
| 85-112 | Defines `getOrganizedDetailsRows()`, which turns listing fields into display rows. Optional district and compound rows only appear when present. |
| 114-121 | Turns detail rows into HTML for the card details table. |
| 123-125 | Turns detail rows into plain text for copy-to-clipboard. |
| 128-168 | Defines progress polling. It calls `/progress`, updates the progress bar, and runs a completion callback when the backend marks the upload as done. |
| 170-174 | Resets the progress overlay UI before a new import. |
| 176-270 | Defines `renderCards()`, the main rendering function for listing cards. |
| 181-189 | Shows the empty state when there are no listings. |
| 192 | Updates the result count. |
| 194-241 | Builds one card per listing, including sender/date, view tabs, details, ad snippet, original message, and copy buttons. |
| 243-246 | Attaches click handlers to every copy button. |
| 248-269 | Attaches card tab behavior and updates the floating copy button based on the active tab. |
| 272-284 | Defines `fetchListings()`, which builds the `/listings` URL, sends filters as query params, and renders the response. |
| 286-303 | Defines `loadCities()`, which fetches `/cities`, rebuilds the city dropdown, and preserves the selected city when possible. |
| 305-315 | Defines `getFilters()`, reading the current filter form values. |
| 317-325 | Defines a small debounce for price input filtering so the app does not request on every keystroke immediately. |
| 327-333 | Wires input/change events from the filter controls to listing fetches. |
| 335-340 | Wires the reset button to clear filters and fetch all listings. |
| 342-345 | Opens the hidden file picker when the import button is clicked. |
| 348-387 | Handles a selected chat file: resets progress, shows the overlay, starts polling, uploads the file, and handles errors. |
| 389-393 | Runs initial loading: city list first, then listings. |
| 395-414 | Contains a placeholder for a future natural-language inquiry parser. |

## `backend/test_ImprovedPromptCompact.py`

This file is the extraction pipeline.

| Section | What it does |
| --- | --- |
| Imports and constants | Imports parsing, database, timing, Pydantic, logging, and shared paths. `DB_PATH` now points to the backend database file. |
| `ListingExtraction` | Defines the exact schema Gemini should return for each listing. It includes property type, transaction type, price, down payment, currency, bedrooms, compound, city, district, ad snippet, and ad index. |
| `SYSTEM_PROMPT` | Gives Gemini detailed extraction rules and examples. This is the core prompt engineering layer. |
| `build_extraction_prompt()` | Formats a batch of WhatsApp messages as numbered `--- AD N ---` blocks. |
| `update_progress_file()` | Writes progress state into `backend/progress.json` so the frontend can show upload progress. |
| `call_gemini()` | Sends one batch to Gemini, asks for JSON matching `ListingExtraction`, tracks token usage/cost, retries failures, and returns parsed dictionaries. |
| `run_pipeline_improved()` | Orchestrates the whole backend job: load env, parse chat, select recent days, filter ads, batch ads, call Gemini per batch, insert rows, log analysis, and mark progress complete. |
| `_init_db()` | Creates the `listings` SQLite table if needed. |
| `_insert_listing()` | Inserts one extracted listing into SQLite. |
| `_get_recent_days()` | Keeps messages from the most recent N days in the chat file. |
| `_filter_ads()` | Uses `filter_chat.classify()` to keep only messages that look like real estate ads. |
| `_simple_batches()` | Provides a fallback batching strategy if the batching module cannot be imported. |
| `if __name__ == "__main__"` | Lets the pipeline be run directly on a sample file. |

## Refactor Done

- Added `backend/paths.py` to centralize shared file paths.
- Added `backend/__init__.py` so the backend can behave as a Python package.
- Updated API, database, pipeline, cost, analysis, and batching modules to use safer local imports where needed.
- Made progress, upload, database, and cost files resolve inside `backend/` instead of depending on the shell working directory.
- Made `/progress` handle missing or malformed JSON without a bare `except`.
- Added query validation for `limit` and `offset`.
- Ensured database connections close in `dbControl.py` even if a query fails.
- Added `standalone` to the extraction enum because the prompt examples already use it.
- Fixed frontend city dropdown duplication after importing a new chat.
- Fixed the visible `Compund` label typo to `Compound`.

## Suggested Next Refactors

1. Rename `test_ImprovedPromptCompact.py` to something production-facing like `extraction_pipeline.py`.
2. Split the giant pipeline file into `schema.py`, `prompt.py`, `gemini_client.py`, `pipeline.py`, and `repository.py`.
3. Move hard-coded values like API URL, model name, CORS origins, and selected day count into config.
4. Add backend tests for `/listings`, `/cities`, and progress handling.
5. Add a migration step for database schema changes instead of only `CREATE TABLE IF NOT EXISTS`.
6. Persist `down_payment` if the UI should display or filter it.

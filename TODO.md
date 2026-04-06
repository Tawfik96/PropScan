# PropScan Setup & Run TODO

## Completed
- [x] Plan confirmed and project analyzed (FastAPI backend + frontend)
- [x] Error diagnosed: pip install fails due to Anaconda metadata corruption (InvalidVersion '4.0.0-unsupported')

## Pending Steps
1. **FIX PIP INSTALL** (in backend/):
   ```
   rm -rf ~/opt/anaconda3/lib/python3.8/site-packages/pyodbc* ~/opt/anaconda3/lib/python3.8/site-packages/pyzmq*
   pip install --force-reinstall --no-cache-dir -r requirements.txt
   ```
2. Start backend server: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
3. In new terminal, serve frontend: `cd /Users/rawanabdelnasser/Desktop/AI_Real_ESTATE/PropScan && python -m http.server 3000`
4. Test upload: Upload `backend/mini_chat.txt` via `/upload` endpoint (curl or frontend)
5. Query listings: `curl http://localhost:8000/listings`
6. View app: Open `http://localhost:3000` in browser

## Notes
- Run commands in backend/ directory.
- GEMINI_API_KEY in `.env` is set.
- DB: `backend/listings.db` auto-created on upload.
- Frontend queries `/listings`, `/cities` from backend.
- If pip issues persist: Create venv `python -m venv venv`, `source venv/bin/activate`, then install.

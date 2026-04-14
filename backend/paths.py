from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "Taw_Generated_DB.db"
PROGRESS_FILE = BASE_DIR / "progress.json"
UPLOADED_CHAT_FILE = BASE_DIR / "uploaded_chat_file.txt"
COST_FILE = BASE_DIR / "costs.json"

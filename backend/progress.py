"""
progress.py
-----------
Real-time progress tracking for the extraction pipeline.
Writes pipeline state to progress.json, which the FastAPI server
exposes via the /progress endpoint.
"""

import json
from config import PROGRESS_FILE


def update_progress_file(current: int, total: int, status: str = "Processing", reset: bool = False) -> None:
    if reset:
        progress_data = {
            "current":    0,
            "total":      0,
            "percentage": 0,
            "status":     "",
            "done":       False,
        }
    else:
        done = total > 0 and current >= total
        progress_data = {
            "current":    current,
            "total":      total,
            "percentage": round((current / total) * 100) if total > 0 else 0,
            "status":     status,
            "done":       done,
        }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress_data, f)

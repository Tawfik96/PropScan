from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from typing import Optional
import os
import json

import db
import pipeline
from progress import update_progress_file
from config import PROGRESS_FILE, UPLOADED_CHAT_FILE

app = FastAPI(title="WhatsApp Real Estate Parser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()


@app.get("/progress")
def get_progress():
    try:
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    except Exception:
        return {"current": 0, "total": 0, "message": ""}


@app.post("/reset-progress")
def reset_progress():
    update_progress_file(0, 0, "Uploading…", reset=True)
    return {"ok": True}


@app.post("/upload")
async def upload_chat(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(os.path.dirname(__file__), UPLOADED_CHAT_FILE)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        await run_in_threadpool(pipeline.run_pipeline_improved, file_path, 2)
        return {"status": "ok", "message": "Chat processed successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})


@app.get("/listings")
def get_listings(
    price_min:        Optional[float] = Query(None),
    price_max:        Optional[float] = Query(None),
    bedrooms:         Optional[int]   = Query(None),
    city:             Optional[str]   = Query(None),
    transaction_type: Optional[str]   = Query(None),
    property_type:    Optional[str]   = Query(None),
    limit:            int             = Query(20000),
    offset:           int             = Query(0),
):
    if not db.has_listings_table():
        return {
            "listings": [],
            "count":    0,
            "message":  "There are no listings yet. Please upload a chat file first.",
        }

    listings = db.get_listings(
        price_min=price_min,
        price_max=price_max,
        bedrooms=bedrooms,
        city=city,
        transaction_type=transaction_type,
        property_type=property_type,
        limit=limit,
        offset=offset,
    )

    if not listings:
        return {
            "listings": [],
            "count":    0,
            "message":  "No listings found right now. Try uploading a chat file.",
        }

    return {"listings": listings, "count": len(listings)}


@app.get("/cities")
def get_cities():
    return {"cities": db.get_distinct_cities()}


@app.get("/health")
def health():
    return {"status": "ok"}

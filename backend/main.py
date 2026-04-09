from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import dbControl
import test_ImprovedPromptCompact
import os, json
from fastapi.concurrency import run_in_threadpool

PROGRESS_FILE = "progress.json"
UPLOADED_CHAT_FILE="uploaded_chat_file.txt"
app = FastAPI(title="WhatsApp Real Estate Parser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

dbControl.init_db()



@app.get("/progress")
def get_progress():
    try:
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    except:
        return {"current": 0, "total": 0, "message": ""}

@app.post("/reset-progress")
def reset_progress():
    test_ImprovedPromptCompact.update_progress_file(0, 0, "Uploading…", reset=True)
    return {"ok": True}

@app.post("/upload")
async def upload_chat(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(os.path.dirname(__file__), UPLOADED_CHAT_FILE)

        with open(file_path, "wb") as f:
            f.write(await file.read())
        # Run blocking code safely
        await run_in_threadpool(test_ImprovedPromptCompact.run_pipeline_improved, file_path, 2)
        return {"status": "ok", "message": "Chat processed successfully"}

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})

@app.get("/listings")
def get_listings(
    price_min: Optional[float] = Query(None),
    price_max: Optional[float] = Query(None),
    bedrooms: Optional[int] = Query(None),
    city: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    property_type: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0),
):
    if not dbControl.has_listings_table():
        return {
            "listings": [],
            "count": 0,
            "message": "There are no listings yet. Please upload a chat file first."
        }

    listings = dbControl.get_listings(
        price_min=price_min,
        price_max=price_max,
        bedrooms=bedrooms,
        city=city,
        transaction_type=transaction_type,
        property_type=property_type,
        limit=limit,
        offset=offset,
    )

    if len(listings) == 0:
        return {
            "listings": [],
            "count": 0,
            "message": "No listings found right now. Try uploading a chat file."
        }

    return {"listings": listings, "count": len(listings)}


@app.get("/cities")
def get_cities():
    return {"cities": dbControl.get_distinct_cities()}


@app.get("/health")
def health():
    return {"status": "ok"}

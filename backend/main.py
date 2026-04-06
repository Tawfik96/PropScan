from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import dbControl
import extractFromChatExport
import os
from fastapi.concurrency import run_in_threadpool

app = FastAPI(title="WhatsApp Real Estate Parser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pipeline status (in-memory, single-run) ──
pipeline_status = {
    "stage": "idle",
    "stage_index": 0,
    "total_stages": 5,
    "batch": 0,
    "total_batches": 0,
    "started_at": None,
    "done": False,
    "error": None,
}

def reset_status():
    pipeline_status.update({
        "stage": "idle", "stage_index": 0, "total_stages": 5,
        "batch": 0, "total_batches": 0,
        "started_at": None, "done": False, "error": None,
    })

dbControl.init_db()

@app.get("/status")
def get_status():
    return pipeline_status

@app.post("/upload")
async def upload_chat(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(os.path.dirname(__file__), file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        reset_status()
        pipeline_status["started_at"] = __import__("time").time()

        await run_in_threadpool(
            extractFromChatExport.run_pipeline,
            file_path, 1, pipeline_status
        )
        return {"status": "ok", "message": "Chat processed successfully"}

    except Exception as e:
        pipeline_status["error"] = str(e)
        pipeline_status["stage"] = "error"
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
        return {"listings": [], "count": 0, "message": "No listings yet."}
    listings = dbControl.get_listings(
        price_min=price_min, price_max=price_max, bedrooms=bedrooms,
        city=city, transaction_type=transaction_type,
        property_type=property_type, limit=limit, offset=offset,
    )
    if len(listings) == 0:
        return {"listings": [], "count": 0, "message": "No listings found."}
    return {"listings": listings, "count": len(listings)}

@app.get("/cities")
def get_cities():
    return {"cities": dbControl.get_distinct_cities()}

@app.get("/health")
def health():
    return {"status": "ok"}
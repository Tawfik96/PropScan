from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import dbControl
import extractFromChatExport
import pipeline
import os

app = FastAPI(title="WhatsApp Real Estate Parser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

dbControl.init_db()
@app.post("/upload")
async def upload_chat(file: UploadFile = File(...)):
    try:
      #store the file in the directory and return the path
      file_path = os.path.join(os.path.dirname(__file__), file.filename)
      with open(file_path, "wb") as f:
        f.write(await file.read())
        # pipeline.process_chat(file_path)
        extractFromChatExport.run_pipeline(file_path,1)
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

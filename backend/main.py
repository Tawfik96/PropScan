from fastapi import FastAPI, UploadFile, File, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import os
from fastapi.concurrency import run_in_threadpool

# Support both `python backend/main.py` (bare) and `import backend.main` (package)
try:
    from backend import dbControl
    from backend import extractFromChatExport
except ImportError:
    import dbControl  # type: ignore
    import extractFromChatExport  # type: ignore
from run_tests_programmatically import run_tests  
  


app = FastAPI(title="WhatsApp Real Estate Parser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# dbControl.init_db()  # Moved to endpoints to avoid test conflicts
@app.post("/upload")
async def upload_chat(file: UploadFile = File(...)):
    # Validate file extension — only .txt WhatsApp exports are accepted
    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .txt WhatsApp chat exports are accepted.",
        )

    try:
        file_path = os.path.join(os.path.dirname(__file__), file.filename)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Run blocking code safely
        await run_in_threadpool(extractFromChatExport.run_pipeline, file_path, 1)
        return {"status": "ok", "message": "Chat processed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
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

    return {"listings": listings, "count": len(listings), "message": "" if listings else "No listings found matching your filters."}


@app.get("/cities")
def get_cities():
    return {"cities": dbControl.get_distinct_cities()}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/process-chat")
async def process_chat(file: UploadFile, debug: bool = False):

    file_path = os.path.join(os.path.dirname(__file__), file.filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    results = await run_in_threadpool(
        extractFromChatExport.run_pipeline,
        file_path,
        1
    )

    test_status = None
    if debug:
        test_status = run_tests()

    return {
        "results": results,
        "tests_passed": test_status
    }
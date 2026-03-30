"""
pipeline.py
-----------
STUB — Replace the body of `process_chat` with your real pipeline logic.

The function receives the raw text content of the WhatsApp export file.
It should parse the messages, run extraction, and INSERT results into the DB
via models.insert_listing(). The FastAPI layer never writes listings itself;
it only reads them back after this function returns.
"""
from extractFromChatExport import run_pipeline

def process_chat(file_content: str):
    """
    STUB: Replace with real pipeline later.
    """
    run_pipeline(file_content,1)
    

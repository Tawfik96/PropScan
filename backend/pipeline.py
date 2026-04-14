"""
pipeline.py
-----------
Main extraction pipeline orchestrator.

Entry point:
    run_pipeline_improved(chat_file, days=2)

Steps:
  1. Parse WhatsApp export
  2. Select the N most recent days
  3. Filter messages to real estate ads
  4. Build optimal batches for the API
  5. Extract listings via Gemini
  6. Store results in SQLite
  7. Print token / cost summary
"""

import os
import time
from datetime import datetime

import db
import extractor
import progress as prog
from analysis import open_analysis_log
from filter_chat import parse_whatsapp_export, classify
from batch_messages import build_batches, compute_ads_avg


# ── Public entry point ────────────────────────────────────────────────────────

def run_pipeline_improved(chat_file: str, days: int = 2) -> None:
    """
    Enhanced pipeline with per-batch cost tracking and cache monitoring.
    """
    from google import genai
    from dotenv import load_dotenv

    load_dotenv()
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    run_start = time.perf_counter()
    run_ts    = datetime.now().isoformat(timespec="seconds")

    print(f"{'='*70}")
    print(f"  Real Estate Ad Extraction Pipeline (IMPROVED)")
    print(f"  {run_ts}  |  {extractor.GEMINI_MODEL}  |  Days: {days}")
    print(f"{'='*70}\n")

    # ── Step 1: Parse ──────────────────────────────────────────────────────────
    messages = parse_whatsapp_export(chat_file)
    print(f"[1/5] Parsed {len(messages)} messages")

    if not messages:
        print("      No messages found.")
        return

    dates = sorted(set(m["datetime"].date() for m in messages))
    print(f"      Date range: {dates[0]} → {dates[-1]}")

    # ── Step 2: Select target days ─────────────────────────────────────────────
    day_messages  = _get_recent_days(messages, days)
    target_dates  = sorted(set(m["datetime"].date() for m in day_messages))
    print(f"\n[2/5] Target: {target_dates[0]} → {target_dates[-1]}  ({len(day_messages)} msgs)")

    # ── Step 3: Filter ads ─────────────────────────────────────────────────────
    ads, fstats = _filter_ads(day_messages)
    print(f"\n[3/5] Filter: {fstats['passed']} ads from {len(day_messages)} messages")
    print(
        f"      Dropped: system={fstats['system']}  short={fstats['too_short']}  "
        f"blocklist={fstats['blocklist']}  no_kw={fstats['no_keywords']}"
    )

    if not ads:
        print("      No ads found.")
        return

    # ── Build batches ──────────────────────────────────────────────────────────
    try:
        ads_avg = compute_ads_avg(ads)
        batches = build_batches(ads, ads_avg)
    except ImportError:
        BATCH_SIZE = 10
        batches = _simple_batches(ads, BATCH_SIZE)

    prog.update_progress_file(0, len(batches), "Starting batches...")
    logger = open_analysis_log(run_ts, extractor.GEMINI_MODEL, len(batches), days, chat_file)
    print(f"      Batches: {len(batches)}")

    # ── Count system prompt tokens ─────────────────────────────────────────────
    try:
        count_resp = client.models.count_tokens(
            model=extractor.GEMINI_MODEL,
            contents=extractor.SYSTEM_PROMPT,
        )
        sys_tokens = count_resp.total_tokens
        above = sys_tokens >= 1024
        print(
            f"\n  📏 System prompt: {sys_tokens:,} tokens "
            f"({'✅ above' if above else '⚠️  below'} 1024 implicit cache threshold)"
        )
    except Exception:
        print(f"\n  📏 System prompt: (could not count tokens)")

    # ── Step 4: Extract ────────────────────────────────────────────────────────
    print(f"\n[4/5] Extracting via {extractor.GEMINI_MODEL}...")
    print(
        f"      {'Batch':>5}  {'Msgs':>4}  {'Extracted':>9}  "
        f"{'Input':>7}  {'Cached':>7}  {'Output':>7}  {'Think':>7}  "
        f"{'Cost':>10}  {'API Time':>8}"
    )
    print(
        f"      {'─'*5}  {'─'*4}  {'─'*9}  "
        f"{'─'*7}  {'─'*7}  {'─'*7}  {'─'*7}  "
        f"{'─'*10}  {'─'*8}"
    )

    conn = db.init_schema()
    total_inserted = 0
    all_info       = []

    for batch_num, batch_obj in enumerate(batches, 1):
        prog.update_progress_file(batch_num, len(batches), f"Processing batch {batch_num}...")

        batch = batch_obj.messages if hasattr(batch_obj, "messages") else batch_obj

        t_batch = time.perf_counter()
        results, info, api_response = extractor.call_gemini(batch, client)
        batch_total = time.perf_counter() - t_batch

        all_info.append(info)

        for result in results:
            idx = result.get("ad_index", 1) - 1
            ad  = batch[idx] if 0 <= idx < len(batch) else None
            db.insert_listing(
                conn,
                result,
                original_msg=ad["body"] if ad else "",
                sender=ad.get("sender") if ad else None,
                date=ad["datetime"].isoformat() if ad and ad.get("datetime") else None,
            )
            total_inserted += 1
        conn.commit()

        api_ms     = f"{info['api_call_s']*1000:.0f}ms" if info["api_call_s"] else "err"
        cache_flag = " 💾" if info["cached_tokens"] > 0 else ""
        print(
            f"      {batch_num:>5}  {len(batch):>4}  {len(results):>9}  "
            f"{info['input_tokens']:>7,}  {info['cached_tokens']:>7,}  "
            f"{info['output_tokens']:>7,}  {info['thinking_tokens']:>7,}  "
            f"${info['cost_total']:>9.6f}  {api_ms}{cache_flag}"
        )

        if batch_num < len(batches):
            time.sleep(1)

        logger.log_batch(
            batch_num=batch_num,
            total_batches=len(batches),
            batch=batch,
            results=results,
            batch_total_s=batch_total,
            api_response=api_response,
            api_s=info["api_call_s"] or 0.0,
            estimated_ads=batch_obj.estimated_ads,
        )

    conn.close()
    prog.update_progress_file(len(batches), len(batches), "Complete")

    # ── Step 5: Summary ────────────────────────────────────────────────────────
    total_time     = time.perf_counter() - run_start
    total_input    = sum(i["input_tokens"]    for i in all_info)
    total_cached   = sum(i["cached_tokens"]   for i in all_info)
    total_output   = sum(i["output_tokens"]   for i in all_info)
    total_thinking = sum(i["thinking_tokens"] for i in all_info)
    total_cost     = sum(i["cost_total"]      for i in all_info)

    cache_pct = (total_cached / total_input * 100) if total_input > 0 else 0

    print(f"\n[5/5] {'='*60}")
    print(f"  Listings saved    : {total_inserted}")
    print(f"  Total time        : {total_time:.1f}s")
    print(f"  Database          : {os.path.abspath(db.DB_PATH)}")

    print(f"\n  ── Token Summary {'─'*42}")
    print(f"  Total input       : {total_input:>10,}")
    print(f"    of which cached : {total_cached:>10,}  ({cache_pct:.1f}%)")
    print(f"  Total output      : {total_output:>10,}")
    print(f"  Total thinking    : {total_thinking:>10,}")

    print(f"\n  ── Cost Summary {'─'*43}")
    cost_fresh    = sum(i["cost_input"]    for i in all_info)
    cost_cached   = sum(i["cost_cached"]   for i in all_info)
    cost_output   = sum(i["cost_output"]   for i in all_info)
    cost_thinking = sum(i["cost_thinking"] for i in all_info)
    print(f"  Fresh input       : ${cost_fresh:.8f}  (${extractor.PRICE_INPUT}/1M)")
    print(f"  Cached input      : ${cost_cached:.8f}  (${extractor.PRICE_CACHED_READ}/1M)")
    print(f"  Output            : ${cost_output:.8f}  (${extractor.PRICE_OUTPUT}/1M)")
    print(f"  Thinking          : ${cost_thinking:.8f}  (${extractor.PRICE_OUTPUT}/1M)")
    print(f"  TOTAL             : ${total_cost:.8f}")

    if total_cached > 0:
        savings = (total_cached / 1e6) * (extractor.PRICE_INPUT - extractor.PRICE_CACHED_READ)
        print(f"\n  💾 Implicit cache saved: ${savings:.8f}")
    else:
        print(f"\n  ℹ️  No implicit cache hits this run.")
        print(f"     This is normal for a single run or first run.")
        print(f"     Implicit caching activates when consecutive requests")
        print(f"     share the same prefix within a short time window.")

    # ── Property type breakdown ────────────────────────────────────────────────
    import sqlite3
    conn2 = sqlite3.connect(db.DB_PATH)
    cursor = conn2.execute(
        """
        SELECT property_type, COUNT(*) FROM listings
        WHERE property_type IS NOT NULL
        GROUP BY property_type ORDER BY 2 DESC
        """
    )
    prop_types = {r[0]: r[1] for r in cursor}
    conn2.close()

    if prop_types:
        print(f"\n  ── Property Types {'─'*41}")
        for k, v in prop_types.items():
            print(f"    {k}: {v}")

    print(f"\n{'='*70}")
    logger.finalize(total_inserted=total_inserted, fstats=fstats)


# ── Private helpers ───────────────────────────────────────────────────────────

def _get_recent_days(messages: list[dict], days: int) -> list[dict]:
    if not messages:
        return []
    dates  = sorted(set(m["datetime"].date() for m in messages))
    target = set(dates[-days:])
    return [m for m in messages if m["datetime"].date() in target]


def _filter_ads(messages: list[dict]) -> tuple[list[dict], dict]:
    stats = {"system": 0, "too_short": 0, "blocklist": 0, "no_keywords": 0, "passed": 0}
    ads   = []
    for msg in messages:
        result = classify(msg)
        if result == "pass":
            stats["passed"] += 1
            ads.append(msg)
        else:
            stats[result] += 1
    return ads, stats


class _SimpleBatch:
    """Minimal batch wrapper used as a fallback when batch_messages is unavailable."""
    def __init__(self, msgs: list[dict]):
        self.messages      = msgs
        self.estimated_ads = len(msgs)


def _simple_batches(ads: list[dict], size: int) -> list[_SimpleBatch]:
    return [_SimpleBatch(ads[i: i + size]) for i in range(0, len(ads), size)]


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_pipeline_improved(
        "SampleTextFiles/New50DayGTSample.txt",
        8,
    )

"""
compare_to_ground_truth.py
==========================
Compares an LLM-generated listings DB against ground_truth.db.

Matching strategy:
  - Rows are matched by (reference_id) when available, then by
    (compound_name + bedrooms + area_sqm + transaction_type) as fallback.
  - Each field is scored independently.
  - Numeric fields use a tolerance band (default ±5%).
  - A final overall score is printed per row and in aggregate.

Usage:
    python ground_truth/compare_to_ground_truth.py path/to/llm_output.db

Output:
    - Per-row match table
    - Per-field accuracy summary
    - Overall score  (0–100)
    - CSV report saved to:  ground_truth/comparison_report.csv
"""

import sqlite3
import sys
import os
import json
import csv
from datetime import datetime
import tempfile

temp_db = tempfile.NamedTemporaryFile(delete=False)
os.environ["DB_PATH"] = temp_db.name

GT_DB      = os.path.join(os.path.dirname(__file__), "ground_truth.db")
REPORT_CSV = os.path.join(os.path.dirname(__file__), "comparison_report.csv")
TOLERANCE  = 0.05   # 5% numeric tolerance


# ── Fields to compare and their types ────────────────────────────────────────

FIELDS = {
    # field_name            : ("exact" | "numeric" | "bool" | "json_list" | "text_loose")
    "property_type":          "exact",
    "transaction_type":       "exact",
    "price":                  "numeric",
    "currency":               "exact",
    "area_sqm":               "numeric",
    "bedrooms":               "exact",
    "bathrooms":              "exact",
    "floor_number":           "exact",
    "furnished":              "exact",
    "finishing":              "exact",
    "has_garden":             "bool",
    "garden_area_sqm":        "numeric",
    "has_pool":               "bool",
    "has_balcony":            "bool",
    "city":                   "text_loose",
    "district":               "text_loose",
    "compound_name":          "text_loose",
    "down_payment":           "numeric",
    "installment_amount":     "numeric",
    "reference_id":           "exact",
    "phone_numbers":          "json_list",
}

CRITICAL_FIELDS = {"property_type", "transaction_type", "price", "currency",
                   "bedrooms", "area_sqm", "compound_name"}

# ── Comparators ───────────────────────────────────────────────────────────────

def cmp_exact(a, b):
    if a is None and b is None: return "skip"
    if a is None or b is None:  return "miss"
    return "ok" if str(a).strip().lower() == str(b).strip().lower() else "fail"

def cmp_numeric(a, b, tol=TOLERANCE):
    if a is None and b is None: return "skip"
    if a is None or b is None:  return "miss"
    try:
        fa, fb = float(a), float(b)
        if fa == 0 and fb == 0: return "ok"
        diff = abs(fa - fb) / max(abs(fa), abs(fb), 1)
        return "ok" if diff <= tol else "fail"
    except (TypeError, ValueError):
        return "fail"

def cmp_bool(a, b):
    if a is None and b is None: return "skip"
    if a is None or b is None:  return "miss"
    return "ok" if bool(a) == bool(b) else "fail"

def cmp_json_list(a, b):
    if a is None and b is None: return "skip"
    if a is None or b is None:  return "miss"
    try:
        la = set(json.loads(a) if isinstance(a, str) else a)
        lb = set(json.loads(b) if isinstance(b, str) else b)
        # normalise phone numbers: strip spaces, dashes, leading +20/0
        def norm(p): return re.sub(r"[\s\-\+]", "", str(p)).lstrip("20").lstrip("0")
        import re
        la = set(norm(x) for x in la)
        lb = set(norm(x) for x in lb)
        return "ok" if la == lb else "fail"
    except Exception:
        return "fail"

def cmp_text_loose(a, b):
    """Case-insensitive substring match — GT value must appear in LLM value."""
    if a is None and b is None: return "skip"
    if a is None or b is None:  return "miss"
    a_clean = str(a).strip().lower()
    b_clean = str(b).strip().lower()
    return "ok" if (a_clean in b_clean or b_clean in a_clean) else "fail"

COMPARATORS = {
    "exact":      cmp_exact,
    "numeric":    cmp_numeric,
    "bool":       cmp_bool,
    "json_list":  cmp_json_list,
    "text_loose": cmp_text_loose,
}

# ── DB helpers ────────────────────────────────────────────────────────────────

def load_rows(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM listings").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── Matching ──────────────────────────────────────────────────────────────────

def match_rows(gt_rows, llm_rows):
    """
    Returns list of (gt_row, llm_row | None) pairs.
    Primary key: reference_id (when not null).
    Fallback: (compound_name, bedrooms, area_sqm, transaction_type).
    """
    llm_by_ref = {}
    llm_by_key = {}
    for r in llm_rows:
        ref = (r.get("reference_id") or "").strip().lower()
        if ref:
            llm_by_ref[ref] = r
        key = (
            (r.get("compound_name") or "").lower(),
            r.get("bedrooms"),
            r.get("area_sqm"),
            (r.get("transaction_type") or "").lower(),
        )
        llm_by_key[key] = r

    pairs = []
    for gt in gt_rows:
        ref = (gt.get("reference_id") or "").strip().lower()
        llm = llm_by_ref.get(ref)
        if not llm:
            key = (
                (gt.get("compound_name") or "").lower(),
                gt.get("bedrooms"),
                gt.get("area_sqm"),
                (gt.get("transaction_type") or "").lower(),
            )
            llm = llm_by_key.get(key)
        pairs.append((gt, llm))
    return pairs

# ── Scoring ───────────────────────────────────────────────────────────────────

def score_pair(gt, llm):
    """Returns {field: result} where result ∈ {ok, fail, miss, skip}."""
    if llm is None:
        return {f: "miss" for f in FIELDS}
    results = {}
    for field, ftype in FIELDS.items():
        gt_val  = gt.get(field)
        llm_val = llm.get(field)
        results[field] = COMPARATORS[ftype](gt_val, llm_val)
    return results

# ── Report ────────────────────────────────────────────────────────────────────

def run_comparison(llm_db_path):
    print(f"\n{'='*65}")
    print(f"  PropScan — Ground Truth Comparison")
    print(f"  GT DB  : {GT_DB}")
    print(f"  LLM DB : {llm_db_path}")
    print(f"  Run at : {datetime.now().isoformat(timespec='seconds')}")
    print(f"{'='*65}\n")

    gt_rows  = load_rows(GT_DB)
    llm_rows = load_rows(llm_db_path)
    print(f"  GT rows  : {len(gt_rows)}")
    print(f"  LLM rows : {len(llm_rows)}")

    pairs = match_rows(gt_rows, llm_rows)
    matched = sum(1 for _, llm in pairs if llm is not None)
    print(f"  Matched  : {matched}/{len(gt_rows)} GT rows found in LLM output\n")

    # Per-row detail
    all_results = []
    csv_rows    = []

    for i, (gt, llm) in enumerate(pairs, 1):
        ref   = gt.get("reference_id") or f"row_{i}"
        label = f"{ref} | {gt.get('compound_name','?')} | {gt.get('transaction_type','?')} | {gt.get('bedrooms','?')}BR"

        if llm is None:
            print(f"  [{i:02d}] ✗ NOT FOUND  {label}")
            all_results.append({f: "miss" for f in FIELDS})
            csv_rows.append({"ref": ref, "matched": False, **{f: "miss" for f in FIELDS}})
            continue

        res = score_pair(gt, llm)
        all_results.append(res)

        ok_count   = sum(1 for v in res.values() if v == "ok")
        fail_count = sum(1 for v in res.values() if v == "fail")
        skip_count = sum(1 for v in res.values() if v == "skip")
        scored     = ok_count + fail_count
        row_score  = round(ok_count / scored * 100, 1) if scored else 0

        critical_fails = [f for f in CRITICAL_FIELDS if res.get(f) == "fail"]
        status = "✓" if not critical_fails else "⚠"
        print(f"  [{i:02d}] {status} {row_score:5.1f}%  {label}")
        if fail_count:
            fails = [f"{f}={res[f]}" for f, v in res.items() if v in ("fail", "miss")]
            print(f"         fails: {', '.join(fails)}")
        if critical_fails:
            print(f"         CRITICAL fails: {', '.join(critical_fails)}")

        csv_rows.append({"ref": ref, "matched": True, "row_score": row_score, **res})

    # Per-field summary
    print(f"\n  {'─'*55}")
    print(f"  Per-field accuracy  (ok / scored, skips excluded)\n")
    field_scores = {}
    for field in FIELDS:
        ok   = sum(1 for r in all_results if r.get(field) == "ok")
        fail = sum(1 for r in all_results if r.get(field) == "fail")
        miss = sum(1 for r in all_results if r.get(field) == "miss")
        scored = ok + fail + miss
        pct = round(ok / scored * 100, 1) if scored else 0
        field_scores[field] = pct
        bar = "█" * int(pct / 5)
        marker = " ◄ CRITICAL" if field in CRITICAL_FIELDS else ""
        print(f"    {field:<22} {pct:5.1f}%  {bar}{marker}")

    # Overall score — critical fields weighted 2×
    weighted_sum   = sum(
        field_scores[f] * (2 if f in CRITICAL_FIELDS else 1)
        for f in FIELDS
    )
    weight_total   = sum(2 if f in CRITICAL_FIELDS else 1 for f in FIELDS)
    overall        = round(weighted_sum / weight_total, 1)
    match_rate     = round(matched / len(gt_rows) * 100, 1)

    print(f"\n  {'─'*55}")
    print(f"  Row match rate  : {match_rate}%  ({matched}/{len(gt_rows)})")
    print(f"  Overall score   : {overall}/100  (critical fields weighted 2×)")
    print(f"  {'─'*55}")

    grade = (
        "EXCELLENT ✓✓" if overall >= 90 else
        "GOOD ✓"       if overall >= 75 else
        "FAIR ⚠"       if overall >= 55 else
        "POOR ✗"
    )
    print(f"  Grade           : {grade}")
    print(f"{'='*65}\n")

    # CSV report
    if csv_rows:
        fieldnames = ["ref", "matched", "row_score"] + list(FIELDS.keys())
        with open(REPORT_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            w.writerows(csv_rows)
        print(f"  Report saved → {REPORT_CSV}\n")

    return overall


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compare_to_ground_truth.py <llm_output.db>")
        sys.exit(1)
    run_comparison(sys.argv[1])

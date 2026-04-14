"""
batch_messages.py
-----------------
Takes the output of filter_chat.py (parsed + classified messages) and
groups them into batches suitable for LLM calls.

Batching rules:
  - Fill up to MAX_CHARS_PER_BATCH chars OR MAX_ADS_PER_BATCH ads,
    whichever comes first.
  - A single message that exceeds MAX_CHARS_PER_BATCH on its own gets
    its own dedicated batch (logged as oversized).
  - Token count is estimated cheaply from char length (no external lib).

Usage (standalone):
    python batch_messages.py

Importable by pipeline:
    from batch_messages import build_batches, estimate_tokens
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from filter_chat import (
    parse_whatsapp_export,
    classify,
    get_size_and_count,
)

# ─── Config ───────────────────────────────────────────────────────────────────

MAX_CHARS_PER_BATCH: int = 8_000
MAX_ADS_PER_BATCH:   int = 10

# Mixed Arabic / Franco / English heuristic: ~3 chars per token
CHARS_PER_TOKEN: float = 3.0


# ─── Data structures ──────────────────────────────────────────────────────────

@dataclass
class Batch:
    messages:       List[dict]        = field(default_factory=list)
    total_chars:    int               = 0
    estimated_ads:  int               = 0
    is_oversized:   bool              = False          # single msg > MAX_CHARS

    @property
    def estimated_tokens(self) -> int:
        return int(self.total_chars / CHARS_PER_TOKEN)

    def summary(self, index: int) -> str:
        flag = "  ⚠ OVERSIZED" if self.is_oversized else ""
        return (
            f"Batch {index+1:>3}: "
            f"{len(self.messages):>2} msg(s) | "
            f"~{self.estimated_ads:>2} ads | "
            f"{self.total_chars:>6} chars | "
            f"~{self.estimated_tokens:>4} tokens"
            f"{flag}"
        )


# ─── Core logic ───────────────────────────────────────────────────────────────
def build_batches(
    messages,
    ads_avg,
    max_chars=MAX_CHARS_PER_BATCH,
    max_ads=MAX_ADS_PER_BATCH
):
    
    #Taw: temp list to sort oversized messages
    enriched = []

    for msg in messages:
        body = msg["body"].strip()
        char_len = len(body)
        _, ad_cnt = get_size_and_count(body, ads_avg)

        enriched.append({
            "msg": msg,
            "chars": char_len,
            "ads": ad_cnt
        })

    enriched.sort(key=lambda x: x["chars"], reverse=True)

    batches: List[Batch] = []

    for item in enriched:
        placed = False

        if item["chars"] > max_chars:
            batches.append(Batch(
                messages=[item["msg"]],
                total_chars=item["chars"],
                estimated_ads=item["ads"],
                is_oversized=True
            ))
            continue

        for batch in batches:
            if batch.is_oversized:
                continue

            if (batch.total_chars + item["chars"] <= max_chars and
                batch.estimated_ads + item["ads"] <= max_ads):

                batch.messages.append(item["msg"])
                batch.total_chars += item["chars"]
                batch.estimated_ads += item["ads"]
                placed = True
                break

        if not placed:
            new_batch = Batch()
            new_batch.messages.append(item["msg"])
            new_batch.total_chars = item["chars"]
            new_batch.estimated_ads = item["ads"]
            batches.append(new_batch)

    return batches
def estimate_tokens(chars: int) -> int:
    """Cheap token estimate — no external library required."""
    return int(chars / CHARS_PER_TOKEN)


def compute_ads_avg(pass_messages: List[dict]) -> float:
    """Average body length in chars across pass messages. Used by build_batches."""
    lengths = [len(m["body"].strip()) for m in pass_messages]
    return sum(lengths) / len(lengths) if lengths else 0


# ─── Main ─────────────────────────────────────────────────────────────────────

def main(filepath: str):
    messages = parse_whatsapp_export(filepath)
    if not messages:
        print("No messages found.")
        return

    # Classify and collect pass messages + compute ads_avg (mirrors filter_chat)
    results    = [(msg, classify(msg)) for msg in messages]
    pass_msgs  = [msg for msg, reason in results if reason == "pass"]
    ads_lengths = [len(msg["body"].strip()) for msg in pass_msgs]

    ads_avg = sum(ads_lengths) / len(ads_lengths) if ads_lengths else 0

    batches = build_batches(pass_msgs, ads_avg)

    # ── Print summary ─────────────────────────────────────────────────────────
    total_chars  = sum(b.total_chars   for b in batches)
    total_ads    = sum(b.estimated_ads for b in batches)
    total_tokens = estimate_tokens(total_chars)
    oversized    = sum(1 for b in batches if b.is_oversized)

    print(f"Pass messages : {len(pass_msgs)}")
    print(f"Batches       : {len(batches)}  ({oversized} oversized)\n")

    for i, batch in enumerate(batches):
        print(batch.summary(i))

    print(f"\nTotal chars   : {total_chars:,}")
    print(f"Est. tokens   : ~{total_tokens:,}")
    print(f"Est. ads      : ~{total_ads}")


if __name__ == "__main__":
    file_path = "backend/v2New50DayGTSample.txt"
    main(file_path)
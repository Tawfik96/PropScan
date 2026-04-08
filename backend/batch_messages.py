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

MAX_CHARS_PER_BATCH: int = 12_000
MAX_ADS_PER_BATCH:   int = 22

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
    messages:          List[dict],
    ads_avg:           float,
    max_chars:         int = MAX_CHARS_PER_BATCH,
    max_ads:           int = MAX_ADS_PER_BATCH,
) -> List[Batch]:
    """
    Pack classified-pass messages into batches.

    Parameters
    ----------
    messages  : list of message dicts (already filtered to 'pass' only)
    ads_avg   : average ad length in chars (from filter_chat stats),
                used by get_size_and_count to estimate ads per message
    max_chars : hard char ceiling per batch
    max_ads   : hard ad-count ceiling per batch

    Returns
    -------
    List of Batch objects, each ready to send to the LLM.
    """
    batches: List[Batch] = []
    current = Batch()

    for msg in messages:
        body      = msg["body"].strip()
        char_len  = len(body)
        _, ad_cnt = get_size_and_count(body, ads_avg)

        # ── Oversized: single message already exceeds the char limit ──────────
        if char_len > max_chars:
            # Flush whatever is in progress first
            if current.messages:
                batches.append(current)
                current = Batch()

            oversized_batch = Batch(
                messages      = [msg],
                total_chars   = char_len,
                estimated_ads = ad_cnt,
                is_oversized  = True,
            )
            batches.append(oversized_batch)
            continue

        # ── Would adding this message exceed either limit? ────────────────────
        would_exceed_chars = (current.total_chars + char_len) > max_chars
        would_exceed_ads   = (current.estimated_ads + ad_cnt) > max_ads

        if current.messages and (would_exceed_chars or would_exceed_ads):
            batches.append(current)
            current = Batch()

        # ── Add to current batch ──────────────────────────────────────────────
        current.messages.append(msg)
        current.total_chars   += char_len
        current.estimated_ads += ad_cnt

    # Flush last batch
    if current.messages:
        batches.append(current)

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
    main("messages_per_day/75_messages_01_03_2025.txt")
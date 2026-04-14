"""
analysis.py
===========
Analysis + cost logging for the Real Estate Ad Extraction Pipeline.
Called from pipeline.py — never run standalone.

Exports:
    open_analysis_log(run_ts, model, total_batches, days, chat_file) -> RunLogger
    RunLogger.log_batch(batch_num, total_batches, batch, results, batch_total_s,
                        api_response=None)
    RunLogger.finalize(total_inserted, fstats, timings)

Output:
    analysis.md  (same directory as this file, appended on every run)


Extra Feature:
    The pipeline now records the costs of each batch and raise an error in case the limit is exceeded!
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

try:
    from . import cost_manager
except ImportError:
    import cost_manager
# ── Constants ─────────────────────────────────────────────────────────────────

ANALYSIS_PATH           = os.path.join(os.path.dirname(__file__), "Big_Analysis.md")
TRUNCATE_CHARS          = 10000

# Gemini Flash Lite pricing (USD per token)
COST_INPUT_PER_TOKEN    = 0.10  / 1_000_000   # $0.10  / 1M
COST_OUTPUT_PER_TOKEN   = 0.40  / 1_000_000   # $0.40  / 1M
COST_THINKING_PER_TOKEN = 0.40  / 1_000_000   # $0.40  / 1M (same as output)
COST_CACHE_PER_TOKEN    = 0.025 / 1_000_000   # $0.025 / 1M (cache read)


# ── Helpers ───────────────────────────────────────────────────────────────────

def format_date_time(dt_str: str):
    dt = datetime.fromisoformat(dt_str)
    date_str = f"{dt.day}/{dt.month}/{dt.year}"
    time_str = f"{dt.hour}:{dt.minute:02d}"
    return date_str, time_str

def _trunc(text: str, limit: int = TRUNCATE_CHARS) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n[truncated — {len(text):,} chars total]"


def _word_count(text: str) -> int:
    return len(text.split())


def _cost(tokens: int, rate: float) -> str:
    return f"${tokens * rate:.5f}"


def _md_table(headers: list[str], row: list) -> str:
    """Single-row markdown table."""
    sep = " | ".join("---" for _ in headers)
    return (
        f"| {' | '.join(headers)} |\n"
        f"| {sep} |\n"
        f"| {' | '.join(str(v) for v in row)} |"
    )


def _multi_row_table(headers: list[str], rows: list[list]) -> str:
    """Multi-row markdown table."""
    sep = " | ".join("---" for _ in headers)
    body = "\n".join(f"| {' | '.join(str(v) for v in row)} |" for row in rows)
    return f"| {' | '.join(headers)} |\n| {sep} |\n{body}"


def _section(title: str) -> str:
    return f"\n**{title}**\n"


def _divider() -> str:
    return "\n---\n"


def _collapsible(summary: str, content: str) -> str:
    """HTML <details> block — renders as collapsible in GitHub MD / most viewers."""
    return (
        f"<details>\n"
        f"<summary>{summary}</summary>\n\n"
        f"```\n{content}\n```\n\n"
        f"</details>\n"
    )


def _safe_div(a, b):
    return a / b if b else 0


# ── Token extraction from api_response ───────────────────────────────────────

def _extract_usage(api_response) -> dict:
    """
    Pull token counts from a Gemini response object's usage_metadata.

    Expected fields on usage_metadata:
        prompt_token_count           → input tokens
        candidates_token_count       → output tokens
        thoughts_token_count         → thinking tokens
        cached_content_token_count   → cache read tokens
        total_token_count
    """
    empty = {
        "input_tokens":    0,
        "output_tokens":   0,
        "thinking_tokens": 0,
        "cache_tokens":    0,
        "total_tokens":    0,
    }
    if api_response is None:
        return empty

    meta = getattr(api_response, "usage_metadata", None)
    if meta is None:
        return empty

    return {
        "input_tokens":    getattr(meta, "prompt_token_count",          0) or 0,
        "output_tokens":   getattr(meta, "candidates_token_count",      0) or 0,
        "thinking_tokens": getattr(meta, "thoughts_token_count",        0) or 0,
        "cache_tokens":    getattr(meta, "cached_content_token_count",  0) or 0,
        "total_tokens":    getattr(meta, "total_token_count",           0) or 0,
    }


def _extract_thinking_text(api_response) -> str:
    if api_response is None:
        return ""
    try:
        for part in api_response.candidates[0].content.parts:
            if getattr(part, "thought", False):
                return part.text or ""
    except Exception:
        pass
    return ""


def _extract_output_text(api_response) -> str:
    if api_response is None:
        return ""
    try:
        parts = []
        for part in api_response.candidates[0].content.parts:
            if not getattr(part, "thought", False):
                text = getattr(part, "text", None)
                if text:
                    parts.append(text)
        return "\n".join(parts)
    except Exception:
        return getattr(api_response, "text", "") or ""





# ── RunLogger ─────────────────────────────────────────────────────────────────

class RunLogger:
    """
    Accumulates per-batch analysis blocks and writes them to analysis.md.
    One instance per pipeline run.
    """

    def __init__(
        self,
        run_ts:        str,
        model:         str,
        total_batches: int,
        days:          int,
        chat_file:     str,
    ):
        self.run_ts        = run_ts
        self.model         = model
        self.total_batches = total_batches
        self.days          = days
        self.chat_file     = chat_file

        # ── Accumulators for run summary ──────────────────────────────────────
        self._total_input_tokens    = 0
        self._total_output_tokens   = 0
        self._total_thinking_tokens = 0
        self._total_cache_tokens    = 0
        self._total_cost            = 0.0

        self._daily_cost_state = cost_manager.load_cost_state()

        self._total_msgs_in         = 0
        self._total_ads_extracted   = 0
        self._total_est_ads         = 0

        self._total_input_words     = 0
        self._total_output_words    = 0
        self._total_input_chars     = 0
        self._total_output_chars    = 0

        self._batch_latencies: list[float] = []   # total wall time per batch (s)
        self._api_latencies:   list[float] = []   # api-only time per batch (s)

        self._batch_records: list[dict] = []       # one dict per batch for summary table

        self._write_run_header()

    # ── Public API ────────────────────────────────────────────────────────────

    def log_batch(
        self,
        batch_num:     int,
        total_batches: int,
        batch:         list[dict],
        results:       list[dict],
        batch_total_s: float,
        api_response=None,
        api_s:         float = 0.0,   # api-only latency from pipeline timing dict
        estimated_ads: int = -1,
    ) -> None:
        """Build and append one batch block to analysis.md."""

        # ── Build full prompt text ────────────────────────────────────────────
        from pipeline_compact import build_extraction_prompt
        input_text    = build_extraction_prompt(batch)
        output_text   = _extract_output_text(api_response)
        thinking_text = _extract_thinking_text(api_response)

        # ── Tokens & cost ─────────────────────────────────────────────────────
        usage = _extract_usage(api_response)
        in_tok  = usage["input_tokens"]
        out_tok = usage["output_tokens"]
        th_tok  = usage["thinking_tokens"]
        ca_tok  = usage["cache_tokens"]

        in_cost  = in_tok  * COST_INPUT_PER_TOKEN
        out_cost = out_tok * COST_OUTPUT_PER_TOKEN
        th_cost  = th_tok  * COST_THINKING_PER_TOKEN
        ca_cost  = ca_tok  * COST_CACHE_PER_TOKEN
        batch_cost = in_cost + out_cost + th_cost + ca_cost
        

        # ── Counts ────────────────────────────────────────────────────────────
        est_ads     = estimated_ads
        in_words    = _word_count(input_text)
        out_words   = _word_count(output_text)
        th_words    = _word_count(thinking_text)
        in_chars    = len(input_text)
        out_chars   = len(output_text)
        th_chars    = len(thinking_text)

        # ── Accumulate ────────────────────────────────────────────────────────
        self._total_input_tokens    += in_tok
        self._total_output_tokens   += out_tok
        self._total_thinking_tokens += th_tok
        self._total_cache_tokens    += ca_tok
        self._total_cost            += batch_cost
        self._daily_state = cost_manager.check_and_update_cost(batch_cost)

        self._total_msgs_in         += len(batch)
        self._total_ads_extracted   += len(results)
        self._total_est_ads         += est_ads

        self._total_input_words     += in_words
        self._total_output_words    += out_words
        self._total_input_chars     += in_chars
        self._total_output_chars    += out_chars

        self._batch_latencies.append(batch_total_s)
        if api_s:
            self._api_latencies.append(api_s)

        self._batch_records.append({
            "batch":       batch_num,
            "msgs":        len(batch),
            "est_ads":     est_ads,
            "extracted":   len(results),
            "in_tok":      in_tok,
            "out_tok":     out_tok,
            "th_tok":      th_tok,
            "ca_tok":      ca_tok,
            "cost":        batch_cost,
            "latency_s":   batch_total_s,
            "api_s":       api_s,
            "in_words":    in_words,
            "out_words":   out_words,
        })

        # ── Build markdown block ──────────────────────────────────────────────
        lines: list[str] = []

        lines.append(f"\n### Batch {batch_num}/{total_batches}\n")

       

        # Collapsible input
        lines.append(_section("Input"))
        lines.append(_collapsible(
            f"▶ Show input text ({in_words} words, {in_chars} chars, {in_tok} tokens)",
            _trunc(input_text),
        ))

        # Collapsible output
        lines.append(_section("Output"))
        lines.append(_collapsible(
            f"▶ Show output text ({out_words} words, {out_chars} chars, {out_tok} tokens)",
            _trunc(output_text) if output_text else "[no output captured]",
        ))

        # Collapsible thinking (only if present)
        if thinking_text:
            lines.append(_section("Thinking"))
            lines.append(_collapsible(
                f"▶ Show thinking text ({th_words}) words, ({out_chars}) chars, {th_tok} tokens)",
                _trunc(thinking_text),
            ))

        lines.append(_divider())

        block = "\n".join(lines)
        self._batch_blocks_list = getattr(self, "_batch_blocks_list", [])
        self._batch_blocks_list.append(block)
        self._append(block)

    def finalize(
        self,
        total_inserted: int,
        fstats:         dict,
    ) -> None:
        """Write the run summary block."""

        n = len(self._batch_records)

        # ── Averages ──────────────────────────────────────────────────────────
        avg_latency    = _safe_div(sum(self._batch_latencies), n)
        avg_api        = _safe_div(sum(self._api_latencies),   len(self._api_latencies)) if self._api_latencies else 0
        avg_in_tok     = _safe_div(self._total_input_tokens,    n)
        avg_out_tok    = _safe_div(self._total_output_tokens,   n)
        avg_in_words   = _safe_div(self._total_input_words,     n)
        avg_out_words  = _safe_div(self._total_output_words,    n)
        avg_extracted  = _safe_div(self._total_ads_extracted,   n)
        throughput     = _safe_div(self._total_ads_extracted,   sum(self._batch_latencies)) if self._batch_latencies else 0

        lines: list[str] = []
        lines.append("\n### Run Summary\n")

        # ── Per-batch overview table ───────────────────────────────────────────
        lines.append(_section("Per-Batch Overview"))
        lines.append(_multi_row_table(
            ["batch", "msgs", "est_ads", "extracted", "in_tok", "out_tok", "th_tok", "ca_tok", "cost", "latency_s", "api_s"],
            [
                [
                    r["batch"],
                    r["msgs"],
                    r["est_ads"],
                    r["extracted"],
                    r["in_tok"]    if r["in_tok"]  else "n/a",
                    r["out_tok"]   if r["out_tok"] else "n/a",
                    r["th_tok"]    or 0,
                    r["ca_tok"]    or 0,
                    f"${r['cost']:.5f}",
                    f"{r['latency_s']:.2f}",
                    f"{r['api_s']:.2f}" if r["api_s"] else "n/a",
                ]
                for r in self._batch_records
            ],
        ))

        # ── Totals & averages ─────────────────────────────────────────────────
        lines.append(_section("Totals"))
        lines.append(_md_table(
            ["msgs_in", "est_ads", "extracted", "total_s", "batches"],
            [
                self._total_msgs_in,
                self._total_est_ads,
                self._total_ads_extracted,
                f"{sum(self._batch_latencies):.2f}",
                n,
            ],
        ))

        lines.append(_section("Averages per Batch"))
        lines.append(_md_table(
            ["avg_latency_s", "avg_api_s", "avg_in_tok", "avg_out_tok", "avg_in_words", "avg_out_words", "avg_extracted", "ads/s"],
            [
                f"{avg_latency:.2f}",
                f"{avg_api:.2f}",
                f"{avg_in_tok:.0f}",
                f"{avg_out_tok:.0f}",
                f"{avg_in_words:.0f}",
                f"{avg_out_words:.0f}",
                f"{avg_extracted:.1f}",
                f"{throughput:.2f}",
            ],
        ))

        # ── Token breakdown ───────────────────────────────────────────────────
        lines.append(_section("Token Breakdown"))
        lines.append(_multi_row_table(
            ["type", "total_tokens", "total_cost", "avg_per_batch"],
            [
                ["input",      self._total_input_tokens,    _cost(self._total_input_tokens,    COST_INPUT_PER_TOKEN),    f"{avg_in_tok:.0f}"],
                ["output",     self._total_output_tokens,   _cost(self._total_output_tokens,   COST_OUTPUT_PER_TOKEN),   f"{avg_out_tok:.0f}"],
                ["thinking",   self._total_thinking_tokens, _cost(self._total_thinking_tokens, COST_THINKING_PER_TOKEN), f"{_safe_div(self._total_thinking_tokens, n):.0f}"],
                ["cache_read", self._total_cache_tokens,    _cost(self._total_cache_tokens,    COST_CACHE_PER_TOKEN),    f"{_safe_div(self._total_cache_tokens, n):.0f}"],
            ],
        ))
        lines.append(f"\n**Total run cost: ${self._total_cost:.6f}**\n")

        lines.append(_section("Daily Cost Status"))
        lines.append(_md_table(
            ["date", "spent", "limit"],
            [
                self._daily_state["date"],
                f"{self._daily_state['daily_cost']:.4f}",
                self._daily_state["max_daily_limit"]
            ]
        ))
                

        # ── Filter stats ──────────────────────────────────────────────────────
        lines.append(_section("Filter Stats"))
        lines.append(_md_table(
            ["system", "too_short", "blocklist", "no_keywords", "passed"],
            [
                fstats.get("system",      0),
                fstats.get("too_short",   0),
                fstats.get("blocklist",   0),
                fstats.get("no_keywords", 0),
                fstats.get("passed",      0),
            ],
        ))

        lines.append(f"\n**Listings inserted:** {total_inserted}\n")
        lines.append("\n" + "=" * 60 + "\n")

        self._append("\n".join(lines))
        print(f"      Analysis logged → {os.path.abspath(ANALYSIS_PATH)}")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _write_run_header(self) -> None:
        
        run_date, run_time =format_date_time(self.run_ts)
        header_lines = [
            f"\n## ({run_date})Run — ({run_time})",
            "",
            _md_table(
                ["model", "total_batches", "days", "file"],
                [self.model, self.total_batches, self.days, os.path.basename(self.chat_file)],
            ),
            "",
        ]
        self._append("\n".join(header_lines))

    def _append(self, text: str) -> None:
        with open(ANALYSIS_PATH, "a", encoding="utf-8") as f:
            f.write(text)


# ── Public factory ────────────────────────────────────────────────────────────

def open_analysis_log(
    run_ts:        str,
    model:         str,
    total_batches: int,
    days:          int,
    chat_file:     str,
) -> RunLogger:
    return RunLogger(run_ts, model, total_batches, days, chat_file)

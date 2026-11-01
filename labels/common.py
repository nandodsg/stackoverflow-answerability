"""Shared plumbing for the P3 quality-label scripts (specs/003, "Quality labels").

Keys come from the gitignored `.env` at the repo root (ANTHROPIC_API_KEY, TYPESAFE_API_KEY, AI_GATEWAY_API_KEY),
never from the command line. The Anthropic client gets the public API URL explicitly: some tools (Claude Code among
them) set ANTHROPIC_BASE_URL in their own shell, and the SDK would otherwise send the key there. Models from other
companies (Google, xAI) go through the Vercel AI Gateway's OpenAI-compatible API, with one key for all of them.

Every paid call is appended to labels/spend_log.csv (tokens and US$), so the README can state the real spend.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
from pathlib import Path

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parent.parent
LABELS = REPO / "labels"
CACHE = LABELS / ".cache"  # question text pulled from BigQuery; gitignored
SPEND_LOG = LABELS / "spend_log.csv"

BQ_PROJECT = os.environ.get("GCP_PROJECT", "so-answerability")
BQ_DATASET = "so_answerability"
BQ_MAX_GB = 10  # same limit as the EDA scripts: stop above it

# US$ per million tokens (Anthropic price list, 2026-10). Thinking tokens are billed as output.
PRICES = {
    "claude-opus-5-5": {"input": 4.00, "output": 20.00, "cache_write": 5.00, "cache_read": 0.20},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00, "cache_write": 2.50, "cache_read": 0.20},
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50, "cache_write": 0.125, "cache_read": 0.01},
}
# Vercel AI Gateway (ai-gateway.vercel.sh/v1/models, 2026-10-31), US regional prices, which are the higher ones.
# Reasoning tokens are billed as output.
GATEWAY_PRICES = {
    "google/gemini-4-argon": {"input": 2.20, "output": 11.00, "cache_write": 2.20, "cache_read": 0.11},
    "spacexai/grok-4.7": {"input": 2.20, "output": 6.60, "cache_write": 2.20, "cache_read": 0.55},
}
PRICES |= GATEWAY_PRICES
GATEWAY_URL = "https://ai-gateway.vercel.sh/v1"

load_dotenv(REPO / ".env")  # no override=True: .env never replaces a variable that is already set


def anthropic_client():
    from anthropic import Anthropic

    return Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], base_url="https://api.anthropic.com")


def gateway_client():
    from openai import OpenAI

    return OpenAI(api_key=os.environ["AI_GATEWAY_API_KEY"], base_url=GATEWAY_URL)


def tokens(usage) -> tuple[int, int, int, int]:
    """(input, output, cache write, cache read) from an Anthropic or an OpenAI-shaped usage object."""
    if hasattr(usage, "prompt_tokens"):  # OpenAI shape: cached tokens are part of prompt_tokens
        details = getattr(usage, "prompt_tokens_details", None)
        cached = (getattr(details, "cached_tokens", 0) or 0) if details else 0
        return (usage.prompt_tokens or 0) - cached, usage.completion_tokens or 0, 0, cached
    return (usage.input_tokens or 0, usage.output_tokens or 0,
            getattr(usage, "cache_creation_input_tokens", 0) or 0, getattr(usage, "cache_read_input_tokens", 0) or 0)


def usd(model: str, usage) -> float:
    if getattr(usage, "cost", None) is not None:  # the gateway reports what it billed; prefer it to the price list
        return float(usage.cost)
    p = PRICES[model]
    i, o, cw, cr = tokens(usage)
    return (i * p["input"] + o * p["output"] + cw * p["cache_write"] + cr * p["cache_read"]) / 1e6


def log_spend(run: str, step: str, model: str, usage) -> float:
    cost = usd(model, usage)
    new = not SPEND_LOG.exists()
    with SPEND_LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["logged_at_utc", "run", "step", "model", "input_tokens", "output_tokens",
                        "cache_write_tokens", "cache_read_tokens", "usd"])
        w.writerow([dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), run, step, model,
                    *tokens(usage), f"{cost:.4f}"])
    return cost


def bq_query(sql: str):
    """Dry-run first; stop above BQ_MAX_GB; then run with the same limit as maximum_bytes_billed."""
    from google.cloud import bigquery

    client = bigquery.Client(project=BQ_PROJECT)
    dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    gb = dry.total_bytes_processed / 1e9
    print(f"BigQuery dry run: {gb:.2f} GB")
    if gb > BQ_MAX_GB:
        raise SystemExit(f"Over the {BQ_MAX_GB} GB limit: not run.")
    job = client.query(sql, job_config=bigquery.QueryJobConfig(maximum_bytes_billed=int(BQ_MAX_GB * 1e9)))
    return [dict(row) for row in job.result()]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

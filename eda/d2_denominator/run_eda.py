"""D2 EDA: accepted rate out of all questions (A) vs out of answered questions (B).

Runs sql/single_tag_by_year.sql against BigQuery (cached as a CSV in ./output) and reuses the 2022 tag table cached by
the D1 EDA, then writes output/summary.md. The query is dry-run first, so the bytes it scans are printed before it runs.

    python eda/d2_denominator/run_eda.py              # reuses cached CSVs when present
    python eda/d2_denominator/run_eda.py --refresh    # requeries BigQuery (the D1 tag table is never requeried here)
"""

import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from google.cloud import bigquery

PROJECT = "so-answerability"
HERE = Path(__file__).resolve().parent
SQL_DIR = HERE / "sql"
OUT_DIR = HERE / "output"
# Run eda/d1_sample_size/run_eda.py first if this file is missing.
TAG_STATS = HERE.parent / "d1_sample_size" / "output" / "tag_stats_2022.csv"

# D1 decision (specs/001): rank only groups with >= 385 in the rate's denominator.
RANKING_CUTOFF = 385
TOP_N = 10
Z95 = 1.96


def query(client, name, refresh, max_gb):
    """Run sql/<name>.sql, caching the result as a CSV."""
    path = OUT_DIR / f"{name}.csv"
    if path.exists() and not refresh:
        return pd.read_csv(path, keep_default_na=False)

    sql = (SQL_DIR / f"{name}.sql").read_text(encoding="utf-8")
    dry_run = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    gb = dry_run.total_bytes_processed / 1e9
    print(f"{name}: scans {gb:.2f} GB")
    if gb > max_gb:
        sys.exit(f"{name}: stopped, {gb:.2f} GB is over the {max_gb:g} GB limit; rerun with --allow-gb {math.ceil(gb)}")
    max_bytes = int(max_gb * 1e9)  # BigQuery itself refuses the real run past this

    job_config = bigquery.QueryJobConfig(maximum_bytes_billed=max_bytes)
    df = client.query(sql, job_config=job_config).to_dataframe(create_bqstorage_client=False)
    df.to_csv(path, index=False)
    return df


def wilson_bounds(k, n, z=Z95):
    """Wilson score interval for k successes out of n (same formula as the D1 EDA)."""
    p = k / n
    centre = p + z**2 / (2 * n)
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    denominator = 1 + z**2 / n
    return (centre - margin) / denominator, (centre + margin) / denominator


def add_rates(df):
    """Answer rate, A (accepted / questions) and B (accepted / answered); A = answer rate × B."""
    df = df.copy()
    df["answer_rate"] = df["n_answered"] / df["n_questions"]
    df["accepted_rate"] = df["n_accepted"] / df["n_questions"]
    df["accepted_among_answered"] = df["n_accepted"] / df["n_answered"]
    df["a_lower"], df["a_upper"] = wilson_bounds(df["n_accepted"], df["n_questions"])
    df["b_lower"], df["b_upper"] = wilson_bounds(df["n_accepted"], df["n_answered"])
    return df


# --- Markdown ------------------------------------------------------------------------------------------------

def fmt(value):
    if isinstance(value, (float, np.floating)):
        return f"{value:.3f}"
    if isinstance(value, (int, np.integer)):
        return f"{value:,}"
    return str(value)


def md_table(df):
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


TAG_COLUMNS = ["tag", "n_questions", "n_answered", "answer_rate", "accepted_rate", "accepted_among_answered"]


def tag_sections(tags):
    """Lowest and highest 10 tags under A and under two ways of ranking B, plus the overlaps."""
    by_questions = tags[tags["n_questions"] >= RANKING_CUTOFF]
    by_answered = tags[tags["n_answered"] >= RANKING_CUTOFF]
    lists = {
        "A, floor on questions (the D2 decision)": (by_questions, "a_lower", "a_upper"),
        "B, floor on answered questions": (by_answered, "b_lower", "b_upper"),
        "B, floor on questions": (by_questions, "b_lower", "b_upper"),
    }
    tops = {name: df.nlargest(TOP_N, lower) for name, (df, lower, _) in lists.items()}
    bottoms = {name: df.nsmallest(TOP_N, upper) for name, (df, _, upper) in lists.items()}

    a_name = next(iter(lists))
    a_bottom = bottoms[a_name]
    sections = [
        "## Tags, 2022",
        f"Eligible tags: {len(by_questions):,} with ≥ {RANKING_CUTOFF} questions; {len(by_answered):,} with "
        f"≥ {RANKING_CUTOFF} answered questions. Of the {TOP_N} lowest tags under A, "
        f"{int((a_bottom['n_answered'] >= RANKING_CUTOFF).sum())} have ≥ {RANKING_CUTOFF} answered questions: a "
        "floor on answered questions removes exactly the tags few people answer.",
        "### Overlap with the A lists (out of 10)",
        md_table(pd.DataFrame({
            "B ranking": list(lists)[1:],
            "top-10 overlap": [len(set(tops[a_name]["tag"]) & set(tops[name]["tag"])) for name in list(lists)[1:]],
            "bottom-10 overlap": [
                len(set(a_bottom["tag"]) & set(bottoms[name]["tag"])) for name in list(lists)[1:]
            ],
        })),
    ]
    for name in lists:
        sections += [f"### Lowest 10 — {name}", md_table(bottoms[name][TAG_COLUMNS])]
    sections += [f"### Highest 10 — {a_name}", md_table(tops[a_name][TAG_COLUMNS])]
    return sections


def single_tag_section(by_year):
    table = by_year[[
        "tag", "creation_year", "n_questions", "n_answered", "answer_rate",
        "accepted_rate", "a_lower", "a_upper", "accepted_among_answered", "b_lower", "b_upper",
    ]]
    return [
        "## Questions tagged only `python` or only `dbt`, 2013–2022",
        "2022 is partial (data ends 2022-09-25). a_lower / a_upper and b_lower / b_upper are 95% Wilson bounds.",
        md_table(table),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--refresh", action="store_true", help="requery BigQuery instead of using cached CSVs")
    parser.add_argument("--allow-gb", type=float, default=10, help="largest dry-run estimate a query may scan, in GB")
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    client = bigquery.Client(project=PROJECT)
    by_year = add_rates(query(client, "single_tag_by_year", args.refresh, args.allow_gb))
    # keep_default_na=False: "null", "nan" and "na" are real tags, not missing values.
    tags = add_rates(pd.read_csv(TAG_STATS, keep_default_na=False))

    pooled = tags[["n_questions", "n_answered", "n_accepted"]].sum()
    summary = [
        "# D2 EDA — accepted rate out of all questions (A) vs out of answered questions (B)",
        "Generated by `run_eda.py`; do not edit by hand. A = accepted / questions; B = accepted / answered "
        "questions; A = answer rate × B.",
        f"Pooled over question–tag links, 2022: A = {pooled['n_accepted'] / pooled['n_questions']:.3f}, "
        f"B = {pooled['n_accepted'] / pooled['n_answered']:.3f}.",
        *tag_sections(tags),
        *single_tag_section(by_year),
    ]
    (OUT_DIR / "summary.md").write_text("\n\n".join(summary) + "\n", encoding="utf-8")
    print(f"wrote {OUT_DIR / 'summary.md'}")


if __name__ == "__main__":
    main()

"""Export the final dbt marts to CSV files the presentation page loads (presentation/data/*.csv).

NOT part of CI and never run by the page: it queries BigQuery, so Nando runs it by hand once the marts are final.

    python presentation/export_marts.py                 # every mart in EXPORTS
    python presentation/export_marts.py --only mart_p1_tags
    python presentation/export_marts.py --dry-run       # prints bytes each query would scan, writes nothing

Needs `GCP_PROJECT` (same variable as profiles.example.yml) and `gcloud auth application-default login`.
Cost guard: each query carries `maximum_bytes_billed` (1 GiB, the marts are a few MB), the same idea as the dbt targets.

Every file starts with one comment line, the CC BY-SA attribution Stack Overflow's data licence asks for; the page and
presentation/check_data.py both skip that first line when reading.
"""
import argparse
import csv
import datetime
import os
import pathlib

DATASET = "so_answerability"
OUT_DIR = pathlib.Path(__file__).parent / "data"
MAX_BYTES = 1024**3  # 1 GiB per query

# mart -> columns the page's SQL relies on (check_data.py verifies the shipped files contain them).
# The six P3 marts chapter 7 uses (rule-based rates and effects, then the quality labels: rates, effects, each label
# against its rule neighbour, and what a label adds beyond the rules); the leakage KPI and the answer lens stay out.
EXPORTS = {
    "mart_p1_tags": [
        "creation_year", "tag", "n_questions", "answer_rate", "accepted_rate", "accepted_rate_among_answered",
        "accepted_rate_lower", "accepted_rate_upper", "answers_per_question", "answers_per_question_lower",
        "answers_per_question_upper", "answers_interval_reliable", "tag_exposure",
        "rank_accepted_top", "rank_accepted_bottom", "rank_answers_top", "rank_answers_bottom",
    ],
    # the same rules on unordered tag pairs (tag_a < tag_b), for the "combinations of tags" part of P1
    "mart_p1_pairs": [
        "creation_year", "tag_a", "tag_b", "n_questions", "answer_rate", "accepted_rate",
        "accepted_rate_among_answered", "accepted_rate_lower", "accepted_rate_upper", "answers_per_question",
        "answers_per_question_lower", "answers_per_question_upper", "tag_exposure",
        "rank_accepted_top", "rank_accepted_bottom", "rank_answers_top", "rank_answers_bottom",
    ],
    "mart_p2_python_dbt": [
        "tag", "creation_year", "n_questions", "answer_rate", "accepted_rate", "answers_per_question", "tag_exposure",
    ],
    "mart_p3_feature_rates": [
        "version", "feature", "bucket", "cohort", "is_reference_bucket", "n_questions", "answer_rate", "accepted_rate",
        "accepted_rate_lower", "accepted_rate_upper", "accepted_rate_among_answered",
    ],
    "mart_p3_feature_effects": [
        "version", "feature", "bucket", "cohort", "n_questions", "accepted_rate_effect", "accepted_rate_effect_margin",
        "accepted_rate_effect_tag_adjusted", "accepted_rate_effect_stable", "answer_rate_effect",
        "accepted_rate_effect_flips_vs_original",
    ],
    "mart_p3_label_rates": [
        "version", "feature", "bucket", "cohort", "is_reference_bucket", "n_questions", "answer_rate", "accepted_rate",
        "accepted_rate_lower", "accepted_rate_upper", "accepted_rate_among_answered",
    ],
    "mart_p3_label_effects": [
        "version", "feature", "bucket", "cohort", "n_questions", "accepted_rate_effect", "accepted_rate_effect_margin",
        "accepted_rate_effect_tag_adjusted", "accepted_rate_effect_stable", "answer_rate_effect", "full_years_with_effect",
    ],
    "mart_p3_label_vs_rules": [
        "label", "level", "rule_feature", "rule_value", "n_questions", "share_of_level", "share_of_rule_value",
    ],
    "mart_p3_label_incremental": [
        "label", "level", "n_questions", "reference_n_questions", "raw_effect", "rules_adjusted_effect", "adjusted_coverage",
    ],
}


def attribution_line(exported_on, placeholder=False):
    if placeholder:
        return ("# PLACEHOLDER: invented numbers for building the page, not Stack Overflow data. "
                "The export script replaces this file with a snapshot of the dbt mart.")
    return (f"# Source: Stack Overflow content (bigquery-public-data.stackoverflow), (c) Stack Exchange Inc. and its "
            f"contributors, licensed CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). "
            f"Snapshot of the dbt mart, exported {exported_on}.")


def write_csv(path, header, rows, first_line):
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(first_line + "\n")
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", action="append", choices=sorted(EXPORTS), help="export just this mart (repeatable)")
    ap.add_argument("--dry-run", action="store_true", help="report bytes to scan, write nothing")
    args = ap.parse_args()

    from google.cloud import bigquery  # imported here so check_data.py can import this module without the client

    project = os.environ["GCP_PROJECT"]
    client = bigquery.Client(project=project)
    today = datetime.date.today().isoformat()
    OUT_DIR.mkdir(exist_ok=True)

    for mart in args.only or EXPORTS:
        sql = f"SELECT * FROM `{project}.{DATASET}.{mart}`"
        dry = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
        print(f"{mart}: would scan {dry.total_bytes_processed / 1e6:.1f} MB")
        if args.dry_run:
            continue
        job = client.query(sql, job_config=bigquery.QueryJobConfig(maximum_bytes_billed=MAX_BYTES))
        result = job.result()
        header = [field.name for field in result.schema]
        rows = [list(row.values()) for row in result]
        write_csv(OUT_DIR / f"{mart}.csv", header, rows, attribution_line(today))
        print(f"  wrote {len(rows)} rows to presentation/data/{mart}.csv")


if __name__ == "__main__":
    main()

"""Reconcile the MetricFlow semantic layer with the numbers the README quotes.

MetricFlow metrics are not dbt tests, so this script plays that role: it runs `mf query` for each check, compares the
result with the expected number, and prints one PASS / FAIL line per check with the acceptance criterion it covers.
Exit code 1 if any check fails.

Before running: `dbt build --select path:models/semantic` (the sem_* views) and `dbt parse` (the semantic manifest that
`mf` reads). Each `mf query` is billed (about 0.05-1.7 GB on the sandbox). By default `mf` is called as `mf`; set the
MF_CMD environment variable to use another command, e.g. MF_CMD="python path/to/mf_wrapper.py".

    python tests/semantic/check_semantic_layer.py
"""
import csv
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

MF_CMD = shlex.split(os.environ.get("MF_CMD", "mf"))
MIN_QUESTIONS = 385  # the D1 floor (specs/001, AC-1.2)

results = []


def mf_query(*args):
    """Run one `mf query` and return its rows as a list of dicts (strings)."""
    with tempfile.TemporaryDirectory() as folder:
        out = Path(folder, "result.csv")
        command = [*MF_CMD, "query", *args, "--csv", str(out)]
        done = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
        if done.returncode != 0 or not out.exists():
            raise RuntimeError(f"mf query failed: {' '.join(args)}\n{done.stdout}\n{done.stderr}")
        with open(out, newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))


def check(ac, description, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {ac:<8} {description}  {detail}")


def dim(name):
    return "{{ Dimension('" + name + "') }}"


# 1. 2022 baseline, whole questions: README says the accepted rate is 30.5%; AC-0.5: accepted rate = answer rate x
#    accepted rate among answered (D2).
row = mf_query(
    "--metrics", "accepted_rate,answer_rate,accepted_rate_among_answered",
    "--group-by", "question__creation_year",
    "--where", f"{dim('question__creation_year')} = 2022",
)[0]
accepted, answered, among = (float(row[k]) for k in ("accepted_rate", "answer_rate", "accepted_rate_among_answered"))
check("README", "2022 baseline accepted rate is 30.5%", round(accepted * 100, 1) == 30.5, f"({accepted:.4f})")
check("AC-0.5", "accepted rate = answer rate x accepted rate among answered", abs(accepted - answered * among) < 1e-9)

# 2. P2, exact python-only and dbt-only (tag_count = 1 means the question carries that tag alone, AC-2.1).
p2 = mf_query(
    "--metrics", "by_tag_answers_per_question,by_tag_questions_per_answer",
    "--group-by", "question_tag__tag,question_tag__creation_year",
    "--where", f"{dim('question_tag__tag')} IN ('python', 'dbt') AND {dim('question_tag__tag_count')} = 1",
)
apq = {(r["question_tag__tag"], int(r["question_tag__creation_year"])): float(r["by_tag_answers_per_question"]) for r in p2}
qpa = {(r["question_tag__tag"], int(r["question_tag__creation_year"])): float(r["by_tag_questions_per_answer"]) for r in p2}
expected = {("python", 2013): 2.31, ("python", 2021): 1.52, ("python", 2022): 1.26,
            ("dbt", 2020): 1.39, ("dbt", 2021): 1.14, ("dbt", 2022): 1.06}
for (tag, year), value in expected.items():
    got = apq.get((tag, year))
    check("README", f"{tag}-only answers per question {year} = {value}", got is not None and round(got, 2) == value,
          f"({got})")
check("AC-0.6", "questions per answer = 1 / answers per question, every python / dbt year",
      all(abs(qpa[key] * apq[key] - 1) < 1e-9 for key in apq if apq[key] and key in qpa), f"({len(apq)} rows)")

# 3. P1, 2022: how many groups pass the 385-question floor. The mart does this in SQL; MetricFlow cannot filter on a
#    metric, so the busiest groups are fetched (more than the expected number) and the floor is applied here.
for label, metric, group_by, expected_count in (
    ("tags", "by_tag_questions", "question_tag__tag", 1162),
    ("tag pairs", "by_pair_questions", "question_pair__tag_a,question_pair__tag_b", 1026),
):
    family = "question_tag" if label == "tags" else "question_pair"
    rows = mf_query(
        "--metrics", metric,
        "--group-by", group_by,
        "--where", f"{dim(family + '__creation_year')} = 2022",
        "--order", f"-{metric}",
        "--limit", "3000",
    )
    ranked = sum(1 for r in rows if int(float(r[metric])) >= MIN_QUESTIONS)
    check("AC-1.2", f"2022 ranked {label} (>= {MIN_QUESTIONS} questions) = {expected_count}", ranked == expected_count,
          f"({ranked}; fetched {len(rows)})")

# 4. 30-day-window variant (specs/001 "Metrics", censoring). The expected numbers were read once from the marts
#    mart_p1_tags_30d / mart_p1_pairs_30d (rank 1 of the accepted-rate "top" and "bottom" lists and the number of ranked
#    groups, per year); the semantic layer must rebuild them from the question rows. Counts (not rounded rates) are
#    compared: if the four counts of a group match, every ratio metric of that group matches too.
#    family, year: ranked groups, then (group, questions, answered, accepted, answers) of the top and the bottom group.
WINDOW_30D = {
    ("tags", 2022): (1020, ("jq", 737, 707, 506, 1057), ("magento2", 425, 160, 37, 181)),
    ("tags", 2021): (1414, ("purrr", 596, 542, 447, 887), ("facebook", 1154, 457, 164, 506)),
    ("pairs", 2022): (884, ("dataframe|dplyr", 569, 539, 413, 985), ("android|webview", 442, 134, 43, 152)),
    ("pairs", 2021): (1450, ("r|regex", 583, 565, 477, 1073), ("google-chrome|google-chrome-extension", 588, 225, 94, 244)),
}
for (label, year), (expected_ranked, *groups) in WINDOW_30D.items():
    prefix, family = ("by_tag_30d_", "question_tag_30d") if label == "tags" else ("by_pair_30d_", "question_pair_30d")
    keys = [f"{family}__tag"] if label == "tags" else [f"{family}__tag_a", f"{family}__tag_b"]
    rows = mf_query(
        "--metrics", prefix + "questions",
        "--group-by", ",".join(keys),
        "--where", f"{dim(family + '__creation_year')} = {year}",
        "--order", f"-{prefix}questions",
        "--limit", "3000",
    )
    ranked = sum(1 for r in rows if int(float(r[prefix + "questions"])) >= MIN_QUESTIONS)
    check("AC-1.2", f"30-day window {year} ranked {label} (>= {MIN_QUESTIONS} questions) = {expected_ranked}",
          ranked == expected_ranked, f"({ranked}; fetched {len(rows)})")
    for position, (group, *expected_counts) in zip(("top", "bottom"), groups):
        parts = group.split("|")
        where = " AND ".join(f"{dim(key)} = '{part}'" for key, part in zip(keys, parts))
        where += f" AND {dim(family + '__creation_year')} = {year}"
        row = mf_query(
            "--metrics", ",".join(prefix + m for m in ("questions", "answered_questions", "accepted_questions", "answers")),
            "--where", where,
        )[0]
        got = [int(float(row[prefix + m])) for m in ("questions", "answered_questions", "accepted_questions", "answers")]
        check("AC-1.2", f"30-day window {year} {label} {position} accepted-rate group {group}: counts match the mart",
              got == expected_counts, f"({got} vs {expected_counts})")
        accepted_rate = float(mf_query("--metrics", prefix + "accepted_rate", "--where", where)[0][prefix + "accepted_rate"])
        check("AC-0.5", f"  its accepted rate = accepted / questions", abs(accepted_rate - expected_counts[2] / expected_counts[0]) < 1e-9)

failed = results.count(False)
print(f"\n{len(results) - failed} passed, {failed} failed")
sys.exit(1 if failed else 0)

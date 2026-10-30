"""D1 EDA, answers-per-question ranking: which ranking rule to use for a mean, and why not a heavier one.

Runs the SQL in ./sql against BigQuery (cached as CSVs in ./output), then writes output/summary.md. Answers per
question is a mean of answer_count, so its 95% interval is mean ± 1.96 × SE (decided with D3, specs/000). Three rules
for ranking it, all on groups with >= 385 questions (D1 floor):

- bounds (chosen): "highest" sorted by the lower bound of mean ± 1.96 × SE, "lowest" by the upper bound;
- raw mean: sorted by the mean itself;
- bootstrap: sorted by the bounds of a percentile bootstrap interval, which needs no normal approximation.

answer_count is skewed (most questions have 0–2 answers, a few have dozens), so the script checks whether the normal
approximation holds (Cochran's rule, n > 25 × skewness², and a coverage simulation), then compares the three rules,
plus the empirical-Bayes mean that D1 keeps as a robustness check, on what they change and what they cost.

    python eda/d1_answers_ranking/run_eda.py              # reuses cached CSVs when present
    python eda/d1_answers_ranking/run_eda.py --refresh    # requeries BigQuery
"""

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd
from google.cloud import bigquery

PROJECT = "so-answerability"
HERE = Path(__file__).resolve().parent
SQL_DIR = HERE / "sql"
OUT_DIR = HERE / "output"

MIN_QUESTIONS = 30  # smallest group kept by the moments SQL; the empirical-Bayes fit uses every group from here up
RANKING_CUTOFF = 385  # D1 floor (specs/001)
TOP_N = 10
Z95 = 1.96
BOOTSTRAP_RESAMPLES = 2_000
COVERAGE_SIMULATIONS = 2_000
SEED = 2022


# --- BigQuery ------------------------------------------------------------------------------------------------

def query(client, name, year, refresh, min_questions):
    """Run sql/<name>.sql with @year and @min_questions, caching the result as a CSV."""
    path = OUT_DIR / f"{name}_{year}.csv"
    if path.exists() and not refresh:
        # keep_default_na=False: "null", "nan" and "na" are real tags, not missing values.
        return pd.read_csv(path, keep_default_na=False)

    sql = (SQL_DIR / f"{name}.sql").read_text(encoding="utf-8")
    params = [
        bigquery.ScalarQueryParameter("year", "INT64", year),
        bigquery.ScalarQueryParameter("min_questions", "INT64", min_questions),
    ]
    dry_run = client.query(
        sql, job_config=bigquery.QueryJobConfig(query_parameters=params, dry_run=True, use_query_cache=False)
    )
    print(f"{name}: scans {dry_run.total_bytes_processed / 1e9:.2f} GB")

    df = client.query(sql, job_config=bigquery.QueryJobConfig(query_parameters=params)).to_dataframe(
        create_bqstorage_client=False
    )
    df.to_csv(path, index=False)
    return df


# --- Statistics ----------------------------------------------------------------------------------------------

def wilson_bounds(k, n, z=Z95):
    """Wilson score interval, as in D1; used here only to rank answer rate for comparison."""
    p = k / n
    centre = p + z**2 / (2 * n)
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    denominator = 1 + z**2 / n
    return (centre - margin) / denominator, (centre + margin) / denominator


def add_mean_columns(df):
    """Mean, SD, SE, 95% bounds and skewness of answer_count per group, from its sums of powers."""
    df = df.copy()
    n = df["n_questions"].astype(float)
    mean = df["sum_answers"] / n
    m2 = df["sum_answers_sq"] / n - mean**2  # population variance
    m3 = df["sum_answers_cube"] / n - 3 * mean * df["sum_answers_sq"] / n + 2 * mean**3
    df["answers_per_question"] = mean
    df["sd"] = np.sqrt(m2 * n / (n - 1))
    df["se"] = df["sd"] / np.sqrt(n)
    df["lower"] = mean - Z95 * df["se"]
    df["upper"] = mean + Z95 * df["se"]
    df["half_width"] = Z95 * df["se"]
    df["skewness"] = m3 / m2**1.5
    # Cochran's rule of thumb: the sample mean is close enough to normal when n > 25 × skewness².
    df["cochran_ok"] = n > 25 * df["skewness"] ** 2
    df["answer_rate"] = df["n_answered"] / n
    df["answer_rate_lower"], df["answer_rate_upper"] = wilson_bounds(df["n_answered"], n)
    df["shrunk_mean"], prior_strength = shrink_to_pooled(df)
    return df, prior_strength


def shrink_to_pooled(df):
    """Empirical Bayes for a mean: pull each group's mean toward the pooled mean, more when its SE is large.

    Normal–normal model fitted by method of moments on every group in df: weight = τ² / (τ² + SE²), where τ² is the
    spread of true group means (observed spread minus average sampling noise). Also returns the prior strength in
    "virtual questions": average within-group variance / τ².
    """
    pooled = df["sum_answers"].sum() / df["n_questions"].sum()
    means = df["sum_answers"] / df["n_questions"]
    se2 = (df["sd"] / np.sqrt(df["n_questions"])) ** 2
    between_var = max(means.var() - se2.mean(), 1e-6)
    weight = between_var / (between_var + se2)
    return pooled + weight * (means - pooled), (df["sd"] ** 2).mean() / between_var


def per_group(dist, key):
    """Yield (group, answer_count values, question counts) from a (group, answer_count, n_questions) table."""
    for name, rows in dist.groupby(key, sort=False):
        yield name, rows["answer_count"].to_numpy(float), rows["n_questions"].to_numpy()


def bootstrap_bounds(dist, key, rng):
    """95% percentile bootstrap interval of the mean per group, and the seconds it took.

    Resampling a group's questions with replacement = drawing its answer_count counts from a multinomial with the
    observed shares, so the frequency table is enough: no question-level rows needed.
    """
    start = time.perf_counter()
    rows = []
    for name, values, counts in per_group(dist, key):
        n = counts.sum()
        draws = rng.multinomial(n, counts / n, size=BOOTSTRAP_RESAMPLES)
        means = draws @ values / n
        lower, upper = np.percentile(means, [2.5, 97.5])
        rows.append({key: name, "boot_lower": lower, "boot_upper": upper})
    return pd.DataFrame(rows), time.perf_counter() - start


def normal_coverage(dist, key, rng):
    """How often mean ± 1.96 × SE contains the true mean, taking each group's observed distribution as the truth.

    Draws COVERAGE_SIMULATIONS samples of the group's size from its own answer_count distribution, builds the interval
    from each sample, and counts how often it covers the group's mean. 95% means the approximation is right.
    """
    rows = []
    for name, values, counts in per_group(dist, key):
        n = counts.sum()
        true_mean = values @ counts / n
        draws = rng.multinomial(n, counts / n, size=COVERAGE_SIMULATIONS)
        means = draws @ values / n
        variances = (draws @ values**2 - n * means**2) / (n - 1)
        half_width = Z95 * np.sqrt(variances / n)
        rows.append({key: name, "coverage": np.mean(np.abs(means - true_mean) <= half_width)})
    return pd.DataFrame(rows)


# --- Summary -------------------------------------------------------------------------------------------------

def fmt(value):
    if isinstance(value, (bool, np.bool_)):
        return "yes" if value else "no"
    if isinstance(value, (float, np.floating)):
        if float(value).is_integer() and abs(value) >= 1:
            return f"{value:,.0f}"
        return f"{value:,.3f}"
    if isinstance(value, (int, np.integer)):
        return f"{value:,}"
    return str(value)


def md_table(df):
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


# Sort keys per rule: (column for "highest", column for "lowest").
RULES = {
    "bounds (chosen)": ("lower", "upper"),
    "raw mean": ("answers_per_question", "answers_per_question"),
    "bootstrap": ("boot_lower", "boot_upper"),
    "empirical Bayes (robustness check)": ("shrunk_mean", "shrunk_mean"),
    "answer rate, Wilson (other metric)": ("answer_rate_lower", "answer_rate_upper"),
}


def three_options(eligible, name_col, boot_seconds):
    """What the raw mean and the bootstrap change versus the bounds, and what each costs."""

    def names(col, ascending):
        return set(eligible.sort_values(col, ascending=ascending).head(TOP_N)[name_col])

    chosen_hi, chosen_lo = RULES["bounds (chosen)"]
    top, bottom = names(chosen_hi, False), names(chosen_lo, True)
    agreement = pd.DataFrame([
        {
            "rule": rule,
            f"top-{TOP_N} overlap": len(top & names(hi, False)),
            f"bottom-{TOP_N} overlap": len(bottom & names(lo, True)),
            # Rank correlation over every ranked group, highest-list key vs the bounds' key.
            "rank correlation": eligible[hi].rank().corr(eligible[chosen_hi].rank()),
        }
        for rule, (hi, lo) in RULES.items()
    ])

    gap = pd.concat([(eligible["lower"] - eligible["boot_lower"]).abs(),
                     (eligible["upper"] - eligible["boot_upper"]).abs()], axis=1).max(axis=1)
    gap_share = gap / eligible["half_width"]
    skewed = ~eligible["cochran_ok"]
    bound_gap = pd.DataFrame([
        {"groups": "all ranked", "n": len(eligible), "median gap": gap.median(), "max gap": gap.max(),
         "median gap / half-width": gap_share.median(), "max gap / half-width": gap_share.max()},
        {"groups": "failing Cochran's rule", "n": int(skewed.sum()), "median gap": gap[skewed].median(),
         "max gap": gap[skewed].max(), "median gap / half-width": gap_share[skewed].median(),
         "max gap / half-width": gap_share[skewed].max()},
    ])

    coverage = pd.DataFrame([
        {"groups": label, "n": len(cov), "min coverage": cov.min(), "p10 coverage": cov.quantile(0.1),
         "median coverage": cov.median()}
        for label, cov in [("all ranked", eligible["coverage"]),
                           ("failing Cochran's rule", eligible.loc[skewed, "coverage"])]
    ])
    worst = eligible.sort_values("coverage").head(5)[
        [name_col, "n_questions", "answers_per_question", "skewness", "max_answers", "coverage"]
    ]

    n_links = int(eligible["n_questions"].sum())
    return [
        f"### Three ranking rules: what changes ({len(eligible):,} ranked)",
        "Overlap of each rule's top / bottom 10 with the bounds' lists, and rank correlation of its \"highest\" sort "
        "key with the lower bound over every ranked group.",
        md_table(agreement),
        "### Bootstrap vs mean ± 1.96 × SE: how far apart are the bounds? (answers per question)",
        md_table(bound_gap),
        f"### Does mean ± 1.96 × SE really cover 95%? ({COVERAGE_SIMULATIONS:,} simulated samples per group)",
        md_table(coverage),
        "Lowest coverage:",
        md_table(worst),
        "### What each rule costs",
        md_table(pd.DataFrame([
            {"rule": "raw mean", "per group": "n, Σx", "in dbt on BigQuery": "one GROUP BY",
             "repeatable": "yes", "this run": "—"},
            {"rule": "bounds (chosen)", "per group": "n, Σx, Σx²", "in dbt on BigQuery": "the same GROUP BY",
             "repeatable": "yes", "this run": "—"},
            {"rule": "bootstrap", "per group": f"{BOOTSTRAP_RESAMPLES:,} resamples",
             "in dbt on BigQuery": f"SQL: {BOOTSTRAP_RESAMPLES:,} × {n_links:,} = "
                                   f"{BOOTSTRAP_RESAMPLES * n_links / 1e9:.1f}B rows; or a Python model (Dataproc, "
                                   "needs billing: not in the sandbox)",
             "repeatable": "only with a fixed seed (BigQuery RAND() takes none)",
             "this run": f"{boot_seconds:.1f} s locally, from a pre-aggregated table"},
            {"rule": "empirical Bayes", "per group": "n, Σx, Σx² + a prior fitted on every group ≥ 30",
             "in dbt on BigQuery": "a second model for the fit", "repeatable": "yes, but moves when the fit set "
             "changes", "this run": "—"},
        ])),
    ]


def sections(df, dist, name_col, label, prior_strength, rng):
    boot, boot_seconds = bootstrap_bounds(dist, name_col, rng)
    df = df.merge(boot, on=name_col, how="left").merge(normal_coverage(dist, name_col, rng), on=name_col, how="left")
    eligible = df[df["n_questions"] >= RANKING_CUTOFF]
    assert eligible["boot_lower"].notna().all(), "every ranked group needs its answer_count distribution"
    cols = [name_col, "n_questions", "answers_per_question", "lower", "upper", "sd", "skewness", "max_answers",
            "answer_rate"]

    precision = eligible[["sd", "half_width", "skewness"]].quantile([0.1, 0.5, 0.9, 1.0])
    precision.index = ["p10", "median", "p90", "max"]
    failing = eligible[~eligible["cochran_ok"]]
    return [
        f"## {label} with ≥ {RANKING_CUTOFF} questions ({len(eligible):,} {label})",
        f"Pooled answers per question {eligible['sum_answers'].sum() / eligible['n_questions'].sum():.3f}. "
        f"Empirical-Bayes prior strength (fitted on {len(df):,} {label} with ≥ {MIN_QUESTIONS} questions): "
        f"{prior_strength:.0f} virtual questions at the pooled mean.",
        "### Precision at the floor (SD and 95% half-width of answers per question; skewness of answer_count)",
        md_table(precision.reset_index().rename(columns={"index": "quantile"})),
        f"### Normal approximation: Cochran's rule (n > 25 × skewness²) fails for {len(failing):,} of "
        f"{len(eligible):,} {label}",
        md_table(failing.sort_values("skewness", ascending=False).head(TOP_N)[cols]) if len(failing) else "None.",
        f"### Highest: top {TOP_N} by lower bound",
        md_table(eligible.sort_values("lower", ascending=False).head(TOP_N)[cols]),
        f"### Lowest: bottom {TOP_N} by upper bound",
        md_table(eligible.sort_values("upper").head(TOP_N)[cols]),
        *three_options(eligible, name_col, boot_seconds),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--year", type=int, default=2022)
    parser.add_argument("--refresh", action="store_true", help="requery BigQuery instead of using cached CSVs")
    args = parser.parse_args()
    OUT_DIR.mkdir(exist_ok=True)

    client = bigquery.Client(project=PROJECT)
    rng = np.random.default_rng(SEED)

    tags, tag_strength = add_mean_columns(
        query(client, "tag_answer_moments", args.year, args.refresh, MIN_QUESTIONS))
    tag_dist = query(client, "tag_answer_distribution", args.year, args.refresh, RANKING_CUTOFF)

    pairs = query(client, "tag_pair_answer_moments", args.year, args.refresh, MIN_QUESTIONS)
    pair_dist = query(client, "tag_pair_answer_distribution", args.year, args.refresh, RANKING_CUTOFF)
    for df in (pairs, pair_dist):
        df["pair"] = df["tag_a"] + " + " + df["tag_b"]
    pairs, pair_strength = add_mean_columns(pairs)

    summary = [
        f"# D1 EDA — answers-per-question ranking ({args.year})",
        "Generated by `run_eda.py`; do not edit by hand. 2022 is partial (data ends 2022-09-25). Interval: "
        "mean ± 1.96 × SE of answer_count per group (specs/000, D3). Bootstrap: 95% percentile interval, "
        f"{BOOTSTRAP_RESAMPLES:,} resamples per group, seed {SEED}.",
        *sections(tags, tag_dist, "tag", "tags", tag_strength, rng),
        *sections(pairs, pair_dist, "pair", "pairs", pair_strength, rng),
    ]
    (OUT_DIR / "summary.md").write_text("\n\n".join(summary) + "\n", encoding="utf-8")
    print(f"wrote {OUT_DIR / 'summary.md'}")


if __name__ == "__main__":
    main()

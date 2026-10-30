"""D1 EDA: how big are tags and tag pairs, and what does that mean for ranking their rates?

Runs the SQL in ./sql against BigQuery, caches each result as a CSV in ./output, then writes the plots and
output/summary.md. Each query is dry-run first, so the bytes it scans are printed before it runs.

    python eda/d1_sample_size/run_eda.py              # reuses cached CSVs when present
    python eda/d1_sample_size/run_eda.py --refresh    # requeries BigQuery
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from google.cloud import bigquery  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

PROJECT = "so-answerability"
HERE = Path(__file__).resolve().parent
SQL_DIR = HERE / "sql"
OUT_DIR = HERE / "output"

# Smallest pair kept by tag_pair_stats.sql; smaller pairs only appear in the size distribution.
MIN_PAIR_QUESTIONS = 30
# Cutoffs to compare. 385 / 1,068 / 2,401 questions are the smallest n with a 95% margin of error within
# ±5 / ±3 / ±2 pp at a 50% rate: n = (1.96 × 0.5 / margin)², rounded up.
CUTOFFS = [30, 100, 385, 500, 1068, 2401]
# D1 decision (specs/001): rank only groups with >= 385 questions.
RANKING_CUTOFF = 385
TOP_N = 10
Z95, Z998 = 1.96, 3.09

BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.bbox": "tight",
    "font.size": 10,
    "text.color": INK,
    "axes.titlesize": 11,
    "axes.titlelocation": "left",
    "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "legend.frameon": False,
})


# --- BigQuery ------------------------------------------------------------------------------------------------

def query(client, name, year, refresh, **int_params):
    """Run sql/<name>.sql with @year (and any extra INT64 params), caching the result as a CSV."""
    path = OUT_DIR / f"{name}_{year}.csv"
    if path.exists() and not refresh:
        # keep_default_na=False: "null", "nan" and "na" are real tags, not missing values.
        return pd.read_csv(path, keep_default_na=False)

    sql = (SQL_DIR / f"{name}.sql").read_text(encoding="utf-8")
    params = [bigquery.ScalarQueryParameter("year", "INT64", year)]
    params += [bigquery.ScalarQueryParameter(key, "INT64", value) for key, value in int_params.items()]

    dry_run = client.query(
        sql, job_config=bigquery.QueryJobConfig(query_parameters=params, dry_run=True, use_query_cache=False)
    )
    print(f"{name}: scans {dry_run.total_bytes_processed / 1e9:.2f} GB")

    job = client.query(sql, job_config=bigquery.QueryJobConfig(query_parameters=params))
    df = job.to_dataframe(create_bqstorage_client=False)
    df.to_csv(path, index=False)
    return df


# --- Statistics ----------------------------------------------------------------------------------------------

def size_freq(sizes):
    """Frequency table of group sizes: one row per n_questions value, with how many groups have that size."""
    return (
        sizes.value_counts()
        .rename_axis("n_questions")
        .reset_index(name="n_groups")
        .sort_values("n_questions", ignore_index=True)
    )


def describe(freq):
    """Distribution stats of group size, computed from a frequency table (so pairs never need one row each)."""
    n = freq["n_questions"].to_numpy(float)
    w = freq["n_groups"].to_numpy(float)
    mean = np.average(n, weights=w)
    std = np.sqrt(np.average((n - mean) ** 2, weights=w))
    log_n = np.log10(n)
    log_mean = np.average(log_n, weights=w)
    cum_share = np.cumsum(w) / w.sum()

    def quantile(q):
        return n[np.searchsorted(cum_share, q)]

    return {
        "groups": w.sum(),
        "mean": mean,
        "std": std,
        "mean - 3 sd": mean - 3 * std,
        "mean + 3 sd": mean + 3 * std,
        "median": quantile(0.5),
        "p75": quantile(0.75),
        "p90": quantile(0.9),
        "p99": quantile(0.99),
        "max": n.max(),
        "skewness": np.average(((n - mean) / std) ** 3, weights=w),
        "log10 mean": log_mean,
        "log10 sd": np.sqrt(np.average((log_n - log_mean) ** 2, weights=w)),
    }


def coverage(freq, cutoffs):
    """For each cutoff, how many groups survive and what share of question links they hold.

    A question link is one (question, group) membership: a question with tags a|b|c has 3 tag links and 3 pair
    links. Links, not questions, because a question counts in every group it belongs to.
    """
    n = freq["n_questions"].to_numpy(float)
    w = freq["n_groups"].to_numpy(float)
    rows = []
    for cutoff in cutoffs:
        kept = n >= cutoff
        rows.append({
            "min questions": cutoff,
            "groups kept": w[kept].sum(),
            "% groups kept": 100 * w[kept].sum() / w.sum(),
            "% question links kept": 100 * (n * w)[kept].sum() / (n * w).sum(),
        })
    return pd.DataFrame(rows)


def wilson_bounds(k, n, z=Z95):
    """Wilson score interval: the range we are ~95% sure the group's true rate is in.

    The lower bound ranks "highest" lists and the upper bound ranks "lowest" lists, so a group needs both an extreme
    rate and enough questions to land at either end.
    """
    p = k / n
    centre = p + z**2 / (2 * n)
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    denominator = 1 + z**2 / n
    return (centre - margin) / denominator, (centre + margin) / denominator


def shrink_to_pooled(k, n, min_n=30):
    """Empirical Bayes: pull each rate toward the pooled rate, more for small groups.

    The beta prior is fitted by method of moments on groups with n >= min_n. Returns the shrunk rates and the
    prior strength, i.e. how many "virtual questions at the pooled rate" every group starts with.
    """
    fit = n >= min_n
    p = k[fit] / n[fit]
    pooled = k[fit].sum() / n[fit].sum()
    sampling_var = np.mean(pooled * (1 - pooled) / n[fit])
    between_var = max(p.var() - sampling_var, 1e-6)
    strength = pooled * (1 - pooled) / between_var - 1
    return (k + strength * pooled) / (n + strength), strength


def add_rate_columns(df):
    df = df.copy()
    df["accepted_rate"] = df["n_accepted"] / df["n_questions"]
    df["wilson_lower"], df["wilson_upper"] = wilson_bounds(df["n_accepted"], df["n_questions"])
    df["shrunk_rate"], strength = shrink_to_pooled(df["n_accepted"], df["n_questions"])
    return df, strength


def outside_limits(df, pooled, z):
    """Share of groups whose accepted rate falls outside pooled ± z·SE, by size band (funnel-plot check)."""
    se = np.sqrt(pooled * (1 - pooled) / df["n_questions"])
    outside = (df["accepted_rate"] - pooled).abs() > z * se
    bands = pd.cut(df["n_questions"], [0, 30, 100, 500, 2000, np.inf], right=False,
                   labels=["1-29", "30-99", "100-499", "500-1,999", "2,000+"])
    return (
        pd.DataFrame({"size band": bands, "outside": outside})
        .groupby("size band", observed=True)
        .agg(groups=("outside", "size"), outside=("outside", "sum"))
        .assign(**{"% outside": lambda t: 100 * t["outside"] / t["groups"]})
        .reset_index()
    )


# --- Plots ---------------------------------------------------------------------------------------------------

def plot_size_histograms(freq, stats, label, path):
    n = freq["n_questions"].to_numpy(float)
    w = freq["n_groups"].to_numpy(float)
    fig, (linear, logged) = plt.subplots(1, 2, figsize=(11, 4))

    linear.hist(n, bins=60, weights=w, color=BLUE)
    linear.axvline(stats["mean"], color=ORANGE, linewidth=1.5, label=f"mean = {stats['mean']:,.0f}")
    linear.axvline(stats["mean + 3 sd"], color=ORANGE, linewidth=1.5, linestyle="--",
                   label=f"mean ± 3 sd = {stats['mean - 3 sd']:,.0f} … {stats['mean + 3 sd']:,.0f}")
    linear.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:,.0f}k" if value else "0"))
    linear.set_title(f"Questions per {label}, linear bins")
    linear.set_xlabel(f"questions per {label}")
    linear.set_ylabel(f"number of {label}s")
    linear.legend()

    bins = np.logspace(0, np.log10(n.max()) + 0.01, 40)
    logged.hist(n, bins=bins, weights=w, color=BLUE, label="observed")
    log_bin_width = np.log10(bins[1]) - np.log10(bins[0])
    grid = np.linspace(0, np.log10(n.max()), 200)
    normal = np.exp(-0.5 * ((grid - stats["log10 mean"]) / stats["log10 sd"]) ** 2)
    normal *= w.sum() * log_bin_width / (stats["log10 sd"] * np.sqrt(2 * np.pi))
    logged.plot(10**grid, normal, color=ORANGE, linewidth=2, label="normal fit on log10(n)")
    logged.set_xscale("log")
    logged.set_title(f"Questions per {label}, log bins")
    logged.set_xlabel(f"questions per {label} (log scale)")
    logged.legend()

    fig.savefig(path)
    plt.close(fig)


def plot_coverage(freq, label, path):
    n_max = freq["n_questions"].max()
    cutoffs = np.unique(np.logspace(0, np.log10(n_max), 200).astype(int))
    table = coverage(freq, cutoffs)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(table["min questions"], table["% groups kept"], color=BLUE, linewidth=2, label=f"% of {label}s kept")
    ax.plot(table["min questions"], table["% question links kept"], color=ORANGE, linewidth=2,
            label="% of question links kept")
    ax.set_xscale("log")
    ax.set_ylim(0, 100)
    ax.set_title(f"What a minimum-size cutoff keeps ({label}s)")
    ax.set_xlabel("minimum questions (log scale)")
    ax.set_ylabel("% kept")
    ax.legend()
    fig.savefig(path)
    plt.close(fig)


def plot_funnel(df, pooled, label, path):
    n_grid = np.logspace(np.log10(df["n_questions"].min()), np.log10(df["n_questions"].max()), 200)
    se = np.sqrt(pooled * (1 - pooled) / n_grid)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.scatter(df["n_questions"], df["accepted_rate"], s=8, color=BLUE, alpha=0.35, linewidths=0,
               label=f"one {label}")
    ax.axhline(pooled, color=INK, linewidth=1, label=f"pooled rate = {pooled:.1%}")
    for z, style, name in [(Z95, "--", "95% limits"), (Z998, "-", "99.8% limits")]:
        ax.plot(n_grid, np.clip(pooled + z * se, 0, 1), color=ORANGE, linewidth=1.5, linestyle=style, label=name)
        ax.plot(n_grid, np.clip(pooled - z * se, 0, 1), color=ORANGE, linewidth=1.5, linestyle=style)
    ax.set_xscale("log")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title(f"Accepted rate vs size, one dot per {label} (funnel plot)")
    ax.set_xlabel("questions (log scale)")
    ax.set_ylabel("accepted answers / questions")
    ax.legend(loc="upper right")
    fig.savefig(path)
    plt.close(fig)


def plot_margin_of_error(path):
    n = np.logspace(1, 5, 200)
    moe = 100 * Z95 * np.sqrt(0.25 / n)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(n, moe, color=BLUE, linewidth=2)
    for cutoff in [100, 385, 1068, 2401]:
        value = 100 * Z95 * np.sqrt(0.25 / cutoff)
        ax.scatter([cutoff], [value], s=40, color=ORANGE, zorder=3)
        ax.annotate(f"n = {cutoff:,}: ±{value:.1f} pp", (cutoff, value), xytext=(8, 4),
                    textcoords="offset points", color=INK)
    ax.set_xscale("log")
    ax.set_title("95% margin of error of a rate, worst case (rate = 50%)")
    ax.set_xlabel("questions in the group (log scale)")
    ax.set_ylabel("± percentage points")
    fig.savefig(path)
    plt.close(fig)


# --- Summary -------------------------------------------------------------------------------------------------

def fmt(value):
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


def ranking_table(df, by, ascending, name_col):
    cols = [name_col, "n_questions", "accepted_rate", "wilson_lower", "wilson_upper", "shrunk_rate"]
    return df.sort_values(by, ascending=ascending).head(TOP_N)[cols]


def d1_sections(df, name_col, label):
    """D1 rule (specs/001): floor, then Wilson lower bound for "highest" and upper bound for "lowest".

    Methods A (raw rate) and C (empirical Bayes) rank the same eligible groups as robustness checks; the overlap
    table counts how many of their top / bottom 10 match the Wilson lists.
    """
    eligible = df[df["n_questions"] >= RANKING_CUTOFF]

    def names(by, ascending):
        return set(eligible.sort_values(by, ascending=ascending).head(TOP_N)[name_col])

    top, bottom = names("wilson_lower", False), names("wilson_upper", True)
    overlap = pd.DataFrame([
        {"method": method, f"top-{TOP_N} overlap": len(top & names(col, False)),
         f"bottom-{TOP_N} overlap": len(bottom & names(col, True))}
        for method, col in [("A: raw rate", "accepted_rate"), ("C: empirical Bayes", "shrunk_rate")]
    ])
    return [
        f"## D1 rule — {label} with ≥ {RANKING_CUTOFF} questions ({len(eligible):,} {label})",
        f"### Highest: top {TOP_N} by Wilson lower bound",
        md_table(ranking_table(eligible, "wilson_lower", False, name_col)),
        f"### Lowest: bottom {TOP_N} by Wilson upper bound",
        md_table(ranking_table(eligible, "wilson_upper", True, name_col)),
        f"### Robustness: overlap of methods A and C with the Wilson lists (out of {TOP_N})",
        md_table(overlap),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--year", type=int, default=2022)
    parser.add_argument("--refresh", action="store_true", help="requery BigQuery instead of using cached CSVs")
    args = parser.parse_args()
    OUT_DIR.mkdir(exist_ok=True)

    client = bigquery.Client(project=PROJECT)
    tags = query(client, "tag_stats", args.year, args.refresh)
    pair_freq = query(client, "tag_pair_size_distribution", args.year, args.refresh)
    pairs = query(client, "tag_pair_stats", args.year, args.refresh, min_questions=MIN_PAIR_QUESTIONS)

    pair_freq = pair_freq.rename(columns={"n_pairs": "n_groups"})
    pairs["pair"] = pairs["tag_a"] + " + " + pairs["tag_b"]
    tag_freq = size_freq(tags["n_questions"])

    checks = pd.DataFrame([
        {"check": "empty or null tag", "rows": int(tags["tag"].isna().sum() + (tags["tag"] == "").sum())},
        {"check": "n_answered > n_questions", "rows": int((tags["n_answered"] > tags["n_questions"]).sum())},
        {"check": "n_accepted > n_answered (accepted answer but answer_count = 0)",
         "rows": int((tags["n_accepted"] > tags["n_answered"]).sum())},
    ])

    stats = {"tags": describe(tag_freq), "tag pairs": describe(pair_freq)}
    stats_table = pd.DataFrame(stats).reset_index(names="statistic")

    tags, tag_strength = add_rate_columns(tags)
    pairs, pair_strength = add_rate_columns(pairs)
    pooled_tag_rate = tags["n_accepted"].sum() / tags["n_questions"].sum()
    pooled_pair_rate = pairs["n_accepted"].sum() / pairs["n_questions"].sum()

    plot_size_histograms(tag_freq, stats["tags"], "tag", OUT_DIR / "01_tag_size_histograms.png")
    plot_size_histograms(pair_freq, stats["tag pairs"], "tag pair", OUT_DIR / "02_pair_size_histograms.png")
    plot_coverage(tag_freq, "tag", OUT_DIR / "03_tag_cutoff_coverage.png")
    plot_coverage(pair_freq, "tag pair", OUT_DIR / "04_pair_cutoff_coverage.png")
    plot_funnel(tags, pooled_tag_rate, "tag", OUT_DIR / "05_tag_funnel.png")
    plot_funnel(pairs, pooled_pair_rate, "tag pair", OUT_DIR / "06_pair_funnel.png")
    plot_margin_of_error(OUT_DIR / "07_margin_of_error.png")

    sections = [
        f"# D1 EDA — sample size per tag and tag pair ({args.year})",
        "Generated by `run_eda.py`; do not edit by hand. Accepted rate = accepted answers / all questions.",
        "## Data checks", md_table(checks),
        "## Size distribution (questions per group)", md_table(stats_table),
        "## What each cutoff keeps — tags", md_table(coverage(tag_freq, CUTOFFS)),
        "## What each cutoff keeps — tag pairs", md_table(coverage(pair_freq, CUTOFFS)),
        f"## Funnel check — tags (pooled accepted rate {pooled_tag_rate:.1%})",
        "If every tag had the same true rate, about 5% / 0.2% of tags would fall outside the 95% / 99.8% limits "
        "by chance. Far more than that means tags really differ, so a ranking has something to find.",
        "### Outside 95% limits", md_table(outside_limits(tags, pooled_tag_rate, Z95)),
        "### Outside 99.8% limits", md_table(outside_limits(tags, pooled_tag_rate, Z998)),
        f"## Funnel check — tag pairs with ≥ {MIN_PAIR_QUESTIONS} questions "
        f"(pooled accepted rate {pooled_pair_rate:.1%})",
        "### Outside 99.8% limits", md_table(outside_limits(pairs, pooled_pair_rate, Z998)),
        "## Why a floor: raw accepted rate with no floor",
        f"Empirical Bayes prior strength: tags start with {tag_strength:,.0f} virtual questions at the pooled rate; "
        f"pairs with {pair_strength:,.0f}.",
        f"### Top {TOP_N} tags by raw rate", md_table(ranking_table(tags, "accepted_rate", False, "tag")),
        f"### Bottom {TOP_N} tags by raw rate", md_table(ranking_table(tags, "accepted_rate", True, "tag")),
        *d1_sections(tags, "tag", "tags"),
        *d1_sections(pairs, "pair", "tag pairs"),
    ]
    (OUT_DIR / "summary.md").write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"Wrote plots and summary.md to {OUT_DIR}")


if __name__ == "__main__":
    main()

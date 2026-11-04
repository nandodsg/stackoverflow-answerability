"""Draws the EDA charts shown in the presentation's decision details (slides 4 and 5), in the page's colours.

Reads only cached CSVs, so it never queries BigQuery: the ones the EDA scripts wrote to eda/*/output (D5's is the
project's own BigQuery job log), plus the P3 effects mart already exported to presentation/data (D4's
original-vs-today's-text chart). Writes the SVGs to presentation/img/eda/. Run the EDA scripts first on a fresh clone
(each README says how).

    python presentation/eda_charts.py
"""

import logging
import math
from pathlib import Path

import matplotlib
import matplotlib.dates
import matplotlib.patches

matplotlib.use("Agg")
# Figtree is the page's font, not installed here: matplotlib measures with the fallback, the browser renders Figtree.
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EDA = ROOT / "eda"
OUT = Path(__file__).resolve().parent / "img" / "eda"

FLOOR, Z95, TOP_N, SEED = 385, 1.96, 10, 2022
# Page tokens (style.css): the chart sits on the dialog's panel, so its own background stays transparent.
TEXT, MUTED, HAIRLINE = "#fffce1", "#7c7c6f", "#42433d"
CANVAS, PANEL = "#0e100f", "#191919"
ENG, P1, P2, P3, PINK = "#00bae2", "#abff84", "#9d95ff", "#ff8709", "#fec5fb"
DARK_GREEN = "#2f9e44"  # D1 funnel's median line: a green apart from P1's, still readable on the dark panel
plt.rcParams.update({
    "svg.fonttype": "none",  # keep text as text, so the page font renders it
    "font.family": ["Figtree", "Segoe UI", "DejaVu Sans", "sans-serif"],
    "font.size": 11,
    "figure.facecolor": "none",
    "axes.facecolor": "none",
    "savefig.facecolor": "none",
    "savefig.bbox": "tight",
    "text.color": TEXT,
    "axes.titlesize": 12,
    "axes.titlelocation": "left",
    "axes.titlecolor": TEXT,
    "axes.edgecolor": HAIRLINE,
    "axes.labelcolor": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": HAIRLINE,
    "grid.linewidth": 0.5,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "legend.frameon": False,
    "legend.labelcolor": TEXT,
})


def read(path):
    # keep_default_na=False: "null", "nan" and "na" are real tags, not missing values.
    return pd.read_csv(path, keep_default_na=False)


def wilson_bounds(k, n, z=Z95):
    """Wilson score interval, 95% (same rule as the EDAs and macros/stats.sql)."""
    p = k / n
    centre = p + z**2 / (2 * n)
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return (centre - margin) / (1 + z**2 / n), (centre + margin) / (1 + z**2 / n)


def ranked_tags():
    """2022 tags at the D1 floor, with accepted rate (A), accepted among answered (B) and their Wilson bounds."""
    tags = read(EDA / "d1_sample_size" / "output" / "tag_stats_2022.csv")
    tags = tags[tags["n_questions"] >= FLOOR].copy()
    tags["rate_a"] = tags["n_accepted"] / tags["n_questions"]
    tags["rate_b"] = tags["n_accepted"] / tags["n_answered"]
    tags["a_lower"], tags["a_upper"] = wilson_bounds(tags["n_accepted"], tags["n_questions"])
    tags["b_lower"], tags["b_upper"] = wilson_bounds(tags["n_accepted"], tags["n_answered"])
    return tags


def d1_floor(path):
    """Left: funnel plot, each 2022 tag's accepted rate against its size. Right: the worst-case 95% margin by size."""
    tags = read(EDA / "d1_sample_size" / "output" / "tag_stats_2022.csv")
    n, rate = tags["n_questions"].astype(float), tags["n_accepted"] / tags["n_questions"]
    pooled = tags["n_accepted"].sum() / tags["n_questions"].sum()
    fig, (funnel, margin) = plt.subplots(1, 2, figsize=(10, 3.6))

    # 42K dots: rasterized, or the SVG weighs megabytes.
    funnel.scatter(n, 100 * rate, s=4, color=ENG, alpha=0.25, linewidths=0, rasterized=True)
    grid = np.logspace(0, np.log10(n.max()), 200)
    se = np.sqrt(pooled * (1 - pooled) / grid)
    funnel.axhline(100 * pooled, color=TEXT, linewidth=1, label=f"all tags pooled: {pooled:.1%}")
    for z, style, name in [(Z95, "--", "95% limits (±1.96 SE)"), (3.09, ":", "99.8% limits (±3.09 SE)")]:
        for sign in (-1, 1):
            funnel.plot(grid, 100 * np.clip(pooled + sign * z * se, 0, 1), color=P3, linewidth=1.5, linestyle=style,
                        label=name if sign == 1 else None)
    median = n.median()
    funnel.axvline(median, color=DARK_GREEN, linewidth=1.5, label=f"median tag: {median:,.0f} questions")
    funnel.axvline(FLOOR, color=PINK, linewidth=1, label=f"{FLOOR}-question floor")
    funnel.set_xscale("log")
    funnel.set_ylim(-2, 102)
    funnel.set_title("Accepted rate by tag size, 2022 tags")
    funnel.set_xlabel(f"questions per tag (log scale), floor at {FLOOR}")
    funnel.set_ylabel("accepted rate (%)")
    funnel.legend(loc="upper left", bbox_to_anchor=(0, -0.2), fontsize=9)  # below: the dots fill the panel

    sizes = np.logspace(0, 4, 200)
    margin.plot(sizes, 100 * Z95 * 0.5 / np.sqrt(sizes), color=ENG, linewidth=2)
    margin.axhline(5, color=MUTED, linewidth=1, linestyle="--")
    for size, label in [(6, "median tag"), (100, None), (FLOOR, "floor"), (1068, None)]:
        value = 100 * Z95 * 0.5 / math.sqrt(size)
        margin.scatter([size], [value], s=30, color=PINK if size == FLOOR else P3, zorder=3)
        text = f"{size:,}: ±{value:.1f} pt" + (f" ({label})" if label else "")
        # The 1,068 label goes under its dot, or it runs into the floor's label.
        offset = (6, -14) if size == 1068 else (8, 4)
        margin.annotate(text, (size, value), xytext=offset, textcoords="offset points", color=TEXT, fontsize=10)
    margin.set_xscale("log")
    margin.set_ylim(0, 45)
    margin.set_title("Worst-case 95% margin of an accepted rate")
    margin.set_xlabel("questions in the tag (log scale)")
    margin.set_ylabel("± points, at a 50% rate")
    fig.savefig(path)
    plt.close(fig)


def d1_sizes(path):
    """Share of tags and of question-tag links by tag size: half the tags are tiny, a few hold most questions."""
    tags = read(EDA / "d1_sample_size" / "output" / "tag_stats_2022.csv")
    edges = [1, 7, 30, 100, 500, 2000, math.inf]
    names = ["1–6", "7–29", "30–99", "100–499", "500–1,999", "2,000+"]
    bins = pd.cut(tags["n_questions"], edges, right=False, labels=names)
    groups = tags.groupby(bins, observed=False)["n_questions"].agg(["size", "sum"])
    rows = [("share of tags", groups["size"] / groups["size"].sum()),
            ("share of question–tag links", groups["sum"] / groups["sum"].sum())]
    # Sequential: one hue (ENG), from mixed into the dialog panel for small tags to lifted toward the text for the
    # biggest, so the six steps stay apart on a dark background.
    panel, eng, text = (np.array(matplotlib.colors.to_rgb(c)) for c in (PANEL, ENG, TEXT))
    shades = [panel + w * (eng - panel) for w in np.linspace(0.2, 1, len(names) - 1)] + [eng + 0.45 * (text - eng)]

    fig, ax = plt.subplots(figsize=(10, 1.9))
    for y, (row, shares) in enumerate(rows):
        left = 0.0
        for name, share, shade in zip(names, shares, shades):
            # The panel-coloured edge is the 2px gap between segments.
            ax.barh(y, 100 * share, left=100 * left, height=0.62, color=shade, edgecolor=PANEL, linewidth=2)
            if share >= 0.05:  # label only segments wide enough to hold it
                ink = CANVAS if shade.mean() > 0.45 else TEXT
                ax.text(100 * (left + share / 2), y, f"{share:.1%}", ha="center", va="center", color=ink,
                        fontsize=10)
            left += share
    ax.set_yticks(range(len(rows)), [row for row, _ in rows])
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of 2022 total")
    ax.grid(False)
    ax.tick_params(axis="y", length=0, labelcolor=TEXT)
    ax.spines["left"].set_visible(False)
    ax.set_title("Tag size, 2022: half the tags are tiny, a few hold most questions")
    # Own swatches: the bars' 2px panel edge would shrink the legend's to a dash.
    swatches = [matplotlib.patches.Patch(color=shade, label=f"{name} questions") for name, shade in zip(names, shades)]
    ax.legend(handles=swatches, loc="upper left", bbox_to_anchor=(0, -0.42), ncol=len(names), fontsize=9,
              handlelength=1.2, handleheight=1.2)
    fig.savefig(path)
    plt.close(fig)


def d2_denominator(path):
    """Each ranked tag by A (accepted / all questions) and B (accepted / answered); the two bottom 10 lists marked."""
    tags = ranked_tags()
    bottom_a = set(tags.nsmallest(TOP_N, "a_upper")["tag"])
    bottom_b = set(tags.nsmallest(TOP_N, "b_upper")["tag"])
    top_a, top_b = set(tags.nlargest(TOP_N, "a_lower")["tag"]), set(tags.nlargest(TOP_N, "b_lower")["tag"])
    assert len(top_a & top_b) == 8 and len(bottom_a & bottom_b) == 5, "lists differ from eda/d2_denominator"

    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.scatter(100 * tags["rate_a"], 100 * tags["rate_b"], s=7, color=HAIRLINE, linewidths=0, label="ranked tag")
    for names, colour, label in [
        (bottom_a - bottom_b, P3, "bottom 10 by A only"),
        (bottom_b - bottom_a, P2, "bottom 10 by B only"),
        (bottom_a & bottom_b, PINK, "bottom 10 by both"),
    ]:
        rows = tags[tags["tag"].isin(names)]
        ax.scatter(100 * rows["rate_a"], 100 * rows["rate_b"], s=28, color=colour, linewidths=0, label=label)
    magento = tags[tags["tag"] == "magento2"].iloc[0]
    ax.annotate("magento2: 41% answered, 9% accepted", (100 * magento["rate_a"], 100 * magento["rate_b"]),
                xytext=(150, -2), textcoords="offset points", color=TEXT, fontsize=10, va="center",
                arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.8})
    ax.set_title(f"2022 tags with ≥ {FLOOR} questions: two ways to count accepted")
    ax.set_xlabel("A: accepted / all questions (%)")
    ax.set_ylabel("B: accepted / answered (%)")
    ax.legend(loc="lower right", fontsize=9)
    fig.savefig(path)
    plt.close(fig)


def d3_ratio(path):
    """python-only, both orientations of the ratio by year, with the 2021 -> 2022 change of each."""
    years = read(EDA / "d3_ratio" / "output" / "answers_by_year.csv")
    py = years[years["tag"] == "python"].sort_values("creation_year")
    apq = py["n_answers"] / py["n_questions"]
    qpa = py["n_questions"] / py["n_answers"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), sharex=True)
    for ax, values, colour, title in [(axes[0], apq, P2, "Answers per question"),
                                      (axes[1], qpa, PINK, "Questions per answer (Q÷A)")]:
        ax.plot(py["creation_year"], values, color=colour, linewidth=2, marker="o", markersize=4)
        change = values.iloc[-1] / values.iloc[-2] - 1
        ax.annotate(f"2021 → 2022: {change:+.0%}", (py["creation_year"].iloc[-1], values.iloc[-1]),
                    xytext=(-118, 0 if change < 0 else -14), textcoords="offset points", color=TEXT, fontsize=10)
        ax.set_title(f"{title}, python-only")
        ax.set_xticks(py["creation_year"][::3])
    axes[0].set_ylabel("ratio")
    fig.savefig(path)
    plt.close(fig)


def d4_edits(path):
    """All 2022 questions. Left: what gets edited, and whether the first edit came after the first answer.
    Right: edited vs never-edited questions, answer and accepted rates (why a never-edited filter is biased)."""
    profile = read(EDA / "d4_edits" / "output" / "edit_profile.csv")
    row = profile[(profile["segment"] == "all") & (profile["creation_year"] == 2022)].iloc[0]
    n = row["n_questions"]
    fig, (bars, rates) = plt.subplots(1, 2, figsize=(10, 2.9), gridspec_kw={"width_ratios": [3, 2]})

    parts = [("first edited after the first answer", P3), ("first edited earlier, or never answered", ENG),
             ("never edited", HAIRLINE)]
    for y, kind in [(0, "tag"), (1, "text")]:
        after = row[f"n_{kind}_edit_after_first_answer"] / n
        other = row[f"n_{kind}_edit"] / n - after
        left = 0.0
        for (name, colour), share in zip(parts, [after, other, 1 - after - other]):
            bars.barh(y, 100 * share, left=100 * left, height=0.5, color=colour, edgecolor=PANEL, linewidth=2,
                      label=name if y == 0 else None)
            centre = 100 * (left + share / 2)
            if share >= 0.08:
                bars.text(centre, y, f"{share:.1%}", ha="center", va="center", fontsize=10,
                          color=CANVAS if colour in (P3, ENG) else TEXT)
            else:  # too narrow to hold its label: write it just above the segment
                bars.text(centre, y - 0.3, f"{share:.1%}", ha="center", va="bottom", fontsize=10, color=TEXT)
            left += share
    bars.set_yticks([0, 1], ["tags", "title or body"])
    bars.set_xlim(0, 100)
    bars.grid(False)
    bars.tick_params(axis="y", length=0, labelcolor=TEXT)
    bars.spines["left"].set_visible(False)
    bars.set_xlabel("% of 2022 questions")
    bars.set_title("What gets edited, and when")
    bars.set_ylim(1.5, -0.75)  # room above the tags bar for its outside labels (y axis inverted)
    bars.legend(loc="upper left", bbox_to_anchor=(0, -0.3), ncol=3, fontsize=9, handlelength=1.2, handleheight=1.2)

    edited = n - row["n_never_edited"]
    groups = [("answer rate", (row["n_answered"] - row["n_answered_never_edited"]) / edited,
               row["n_answered_never_edited"] / row["n_never_edited"]),
              ("accepted rate", (row["n_accepted"] - row["n_accepted_never_edited"]) / edited,
               row["n_accepted_never_edited"] / row["n_never_edited"])]
    x = np.arange(len(groups))
    for offset, index, colour, name in [(-0.18, 1, ENG, "edited"), (0.18, 2, MUTED, "never edited")]:
        values = [100 * group[index] for group in groups]
        rates.bar(x + offset, values, width=0.34, color=colour, label=name)
        for xi, value in zip(x + offset, values):
            rates.text(xi, value + 1.5, f"{value:.1f}%", ha="center", fontsize=10, color=TEXT)
    rates.set_xticks(x, [group[0] for group in groups])
    rates.tick_params(axis="x", length=0, labelcolor=TEXT)
    rates.set_ylim(0, 80)
    rates.set_ylabel("% of the group's questions")
    rates.set_title("Edited questions do better")
    rates.legend(loc="upper right", fontsize=9)
    fig.savefig(path)
    plt.close(fig)


def d4_leakage(path):
    """Each ranked tag by accepted rate and tag exposure (tags first edited after the first answer)."""
    tags = ranked_tags().merge(read(EDA / "d4_edits" / "output" / "leakage_by_tag.csv")[["tag", "n_tag_exposed"]],
                               on="tag")
    tags["exposure"] = tags["n_tag_exposed"] / tags["n_questions"]
    rho = tags["rate_a"].rank().corr(tags["exposure"].rank())
    top, bottom = tags.nlargest(TOP_N, "a_lower"), tags.nsmallest(TOP_N, "a_upper")

    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.scatter(100 * tags["rate_a"], 100 * tags["exposure"], s=7, color=HAIRLINE, linewidths=0, label="ranked tag")
    ax.scatter(100 * top["rate_a"], 100 * top["exposure"], s=28, color=P1, linewidths=0, label="top 10")
    ax.scatter(100 * bottom["rate_a"], 100 * bottom["exposure"], s=28, color=P3, linewidths=0, label="bottom 10")
    ax.axhline(10, color=MUTED, linewidth=1, linestyle="--")
    for name, offset in [("webdriverwait", (8, -4)), ("jq", (8, 4))]:
        tag = tags[tags["tag"] == name].iloc[0]
        if name == "webdriverwait":  # not in a top / bottom 10: drawn again so the labelled dot stands out
            ax.scatter([100 * tag["rate_a"]], [100 * tag["exposure"]], s=28, color=TEXT, linewidths=0, zorder=3)
        ax.annotate(f"{name}: {tag['exposure']:.0%}", (100 * tag["rate_a"], 100 * tag["exposure"]), xytext=offset,
                    textcoords="offset points", color=TEXT, fontsize=10)
    ax.set_yscale("log")
    ax.set_yticks([0.3, 1, 3, 10, 30, 60])
    ax.set_yticklabels(["0.3%", "1%", "3%", "10%", "30%", "60%"])
    ax.set_title(f"2022 tags with ≥ {FLOOR} questions: tag exposure rises with accepted rate "
                 f"(rank correlation {rho:.2f})")
    ax.set_xlabel("accepted rate (%)")
    ax.set_ylabel("tag exposure (log scale)")
    ax.legend(loc="lower right", fontsize=9)
    fig.savefig(path)
    plt.close(fig)


def d4_p3_versions(path):
    """P3, 2018-2021: each text feature's accepted-rate effect on the text as first posted vs today's text."""
    effects = pd.read_csv(ROOT / "presentation" / "data" / "mart_p3_feature_effects.csv", comment="#",
                          keep_default_na=False)
    effects = effects[(effects["cohort"] == "2018-2021") & effects["version"].isin(["original", "current"])]
    wide = effects.pivot_table(index=["feature", "bucket"], columns="version", values="accepted_rate_effect")
    # Features not read from the text (asker, posting time) are identical in both versions by construction.
    wide = wide[(wide["original"] - wide["current"]).abs() > 1e-9].sort_values("original")
    labels = [f"{feature.replace('_', ' ')}: {bucket.split(': ', 1)[1]}" for feature, bucket in wide.index]
    y = np.arange(len(wide))

    fig, ax = plt.subplots(figsize=(10, 0.27 * len(wide) + 1.2))
    ax.hlines(y, 100 * wide["original"], 100 * wide["current"], color=MUTED, linewidth=1.5)
    ax.scatter(100 * wide["original"], y, s=30, color=P3, zorder=3, label="text as first posted (the headline)")
    ax.scatter(100 * wide["current"], y, s=30, color=TEXT, zorder=3, label="today's text")
    ax.axvline(0, color=MUTED, linewidth=1)
    ax.set_yticks(y, labels, fontsize=9)
    ax.tick_params(axis="y", length=0, labelcolor=TEXT)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("accepted-rate effect against the reference bucket (points)")
    ax.set_title("P3, 2018–2021: each text feature's effect barely moves between the original and today's text")
    ax.legend(loc="lower right", fontsize=9)
    fig.savefig(path)
    plt.close(fig)


def d5_budget(path):
    """Every BigQuery query job of the project. Left: GiB billed so far in each month against the free sandbox's
    1 TB a month. Right: what the GiB went to."""
    jobs = read(EDA / "d5_budget" / "output" / "jobs.csv")
    jobs["time"] = pd.to_datetime(jobs["creation_time"], utc=True, format="ISO8601")
    jobs["gib"] = jobs["bytes_billed"].astype(float) / 1024**3
    jobs = jobs.sort_values("time")
    jobs["month"] = jobs["time"].dt.strftime("%Y-%m")
    jobs["running"] = jobs.groupby("month")["gib"].cumsum()
    text_node = jobs["dbt_node"].str.contains("int_post_history_scan|int_question_body_scan")
    full = text_node & (jobs["dbt_target"] == "full_scan")
    kinds = [
        ("post_history.text, full reads", jobs.loc[full & jobs["dbt_node"].str.contains("post_history"), "gib"]),
        ("posts_questions.body, full read", jobs.loc[full & jobs["dbt_node"].str.contains("body"), "gib"]),
        ("2% samples of both", jobs.loc[text_node & ~full, "gib"]),
        ("rest of dbt (dev target)", jobs.loc[~text_node & (jobs["from_dbt"].astype(str) == "True"), "gib"]),
        ("EDA, exports and checks", jobs.loc[jobs["from_dbt"].astype(str) != "True", "gib"]),
    ]
    fig, (line, bars) = plt.subplots(1, 2, figsize=(10, 3.4), gridspec_kw={"width_ratios": [3, 2], "wspace": 0.75})

    for month, group in jobs.groupby("month"):
        start = group["time"].min().floor("D") if month != "2026-11" else pd.Timestamp("2026-11-01", tz="UTC")
        times = [start] + list(group["time"])
        line.step(times, [0] + list(group["running"]), where="post", color=TEXT, linewidth=1.8)
        end = group["running"].iloc[-1]
        name = group["time"].iloc[0].strftime("%B")
        line.annotate(f"{name}: {end:,.0f} GiB ({end / 1024:.0%})", (group["time"].iloc[-1], end), xytext=(6, 4),
                      textcoords="offset points", color=TEXT, fontsize=10)
    line.axhline(1024, color=MUTED, linewidth=1, linestyle="--")
    line.text(jobs["time"].min(), 1024, "free quota: 1 TB a month", va="bottom", color=MUTED, fontsize=10)
    reads = jobs[full]  # three full reads within 12 minutes on Oct 31: one label for the jump
    line.annotate("Oct 31: the text reads\n106 + 35 + 106 GiB", (reads["time"].iloc[0], reads["running"].iloc[1]),
                  xytext=(-8, 0), textcoords="offset points", ha="right", va="center", color=TEXT, fontsize=9)
    line.set_ylim(0, 1150)
    # Room on the right for the month labels, so they stay inside this panel; ticks only on the days with jobs.
    line.set_xlim(pd.Timestamp("2026-10-29", tz="UTC"), pd.Timestamp("2026-11-03 06:00", tz="UTC"))
    line.set_xticks(pd.date_range("2026-10-29", "2026-11-01", freq="D", tz="UTC"))
    line.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %d"))
    line.set_ylabel("GiB billed so far this month")
    line.set_title("Billed against the free monthly quota")

    y = np.arange(len(kinds))
    values = [series.sum() for _, series in kinds]
    bars.barh(y, values, height=0.6, color=[TEXT, TEXT, PINK, ENG, MUTED])
    for yi, (name, series), value in zip(y, kinds, values):
        jobs_word = "job" if len(series) == 1 else "jobs"
        bars.text(value + 6, yi, f"{value:,.0f} GiB · {len(series)} {jobs_word}", va="center", fontsize=10,
                  color=TEXT)
    bars.set_yticks(y, [name for name, _ in kinds], fontsize=9)
    bars.tick_params(axis="y", length=0, labelcolor=TEXT)
    bars.invert_yaxis()
    bars.set_xlim(0, 330)
    bars.grid(axis="y", visible=False)
    bars.set_xlabel("GiB billed")
    bars.set_title(f"What the {jobs['gib'].sum():,.0f} GiB went to")
    fig.savefig(path)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d1_floor(OUT / "d1-floor.svg")
    d1_sizes(OUT / "d1-sizes.svg")
    d2_denominator(OUT / "d2-denominator.svg")
    d3_ratio(OUT / "d3-ratio.svg")
    d4_edits(OUT / "d4-edits.svg")
    d4_leakage(OUT / "d4-leakage.svg")
    d4_p3_versions(OUT / "d4-p3-versions.svg")
    d5_budget(OUT / "d5-budget.svg")
    print(f"Wrote eight SVGs to {OUT}")


if __name__ == "__main__":
    main()

"""Draws the four EDA charts shown in the presentation's decision details (chapter 4), in the page's colours.

Reads only the CSVs the EDA scripts cached in eda/*/output, so it never queries BigQuery. Writes one SVG per decision
to presentation/img/eda/. Run the EDA scripts first on a fresh clone (each README says how).

    python presentation/eda_charts.py
"""

import logging
import math
from pathlib import Path

import matplotlib
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
    ax.set_yscale("log")
    ax.set_yticks([0.3, 1, 3, 10, 30, 60])
    ax.set_yticklabels(["0.3%", "1%", "3%", "10%", "30%", "60%"])
    ax.set_title(f"2022 tags with ≥ {FLOOR} questions: leakage rises with accepted rate (rank correlation {rho:.2f})")
    ax.set_xlabel("accepted / all questions (%)")
    ax.set_ylabel("tags edited after the first answer")
    ax.legend(loc="lower right", fontsize=9)
    fig.savefig(path)
    plt.close(fig)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d1_floor(OUT / "d1-floor.svg")
    d1_sizes(OUT / "d1-sizes.svg")
    d2_denominator(OUT / "d2-denominator.svg")
    d3_ratio(OUT / "d3-ratio.svg")
    d4_leakage(OUT / "d4-leakage.svg")
    print(f"Wrote five SVGs to {OUT}")


if __name__ == "__main__":
    main()

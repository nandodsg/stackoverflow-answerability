"""D1 EDA, follow-up: how precise is a tag's accepted rate at the floor, what does the confidence level change, how
are tag sizes spread, and which tags does the floor leave out?

Reads the cached output/tag_stats_2022.csv written by run_eda.py, so it never queries BigQuery. Writes
output/09_rate_sampling_distribution.png and output/floor_precision.md.

    python eda/d1_sample_size/run_eda.py         # once, to cache the CSV
    python eda/d1_sample_size/floor_precision.py

Each question gets an accepted answer or doesn't, like a coin flip weighted by the tag's true accepted rate, so a
tag's accepted rate is the share of heads in n flips. Measured again, it would land around the true accepted rate,
with a spread of SE = sqrt(p(1 - p) / n), the standard error: within +-1.96 SE 95% of the time, +-2.58 SE 99%, +-3 SE
99.73%. The floor is the smallest n whose worst-case margin meets the target.
"""

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from run_eda import BLUE, MUTED, ORANGE, OUT_DIR, RANKING_CUTOFF, TOP_N, Z95, md_table, wilson_bounds

YEAR = 2022
SEED = 2022
SIMULATIONS = 100_000
# Confidence levels a floor could be built on, with their z (how many standard errors wide the interval is).
LEVELS = [("90%", 1.645), ("95%", Z95), ("99%", 2.576), ("99.73%", 3.0)]
MARGIN = 0.05  # the precision target decided in D1: +-5 points in the worst case (accepted rate = 50%)
# Tag-size bins, the same ones the presentation's D1 chart and the funnel findings use.
SIZE_EDGES = [1, 7, 30, 100, 500, 2000, math.inf]
SIZE_NAMES = ["1–6", "7–29", "30–99", "100–499", "500–1,999", "2,000+"]


def simulate_rates(n, p, rng):
    """Accepted rates of SIMULATIONS imaginary tags with n questions and a true accepted rate p."""
    return rng.binomial(n, p, SIMULATIONS) / n


def sampling_check(rng, pooled):
    rows = []
    for p, label in [(0.5, "50% (worst case)"), (pooled, f"{pooled:.1%} (2022 pooled)")]:
        rates = simulate_rates(RANKING_CUTOFF, p, rng)
        se = math.sqrt(p * (1 - p) / RANKING_CUTOFF)
        row = {"true accepted rate": label, "sd of the simulated rates": f"{100 * rates.std():.2f} pt",
               "standard error formula": f"{100 * se:.2f} pt"}
        for name, z in LEVELS[1:]:
            row[f"within ±{z:g} SE (expect {name})"] = f"{100 * (np.abs(rates - p) <= z * se).mean():.2f}%"
        rows.append(row)
    return rows


def floors_by_level(tags):
    """The floor each confidence level gives for the same +-5 point target, and what it does to the D1 lists."""
    def lists(floor, z):
        eligible = tags[tags["n_questions"] >= floor].copy()
        eligible["lower"], eligible["upper"] = wilson_bounds(eligible["n_accepted"], eligible["n_questions"], z)
        top = set(eligible.sort_values("lower", ascending=False).head(TOP_N)["tag"])
        bottom = set(eligible.sort_values("upper").head(TOP_N)["tag"])
        return len(eligible), top, bottom

    _, top_95, bottom_95 = lists(RANKING_CUTOFF, Z95)

    def row(name, z, floor):
        kept, top, bottom = lists(floor, z)
        return {
            "confidence": name,
            "z (standard errors)": f"{z:g}",
            "floor": f"{floor:,}",
            "tags ranked": f"{kept:,}",
            f"top {TOP_N} shared with 95% / {RANKING_CUTOFF}": f"{len(top & top_95)} of {TOP_N}",
            f"bottom {TOP_N} shared with 95% / {RANKING_CUTOFF}": f"{len(bottom & bottom_95)} of {TOP_N}",
        }

    both = [row(name, z, math.ceil((z * 0.5 / MARGIN) ** 2)) for name, z in LEVELS]
    # Split the two moves: a wider interval at the same floor, and the same interval with a higher floor.
    z_only = [row(name, z, RANKING_CUTOFF) for name, z in LEVELS[2:]]
    floor_only = [row("95%", Z95, math.ceil((z * 0.5 / MARGIN) ** 2)) for _, z in LEVELS[2:]]
    return both, z_only + floor_only


def bottom_sizes(tags):
    """How many of the decided bottom 10 sit below each higher floor (low-rate tags tend to be small)."""
    eligible = tags[tags["n_questions"] >= RANKING_CUTOFF].copy()
    _, eligible["upper"] = wilson_bounds(eligible["n_accepted"], eligible["n_questions"])
    bottom = eligible.sort_values("upper").head(TOP_N)
    top = eligible.assign(lower=wilson_bounds(eligible["n_accepted"], eligible["n_questions"])[0])
    top = top.sort_values("lower", ascending=False).head(TOP_N)
    return [{
        "list": name,
        "median questions": f"{df['n_questions'].median():,.0f}",
        "under 664": f"{(df['n_questions'] < 664).sum()} of {TOP_N}",
        "under 900": f"{(df['n_questions'] < 900).sum()} of {TOP_N}",
    } for name, df in [(f"top {TOP_N}", top), (f"bottom {TOP_N}", bottom)]]


def size_spread(tags):
    """Share of tags and of question-tag links by tag size: half the tags are tiny, a few hold most questions."""
    bins = pd.cut(tags["n_questions"], SIZE_EDGES, right=False, labels=SIZE_NAMES)
    groups = tags.groupby(bins, observed=False)["n_questions"].agg(["size", "sum"])
    return [{
        "questions per tag": name,
        "tags": f"{row['size']:,}",
        "share of tags": f"{row['size'] / groups['size'].sum():.1%}",
        "question-tag links": f"{row['sum']:,}",
        "share of links": f"{row['sum'] / groups['sum'].sum():.1%}",
    } for name, row in groups.iterrows()]


def left_out(tags):
    """Tags under the floor (but with 100+ questions) whose accepted rate beats every ranked tag's."""
    rate = tags["n_accepted"] / tags["n_questions"]
    best_ranked = rate[tags["n_questions"] >= RANKING_CUTOFF].max()
    under = tags[(tags["n_questions"] >= 100) & (tags["n_questions"] < RANKING_CUTOFF) & (rate > best_ranked)]
    under = under.assign(rate=rate).sort_values("rate", ascending=False)
    rows = [{"tag": r.tag, "questions": f"{r.n_questions:,}", "accepted rate": f"{r.rate:.1%}"}
            for r in under.itertuples()]
    return best_ranked, rows


def plot_sampling(rng, path):
    """Simulated accepted rate of one tag with 385 questions and a true rate of 50%: 95% within ±1.96 SE."""
    p = 0.5
    rates = simulate_rates(RANKING_CUTOFF, p, rng)
    se = math.sqrt(p * (1 - p) / RANKING_CUTOFF)
    fig, ax = plt.subplots(figsize=(8, 4))
    # One bin per possible rate (k / 385), so no bin holds two values and none is empty.
    edges = 100 * (np.arange(RANKING_CUTOFF + 2) - 0.5) / RANKING_CUTOFF
    ax.hist(100 * rates, bins=edges[(edges > 39) & (edges < 61)], color=BLUE)
    ax.set_xlim(40, 60)
    for z, style, name in [(Z95, "--", "±1.96 SE: 95%"), (3.0, ":", "±3 SE: 99.73%")]:
        for sign in (-1, 1):
            ax.axvline(100 * (p + sign * z * se), color=ORANGE, linewidth=1.5, linestyle=style,
                       label=name if sign == 1 else None)
    ax.set_title(f"Accepted rate of one tag with {RANKING_CUTOFF} questions, simulated {SIMULATIONS:,} times "
                 "(true accepted rate 50%)")
    ax.set_xlabel("measured accepted rate (%)")
    ax.set_ylabel("simulations")
    ax.legend(loc="upper right")
    ax.text(0.01, 0.95, f"SE = √(0.5 × 0.5 / {RANKING_CUTOFF}) = {100 * se:.2f} pt", transform=ax.transAxes,
            color=MUTED, va="top")
    fig.savefig(path)
    plt.close(fig)


def main():
    tags = pd.read_csv(OUT_DIR / f"tag_stats_{YEAR}.csv", keep_default_na=False)
    pooled = tags["n_accepted"].sum() / tags["n_questions"].sum()
    rng = np.random.default_rng(SEED)

    plot_sampling(rng, OUT_DIR / "09_rate_sampling_distribution.png")

    floors_both, floors_split = floors_by_level(tags)
    best_ranked, left_rows = left_out(tags)
    sections = [
        f"# D1 follow-up — how precise is a tag's accepted rate at the floor? ({YEAR})",
        "Generated by `floor_precision.py` from the cached `tag_stats_2022.csv`; do not edit by hand. "
        f"{len(tags):,} tags. Simulations: {SIMULATIONS:,} runs, seed {SEED}.",
        f"## 1. The measured accepted rate of one tag ({RANKING_CUTOFF} questions), simulated again and again",
        md_table(pd.DataFrame(sampling_check(rng, pooled))),
        f"## 2. The floor each confidence level gives, for the same ±{100 * MARGIN:.0f}-point target",
        "Each level ranks with its own Wilson z; overlap counts tags shared with the decided lists "
        f"(95%, ≥ {RANKING_CUTOFF}).",
        "Floor = (z × 0.5 / 0.05)², rounded up.",
        md_table(pd.DataFrame(floors_both)),
        "## 3. Which move changes the lists: the wider interval or the higher floor?",
        f"First rows: the {RANKING_CUTOFF} floor kept, only z changes. Last rows: z kept at 1.96, only the floor "
        "changes.",
        md_table(pd.DataFrame(floors_split)),
        md_table(pd.DataFrame(bottom_sizes(tags))),
        "## 4. How tag sizes are spread",
        "A question-tag link is one question counted under one of its tags: a question with 3 tags makes 3 links.",
        md_table(pd.DataFrame(size_spread(tags))),
        f"## 5. Who the floor leaves out: tags with 100 to {RANKING_CUTOFF - 1} questions above every ranked tag",
        f"The best ranked tag (≥ {RANKING_CUTOFF} questions) has an accepted rate of {best_ranked:.1%}. These tags beat "
        "it but are not ranked, because the floor is about how precisely an accepted rate is measured, not how high "
        "it is.",
        md_table(pd.DataFrame(left_rows)),
    ]
    (OUT_DIR / "floor_precision.md").write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"Wrote 09_rate_sampling_distribution.png and floor_precision.md to {OUT_DIR}")


if __name__ == "__main__":
    main()

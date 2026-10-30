# 001 — Tag answerability (prompt 1)

Status: **draft** — ranking rules (D1) and accepted-rate denominator (D2) decided

> What tags on a Stack Overflow question lead to the most answers and the highest rate of approved answers for the
> current year? What tags lead to the least? How about combinations of tags?

## Population

- **"Current year" = 2022**, the latest year in the snapshot (2022-01-01 → 2022-09-25). The README states this up front.
- Robustness check: the same ranking on full-year 2021. A tag whose rank flips between the two is flagged.

## Metrics

- **Most answers**: answers per question (primary) — total answers is mostly a volume effect, shown for context only.
- **Approved answers**: accepted rate out of all questions (see `000`, D2). Answer rate and accepted rate among
  answered are shown as columns beside it, so each row reads as "few people answer" or "askers rarely accept". 2022
  EDA ([`eda/d2_denominator`](../eda/d2_denominator/README.md)): the lowest tags by accepted rate are mostly rarely
  answered (magento2: 41% answered × 21% accepted among answered = 9%), while some tags are answered about half the
  time but rarely accepted (installation, salesforce).
- Censoring: 2022 questions created after ~2022-08-25 had < 30 days to collect answers. Report the plain metric and a
  30-day-window version on the cohort that had the full window.

## Grain

- Single tags: one row per tag (a question with 3 tags counts once for each).
- Combinations: one row per unordered **tag pair**. Exact full tag sets as a secondary view (open).

## Ranking rules (D1, decided 2026-10-29)

Evidence: [`eda/d1_sample_size`](../eda/d1_sample_size/README.md). Unfiltered, the top and bottom 10 tags by raw
accepted rate all have 1–2 questions (rates of exactly 100% and 0%).

- **Floor: ≥ 385 questions** in the year, for tags and for pairs alike. It comes from a precision target, not from the
  size distribution: 385 is the smallest n whose worst-case (p = 50%) 95% margin of error is within ±5 points,
  n = (1.96 × 0.5 / 0.05)² = 384.2 → 385. The size distribution is far from normal (2022 tags: median 6, mean 90,
  sd 1,543, so mean − 3 sd is negative), which rules out a mean ± k·sd cutoff.
  - Cost in 2022: 1,162 tags (2.7% of tags, 76% of question–tag links); 1,026 pairs (27% of pair links).
  - Because the floor is a precision rule, it stays the same in other years (e.g. the 2021 robustness check).
- **Score: Wilson score interval, 95%.**
  - "Highest" lists sort by the **lower** bound, descending: a tag ranks high only if its rate is high *and* well
    measured.
  - "Lowest" lists sort by the **upper** bound, ascending: a tag ranks low only if its rate is low and well measured.
  - Every row shows n, the raw rate and both bounds; the bound is the sort key, not the reported rate.
  - Applies to answer rate and accepted rate, each with its n = questions. Accepted rate among answered is shown, not
    ranked. Answers per question is a mean, not a proportion, so Wilson does not
    apply: its interval is mean ± 1.96 × SE (decided with D3, see `000`). Ranking: same floor, sorted by the lower
    bound (highest) / upper bound (lowest). *Ranking part proposed, to confirm.*
- **Robustness checks** (reported in one line each; a disagreement is listed, not hidden):
  - Method A — raw rate with the same floor.
  - Method C — empirical-Bayes rate, `(k + m·p₀) / (n + m)`, with m fitted by method of moments on tags with ≥ 30
    questions (2022 EDA: m ≈ 18 for tags, 15 for pairs).
  - Report the overlap of each top / bottom 10 with the Wilson list. 2022 EDA (accepted rate): tags 9–10 of 10 for
    both methods; pairs 9–10 of 10 at the top, 8 of 10 at the bottom.
- Report top and bottom 10 for each metric.

## Open questions

- Does "lead to" invite any causal language? Plan: no — describe association, note confounders (tag popularity, age).
- Pairs only, or also triples / exact sets?

## Acceptance criteria

- AC-1.1 Population limited to questions created in 2022; the cutoff date is printed with the result.
- AC-1.2 Every ranked tag/pair has ≥ 385 questions in the population year.
- AC-1.3 Rates are between 0 and 1; n is shown next to each rate.
- AC-1.4 2021 robustness ranking produced; rank changes in the top/bottom N are listed.
- AC-1.5 Wilson bounds match reference values (unit test): 9/10 → 0.596 / 0.982, 850/1,000 → 0.827 / 0.871,
  1/1 → 0.207 / 1.000, 0/1 → 0.000 / 0.793.
- AC-1.6 "Highest" lists sort by the Wilson lower bound and "lowest" lists by the upper bound.
- AC-1.7 Raw-rate (A) and empirical-Bayes (C) rankings produced with the same floor; overlap with the Wilson top and
  bottom 10 is reported.
- AC-1.8 Every accepted-rate row also shows answer rate and accepted rate among answered (AC-0.5 holds per row).

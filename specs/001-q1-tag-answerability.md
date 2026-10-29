# 001 — Tag answerability (prompt 1)

Status: **draft**

> What tags on a Stack Overflow question lead to the most answers and the highest rate of approved answers for the
> current year? What tags lead to the least? How about combinations of tags?

## Population

- **"Current year" = 2022**, the latest year in the snapshot (2022-01-01 → 2022-09-25). The README states this up front.
- Robustness check: the same ranking on full-year 2021. A tag whose rank flips between the two is flagged.

## Metrics

- **Most answers**: answers per question (primary) — total answers is mostly a volume effect, shown for context only.
- **Approved answers**: accepted rate (see `000`).
- Censoring: 2022 questions created after ~2022-08-25 had < 30 days to collect answers. Report the plain metric and a
  30-day-window version on the cohort that had the full window.

## Grain

- Single tags: one row per tag (a question with 3 tags counts once for each).
- Combinations: one row per unordered **tag pair**. Exact full tag sets as a secondary view (open).

## Ranking rules

- Minimum support so a 3-question tag cannot top the list (threshold set from the profile; candidates: 500 questions per
  tag, 100 per pair).
- Rank rates by a confidence-aware score (Wilson lower bound), not the raw rate; show the raw rate and n alongside.
- Report top and bottom N for each metric.

## Open questions

- Does "lead to" invite any causal language? Plan: no — describe association, note confounders (tag popularity, age).
- Pairs only, or also triples / exact sets?

## Acceptance criteria

- AC-1.1 Population limited to questions created in 2022; the cutoff date is printed with the result.
- AC-1.2 Every ranked tag/pair meets the minimum-support threshold.
- AC-1.3 Rates are between 0 and 1; n is shown next to each rate.
- AC-1.4 2021 robustness ranking produced; rank changes in the top/bottom N are listed.

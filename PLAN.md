# Plan

Working plan for the Stack Overflow answerability take-home. Specs live in [`specs/`](specs/); this file tracks
scope, schedule and decisions.

## Goal

1. **Answer the three prompts exactly** — the gate. A reviewer who reads only the README must get correct, sourced
   answers with assumptions, confidence and limitations.
2. Build those answers the way an analytics team should run them: **spec → dbt models → tests → governed metrics**.
   Every extra must serve a prompt, not sit beside it.

## Scope (Tier 2)

| Piece | What | Serves |
|---|---|---|
| Specs | `specs/00N-*.md`: definitions, grain, assumptions, acceptance criteria — written before SQL | all prompts |
| dbt project | `dbt-bigquery`; public dataset as sources; staging → intermediate → marts in project `so-answerability` | all prompts |
| Testing strategy | `TESTING.md` + generic, unit, singular/reconciliation tests, source freshness, model contracts; each acceptance criterion maps to a test | data quality grading criterion |
| Semantic layer | MetricFlow semantic models + metrics defined once; README numbers reproduced with `mf query` | metric consistency across prompts |
| Executable queries | `queries/q1.sql`, `q2.sql`, `q3.sql`: compiled, commented, run as-is in the BigQuery console (no dbt needed) | submission item 3 |

Out of scope unless time remains (Tier 3): CI, storytelling site (Evidence / Tableau Public), Dagster, dbt MCP.

## Known facts (verified 2026-10-29)

- `posts_questions`: 23,020,127 rows, 2008-07-31 → **2022-09-25**. The snapshot is frozen; "current year" cannot be 2026.
- Questions tagged **exactly** `dbt`: 168 total, first in 2020 (31 / 58 / 79 in 2020 / 2021 / 2022).
  Tagged `dbt` among others: 3 / 96 / 224 / 351 (2019–2022). Exactly `python`: 5.7K–16.3K per year.
- Project `so-answerability` runs in the BigQuery **sandbox** (no billing): tables expire after 60 days, so rebuild with
  `dbt build` if needed after late December 2026.

## Schedule (deadline Tue 2026-11-03)

| Day | Milestone |
|---|---|
| Thu 10-29 | Repo, plan, spec drafts; spec decision D1 with its EDA |
| Fri 10-30 | Spec decisions D2–D4 with EDA and the leakage KPI definition (done); then dbt env, sources + staging, data profile (`specs/000`), first tests |
| Sat 10-31 | Q1 + Q2 marts, tests, numbers |
| Sun 11-01 | Q3 features + semantic layer |
| Mon 11-02 | README narrative, compiled `queries/`, self-review |
| Tue 11-03 | Freeze, make the repo public, email the link |

## Decisions log

| Date | Decision | Why |
|---|---|---|
| 2026-10-29 | Tier 2 scope (dbt + tests + semantic layer + specs) | The two pain points the hiring manager named; extras stay tied to the prompts |
| 2026-10-29 | dbt-bigquery against the public dataset; no local extract | Reviewers already need a Google login; same warehouse family as the team |
| 2026-10-29 | Repo private while in progress, public at submission | Brief allows public or allow-list; no half-done work in public |
| 2026-10-29 | "Current year" = 2022 (latest year in the data, partial) | Data ends 2022-09-25 — see `specs/001` |
| 2026-10-29 | D1: rank tags and pairs with a ≥ 385-question floor + Wilson bounds (lower for highest, upper for lowest); raw rate and empirical Bayes as robustness checks | Floor from a ±5 pt precision target, since group size is far from normal; EDA in `eda/d1_sample_size` — see `specs/001` |
| 2026-10-30 | D2: accepted rate = accepted / **all** questions, as headline and ranking key; answer rate and accepted rate among answered shown beside it, not ranked | Literal reading of the prompt; accepted rate = answer rate × accepted among answered, so the columns explain each row; ranking the answered-only rate would need its own floor, which drops the hardest-to-answer tags. EDA in `eda/d2_denominator` — see `specs/000` |
| 2026-10-30 | D3: show P2's "question-to-answer ratio" as answers per question (with mean ± 1.96·SE intervals); questions per answer shown once as "Q÷A = 1 / this"; YoY as absolute change, relative beside it | Readability (higher = more answers); one metric shared with P1's "most answers"; splits like accepted rate (answer rate × answers per answered question). EDA in `eda/d3_ratio` — see `specs/002` |
| 2026-10-30 | D4: P3 features from the original title/body in `post_history` (one ~110 GB scan into a feature table); P1/P2 on current tags with a tag-edit robustness view; current-text and never-edited results as sensitivity checks; a leakage KPI tracked beside the answers | 45% of 2022 questions are edited, 9% only after their first answer, and edited questions do better, so a never-edited filter is biased. EDA in `eda/d4_edits` — see `specs/000`, `specs/003` |
| 2026-10-30 | Leakage KPI (part of D4): **exposure** = share of questions whose relevant field (tags for P1/P2, title/body for P3) was first edited after the first answer, on every result row; **impact** = each headline recomputed on the original version, with `severity: warn` dbt tests (P1: top/bottom 10 membership change or > 2.5 pt move; P2: YoY direction change or move beyond its interval; P3: effect direction change) | Exposure alone says what could leak, not whether the answer moved, and misses questions that left a group after an answer. In 2022, exposure rises with accepted rate (rank correlation 0.67; 8 of the top 10 tags above 10%), so the leakage sits where P1's headline is. 2.5 pt = half the ±5 pt target behind D1. EDA in `eda/d4_edits` — see `specs/000` |

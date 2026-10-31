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
| dbt project | `dbt-bigquery`; public dataset as sources; staging → intermediate → marts in project `so-answerability`. A clone sets one env var for its own GCP project (tracked `profiles.example.yml`); the one-time `post_history` text-scan model is tagged and left out of default builds | all prompts |
| Testing strategy | `TESTING.md` + generic, unit, singular/reconciliation tests, a snapshot check in place of source freshness, model contracts; each acceptance criterion maps to a test | data quality grading criterion |
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
| Sat 10-31 | One-time text scans (original tags and text, needed by the leakage checks): done; Q1 + Q2 marts, tests, first numbers: done; robustness method C, 30-day window, original-tags impact checks: next |
| Sun 11-01 | Q3 features + semantic layer |
| Mon 11-02 | README narrative, compiled `queries/`, self-review (incl. `AGENTS.md` / `CLAUDE.md`, tested from a clean clone) |
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
| 2026-10-30 | D1, answers per question: same 385 floor, "highest" sorted by the lower bound and "lowest" by the upper bound of mean ± 1.96·SE; raw mean and empirical Bayes as robustness checks; a Cochran's-rule flag per row | One rule for every P1 metric. A bootstrap interval, the raw mean and empirical Bayes give the same top / bottom 10 (9–10 of 10); the bootstrap would need a 5.8B-row SQL model or a Dataproc Python model (not in the sandbox) and is not repeatable without a seed. EDA in `eda/d1_answers_ranking` — see `specs/001` |
| 2026-10-30 | Disclose AI assistance: a short "How this was built" note in the README (spec-first, built with Claude Code as a pair programmer, every decision and its evidence in this log and `eda/`), plus a public `AGENTS.md` (setup, BigQuery cost guardrails, spec → acceptance criterion → test workflow) with a one-line `CLAUDE.md` importing it, written at self-review and tested from a clean clone | Every commit already credits Claude as co-author, so silence would read as evasive. The agent files help anyone who opens the repo with a coding agent: setup without trial and error, and no accidental scan of `body` or `post_history.text` against a cloner's free quota |
| 2026-10-30 | BigQuery cost guardrails: `maximum_bytes_billed` per dbt target (`dev` 20 GiB by default; `full_scan` 120 GiB, used only with `--target full_scan` for the tagged one-time text-scan models); each EDA script stops when its dry-run estimate is over 10 GB unless run with `--allow-gb N` | The cap applies per query, so the low default stops an accidental `posts_questions.body` (36 GB) or `post_history.text` (109 GB) scan before it reads anything; every EDA query so far scans 1–7 GB. The sandbox cannot bill, but its 1 TB/month query quota can run out before the deadline, and a cloner's project may have billing on |
| 2026-10-30 | P3 feature table, designed before the one-time scan: questions created 2018–2022 (plus the original tags of 2013–2017 questions originally tagged exactly `python` or `dbt`, for P2); the original title stored, the body turned into features and dropped; title, body and tag features listed in `specs/003` (core plus code, error-text, effort and greeting signals); one dbt macro per feature with a Markdown rule (`post_history`) and an HTML rule (`posts_questions.body`); current-text features in a second tagged model (~36 GB); both run first on a ~0.1% sample. A 5% random sample keeps the original and current question text and the original answer text (~3 GB), for language-model **quality labels** (discovery set → rubric → hand-labeled gold set that picks the labeling model → labels on the rest) and an answer-level view of acceptance | `post_history.text` bills ~109 GB per read whatever the row filter, so a feature left out costs a rescan: the list is fixed before the scan. The two text formats differ, so one rule for both would invent original-vs-current differences. The two reads together (~145 GB) exceed the `full_scan` cap, so they are two queries. Five cohorts let the two-cohort stability check (AC-3.3) rest on full years. Rule-based features see only the surface of the text; quality labels capture how a question is written, and the gold set makes them defensible. Kept separate from the rules, not compared as rivals: the rules cover every question and run in SQL. See `specs/003` |
| 2026-10-30 | dbt layout: staging = one **view** per source table, without `body` or `post_history.text`; one question hub table `int_questions` partitioned by creation year, with a (question, tag) view on top; the data profile as the dbt model `profile_by_year`. Source freshness replaced by a test that warns if the snapshot's row counts or newest dates change. Profile: `answer_count` equals the joined answers for every question; 0 orphan answers; 292 legacy (2008–2012) accepted ids that do not resolve, kept and listed by a warning test | Views store nothing (the sandbox has 10 GB) and read only the columns used; leaving the big text columns out of staging means no model can scan them by accident. The year partition cuts a 2022 query from 0.84 to 0.05 GB. A full build bills about 17 GB. Freshness would fail on every run of a frozen 2022 snapshot; what matters is that the snapshot behind the README numbers has not changed. See `specs/000` |
| 2026-10-31 | Both one-time text scans run (`post_history.text` 106 GiB, `posts_questions.body` 35 GiB) and checked on the stored tables instead of on samples; the Markdown (original) and HTML (current) rules agree on 4.05M never-edited questions: title 100%, has code 98.0%, code-block count 94%, inline code 98%, image 99.9%, links 98%, error / effort / greeting text >= 99.95%. The ~2% disagreement on code is the format floor, subtracted when the leakage KPI counts differences between original and current text. The `dbt_utils` package (pinned 1.3.0, installed with `dbt deps`) supplies the generic tests behind the acceptance criteria | A `TABLESAMPLE` takes whole storage blocks, so two samples of two tables cannot be compared question by question (a 0.1% sample was one block from one year); the comparison needed the full tables. Checking by rates on 2% samples still found two rule bugs before the full scans, and the per-question comparison found three more (a few cheap re-runs were worth it: the text scan was run twice, 106 GiB each) |

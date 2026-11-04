# EDA — D4: edited questions

Supports the edit rules in [`specs/000`](../../specs/000-shared-definitions.md) and
[`specs/003`](../../specs/003-q3-post-qualities.md). `posts_questions` keeps only the latest title, body and tags;
anyone with enough reputation can edit a question, often after it was answered. `post_history` keeps every version.

Words used below. **Leakage**: an edit made after the answer, and possibly because of it, read as if it were a quality
of the question (someone answers with `dplyr`, then adds the `dplyr` tag). **Exposure**: the share of a group's
questions whose tags (tag exposure) or title/body (text exposure) were first edited after the question's first answer;
it measures what *could* leak. Whether it moved a result is the impact check (see "What the checks found").

## Run it

```bash
.venv/Scripts/python eda/d4_edits/run_eda.py              # add --refresh to requery BigQuery
```

Same setup as [`d1_sample_size`](../d1_sample_size/README.md). The queries scan about 6.9 GB and 5.2 GB (each
dry-run first and capped at 10 GB): they read ids, types, dates and user ids from `post_history`, never its `text`
column, whose one read (106 GiB) happens in the dbt project, not here. Why that read was worth it on a free tier, and
what it billed: [README, "Running on a free tier"](../../README.md#running-on-a-free-tier).

| File | What |
|---|---|
| `sql/edit_profile.sql` | one row per (segment, year): edited questions, what was edited (tags vs title/body), by whom, whether after the first answer, and answer / accepted counts for never-edited questions |
| `sql/leakage_by_tag.sql` | one row per 2022 tag with ≥ 385 questions: questions whose tags / title-body were first edited after the first answer (tag and text exposure) |
| `run_eda.py` | runs both queries (cached as CSV in `output/`), joins the tag exposure to the D1 tag rates (`../d1_sample_size/output/tag_stats_2022.csv`), writes `output/summary.md` |

## What it found

1. **Edits are common.** 45% of 2022 questions were edited: 13.5% had tag edits (10.6% by someone other than the
   asker) and 40% title/body edits (18% by someone else). python-only: 52–60% edited per year; dbt-only: 24–42%
   ([what gets edited][s-what]).
2. **Some edits come after the answer.** 9% of 2022 questions had their title/body first edited after the first
   answer, 4.4% their tags (python-only title/body: 14–28% a year). Features measured on that text can be caused by
   the answer.
3. **A never-edited filter is biased.** Edited questions do better: 2022 answer rate 67% vs 57%, accepted rate 34% vs
   28% ([edited vs never edited][s-rates]). The gap isn't even stable: among python-only questions, the edited ones
   had the *lower* accepted rate every year from 2013 to 2020 (62.7% vs 68.3% in 2013). Edits also accumulate with
   age, so the filter keeps relatively more recent questions.
4. **Tag edits are small for P2.** 6–9% of python-only questions a year had a tag edit; dbt-only, 2 questions in
   2020–2022 (1 of them after the first answer).
5. **Data check:** `last_edit_date IS NULL` matches "no edit in `post_history`" almost exactly (32 differences out of
   637,996 edited questions; [data check][s-check]).
6. **The possible leakage sits where P1's headline is.** Across the 1,162 ranked 2022 tags, tag exposure has a median
   of 3.7% and a p90 of 10%, up to 62% for `webdriverwait`, a tag answerers add ([exposure by tag][s-tags]). It rises
   with accepted rate: rank correlation 0.67 (sort the tags by each measure and compare the two orders; 1 is the same
   order, 0 no relation), and still 0.49 among answered questions, since an unanswered question cannot be exposed.
   8 of the top 10 tags by accepted rate are above 10% (jq 19%), the whole bottom 10 at or under 3.1%
   ([exposure vs the P1 ranking][s-rank]).

**Decision (D4):** P3 features from the original title/body in `post_history` (one 106 GiB read into a feature
table); P1/P2 on current tags, the tags the prompts ask about, rebuilt on the original tags as a check; current text,
never-edited and not-edited-after-first-answer as P3 sensitivity checks; a leakage KPI tracked beside the answers.
Its definition (finding 6 above): exposure on every row, plus an impact check per prompt on the original version,
with `severity: warn` dbt tests (see [`specs/000`][spec]).

## What the checks found

The impact checks run in the dbt project, not here; the numbers below come from the root README.

- **P1** ([README][p1]): rebuilt on the original tags, the `warn` test flags 46 tags and 65 pairs. 9 of 10 tags stay in
  each accepted-rate list: `tidyr` (#5) falls under 385 questions on its original tags and `java-stream` comes in;
  `usb` (#8 at the bottom) gives way to `video-streaming`. Pairs keep 7 of the top 10 and 8 of the bottom 10; the #1
  pair, `arrays + google-sheets` (exposure 64%), falls under 385 and is not quoted as a finding.
- **P2** ([README][p2]): tag exposure 3.6–5.1% of python-only questions a year, 0–3.2% of dbt-only; 3 rows flagged
  (python 2019 and 2021, dbt 2022), none changes a conclusion.
- **P3** ([README][p3]): today's text would have given 5.1–7.4% of each year's questions a different "has a code
  block" value, beyond the format noise; the effects barely move (a code block +11.8 points on the original text,
  +11.3 on today's; the widest gap, an image, +4.7 vs +2.3), and the `warn` test raises one warning.

Exposure is a lower bound: a question whose field was edited before and again after its first answer counts as not
exposed (its first edit came first). The rebuilds compare the original version with today's, so they catch it.

[s-check]: output/summary.md#data-check-last_edit_date-vs-post_history
[s-what]: output/summary.md#what-gets-edited-by-whom-and-when
[s-rates]: output/summary.md#edited-vs-never-edited-questions
[s-tags]: output/summary.md#exposure-by-tag-2022-1162-tags-with--385-questions
[s-rank]: output/summary.md#exposure-vs-the-p1-accepted-rate-ranking-2022-d1-rule
[spec]: ../../specs/000-shared-definitions.md#leakage-kpi-d4
[p1]: ../../README.md#do-tag-edits-change-the-lists
[p2]: ../../README.md#do-tag-edits-change-it
[p3]: ../../README.md#do-edits-change-it

# EDA — D4: edited questions

Supports the edit rules in [`specs/000`](../../specs/000-shared-definitions.md) and
[`specs/003`](../../specs/003-q3-post-qualities.md). `posts_questions` keeps only the latest title, body and tags;
anyone with enough reputation can edit a question, often after it was answered. `post_history` keeps every version.

## Run it

```bash
.venv/Scripts/python eda/d4_edits/run_eda.py              # add --refresh to requery BigQuery
```

Same setup as [`d1_sample_size`](../d1_sample_size/README.md). The queries scan about 6.9 GB and 5.2 GB: they read
ids, types, dates and user ids from `post_history`, never its `text` column (~110 GB).

| File | What |
|---|---|
| `sql/edit_profile.sql` | one row per (segment, year): edited questions, what was edited (tags vs title/body), by whom, whether after the first answer, and answer / accepted counts for never-edited questions |
| `sql/leakage_by_tag.sql` | one row per 2022 tag with ≥ 385 questions: questions whose tags / title-body were first edited after the first answer (leakage exposure) |
| `run_eda.py` | runs the SQL, joins the tag exposure to the D1 tag rates (`../d1_sample_size/output/tag_stats_2022.csv`), writes `output/summary.md` |

## What it found

1. **Edits are common.** 45% of 2022 questions were edited: 13.5% had tag edits (10.6% by someone other than the
   asker) and 40% title/body edits (18% by someone else). python-only: 52–60% edited per year; dbt-only: 24–42%.
2. **Some edits come after the answer.** 9% of 2022 questions had their title/body first edited after the first
   answer (python-only: 14–28%). Features measured on that text can be caused by the answer.
3. **A never-edited filter is biased.** Edited questions do better: 2022 answer rate 67% vs 57%, accepted rate 34% vs
   28%. Edits also accumulate with age, so the filter keeps relatively more recent questions.
4. **Tag edits are small for P2.** 6–9% of python-only questions had a tag edit; dbt-only, 1 question in 2020–2022.
5. **Data check:** `last_edit_date IS NULL` matches "no edit in `post_history`" almost exactly (32 differences).
6. **Leakage sits where P1's headline is.** Across the 1,162 ranked 2022 tags, tag exposure (tags first edited after
   the first answer) has a median of 3.7% and a p90 of 10%, up to 62% for `webdriverwait`, a tag answerers add. It
   rises with accepted rate (rank correlation 0.67; 0.49 among answered questions, since an unanswered question
   cannot be exposed): 8 of the top 10 tags by accepted rate are above 10% (jq 19%), the whole bottom 10 below 3%.

**Decision (D4):** P3 features from the original title/body in `post_history` (one ~110 GB scan into a feature table);
P1/P2 on current tags with a tag-edit robustness view; current text, never-edited and not-edited-after-first-answer as
sensitivity checks; a leakage KPI tracked beside the answers. Its definition (finding 6 above): exposure on every row,
plus an impact check per prompt on the original version, with `severity: warn` dbt tests (see `specs/000`).

# EDA — D4: edited questions

Supports the edit rules in [`specs/000`](../../specs/000-shared-definitions.md) and
[`specs/003`](../../specs/003-q3-post-qualities.md). `posts_questions` keeps only the latest title, body and tags;
anyone with enough reputation can edit a question, often after it was answered. `post_history` keeps every version.

## Run it

```bash
.venv/Scripts/python eda/d4_edits/run_eda.py              # add --refresh to requery BigQuery
```

Same setup as [`d1_sample_size`](../d1_sample_size/README.md). The query scans about 6.9 GB: it reads ids, types,
dates and user ids from `post_history`, never its `text` column (~110 GB).

| File | What |
|---|---|
| `sql/edit_profile.sql` | one row per (segment, year): edited questions, what was edited (tags vs title/body), by whom, whether after the first answer, and answer / accepted counts for never-edited questions |
| `run_eda.py` | runs the SQL, writes `output/summary.md` |

## What it found

1. **Edits are common.** 45% of 2022 questions were edited: 13.5% had tag edits (10.6% by someone other than the
   asker) and 40% title/body edits (18% by someone else). python-only: 52–60% edited per year; dbt-only: 24–42%.
2. **Some edits come after the answer.** 9% of 2022 questions had their title/body first edited after the first
   answer (python-only: 14–28%). Features measured on that text can be caused by the answer.
3. **A never-edited filter is biased.** Edited questions do better: 2022 answer rate 67% vs 57%, accepted rate 34% vs
   28%. Edits also accumulate with age, so the filter keeps relatively more recent questions.
4. **Tag edits are small for P2.** 6–9% of python-only questions had a tag edit; dbt-only, 1 question in 2020–2022.
5. **Data check:** `last_edit_date IS NULL` matches "no edit in `post_history`" almost exactly (32 differences).

**Decision (D4):** P3 features from the original title/body in `post_history` (one ~110 GB scan into a feature table);
P1/P2 on current tags with a tag-edit robustness view; current text, never-edited and not-edited-after-first-answer as
sensitivity checks; a leakage KPI (edits after the first answer, features that changed) tracked beside the answers.

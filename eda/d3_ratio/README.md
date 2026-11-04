# EDA — D3: which way up for the question-to-answer ratio

Supports the definition in [`specs/000`](../../specs/000-shared-definitions.md) and its use in
[`specs/002`](../../specs/002-q2-python-vs-dbt.md): P2 asks for the "question-to-answer ratio". Questions per answer
(Q÷A, the literal reading) and answers per question (A÷Q) carry the same information, one being 1 / the other
(100 questions, 150 answers → 0.67 vs 1.5).

## Run it

```bash
.venv/Scripts/python eda/d3_ratio/run_eda.py              # add --refresh to requery BigQuery
```

Same setup as [`d1_sample_size`](../d1_sample_size/README.md) (venv, application-default credentials,
`so-answerability`). The query scans about 1.5 GB.

| File | What |
|---|---|
| `sql/answers_by_year.sql` | one row per (tag, year) for questions tagged exactly `python` or exactly `dbt`, 2013–2022: questions, unanswered, answers (from `answer_count` and from `posts_answers`), sum of squares for the SE |
| `run_eda.py` | runs the SQL, computes both orientations with 95% intervals, YoY changes and the answer-rate split, writes `output/summary.md` |

## What it found

1. **The relative YoY change depends on the orientation.** python-only, 2021 → 2022: answers per question −17%,
   questions per answer +21%. Same data, different headline %, so one orientation must be chosen and stated.
2. **python-only answers per question falls steadily**: 2.31 (2013) → 1.52 (2021) → 1.26 (2022, partial), with
   intervals of about ±0.02–0.04.
3. **About ¾ of python's 2022 drop is censoring.** Answers per question = answer rate × answers per answered question:
   the answer rate fell 85% → 73% while answers per answered question only went 1.79 → 1.71. Same story as the
   accepted rate in [`d2_denominator`](../d2_denominator/README.md).
4. **dbt-only cannot support a trend**: 1.39 / 1.14 / 1.06 answers per question (2020–2022, 31 / 58 / 79 questions),
   with 95% intervals overlapping year to year.
5. **Data check:** for these questions, `answer_count` matches the answers present in `posts_answers` exactly (gap 0).
   The full check for all questions is AC-0.4.

**Decision (D3, `specs/000` and `specs/002`):** show answers per question, with mean ± 1.96·SE intervals; questions per
answer appears once as "Q÷A = 1 / this" in the README and the presentation. YoY change as absolute difference, relative
beside it.

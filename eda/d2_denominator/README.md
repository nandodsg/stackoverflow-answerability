# EDA — D2: which denominator for accepted rate

Supports the definition in [`specs/000`](../../specs/000-shared-definitions.md): should "rate of approved answers on
questions" divide by all questions (A) or by answered questions (B)? The two are linked:
**A = answer rate × B** (100 questions, 60 answered, 30 accepted → 30% = 60% × 50%).

## Run it

```bash
.venv/Scripts/python eda/d2_denominator/run_eda.py              # add --refresh to requery BigQuery
```

Same setup as [`d1_sample_size`](../d1_sample_size/README.md) (venv, application-default credentials,
`so-answerability`). The query scans about 1.1 GB; the 2022 tag table is reused from the D1 output, so run the D1 EDA
first on a fresh clone.

| File | What |
|---|---|
| `sql/single_tag_by_year.sql` | one row per (tag, year) for questions tagged exactly `python` or exactly `dbt`, 2013–2022 |
| `run_eda.py` | runs the SQL, computes A, B and their Wilson bounds, writes `output/summary.md` |

## What it found

1. **The highest tags barely depend on the choice.** 8 of the top 10 tags in 2022 are the same under A and B (data.table,
   dplyr, jq, awk, regex…).
2. **The lowest tags depend on it, and partly through the floor.** Under A, the lowest tags are the ones few people
   answer (magento2: 41% answered, 9% accepted). None of those 10 has 385 *answered* questions, so ranking B with the
   385 floor counted on its own denominator drops them all (0/10 overlap, 692 eligible tags instead of 1,162). With
   the floor counted on questions, the overlap is 5/10: the other five are tags answered about half the time whose
   askers rarely accept (installation, salesforce, sharepoint-online, single-sign-on, npm-install).
3. **In P2, B separates censoring from behaviour.** Questions tagged only `python`: A falls 43% → 35% from 2021 to
   2022, B only 51% → 48%. Most of the 2022 drop is questions not answered yet when the data stops. For `dbt` only
   (31 / 58 / 79 questions, 2020–2022), the Wilson ranges of A and B overlap year to year, so neither supports a
   trend.

**Decision (D2, `specs/000`):** accepted rate = accepted / all questions, as headline and ranking key. Answer rate and
accepted rate among answered are shown beside it on every row and are not ranked, so the D1 rule applies unchanged
and the hardest-to-answer tags stay in the lists.

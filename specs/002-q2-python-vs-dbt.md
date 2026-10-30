# 002 — python-only vs dbt-only, year over year (prompt 2)

Status: **draft**

> For posts which are tagged with only 'python' or 'dbt', what is the year over year change of question-to-answer ratio
> for the last 10 years? How about the rate of approved answers on questions for the same time period? How do posts
> tagged with only 'python' compare to posts only tagged with 'dbt'?

## Population

- **Only `python`**: `tags = 'python'` exactly. **Only `dbt`**: `tags = 'dbt'` exactly. Read literally: one tag, no others.
- **Last 10 years**: 2013 → 2022 (2022 partial, ends 09-25; flagged in every chart and table).
- Cohort by **question creation year**; answers are attributed to their question's year.
- **Current tags** (D4, see `000`): "posts which are tagged" is read as the tags today. 6–9% of python-only questions
  had a tag edit (dbt-only: 1 in 2020–2022); a robustness view drops tag-edited questions.
- **Leakage KPI** (see `000`): each (tag, year) row shows its tag exposure (python-only 3.8–5.1% per year). Impact
  check: the populations rebuilt from the original tags, which also catches questions that left them after an answer
  (posted as `python`, retagged `python|pandas`); a YoY change that switches direction or moves by more than its
  interval half-width is flagged.

## Metrics

- **Question-to-answer ratio (D3)**: shown as **answers per question** (see `000`), with a 95% interval
  (mean ± 1.96 × SE). The literal questions per answer is shown once, with the sentence "Q÷A = 1 / this" in the
  README and the presentation, and is never charted.
  - Why: higher = more answers reads naturally; it is the same metric as P1's "most answers", so one definition serves
    both prompts; and it splits like accepted rate does (answer rate × answers per answered question).
  - YoY change: absolute difference (e.g. −0.26 answers per question) as the main number, relative difference beside
    it. Relative changes do not flip cleanly under inversion (python 2021 → 2022: −17% here, +21% as questions per
    answer), so the README states which one it uses.
  - 2022 EDA ([`eda/d3_ratio`](../eda/d3_ratio/README.md)): python-only falls 2.31 → 1.52 → 1.26 answers per question
    (2013 / 2021 / 2022); about ¾ of the 2022 drop comes from the lower answer rate (questions not answered yet when
    the data stops). dbt-only: 1.39 / 1.14 / 1.06 (2020–2022), intervals overlapping year to year.
- **Accepted rate** (out of all questions, see `000`, D2) per cohort year, YoY change in percentage points. Answer
  rate and accepted rate among answered shown beside it: they split a change into "fewer questions answered" vs
  "askers accepting less". 2022 EDA ([`eda/d2_denominator`](../eda/d2_denominator/README.md)): python-only accepted
  rate falls 43% → 35% from 2021 to 2022, but accepted among answered only 51% → 48%; most of the drop is 2022
  questions not yet answered when the data stops (censoring), which the narrative must say.

## The dbt problem (state it, don't hide it)

- dbt-only questions exist only from 2020: 31 / 58 / 79. "Ten years" is 2.7 years for dbt, on tiny samples.
- Show confidence intervals for dbt rates; avoid YoY claims the intervals don't support.
- Sensitivity view, clearly labeled: questions tagged `dbt` among other tags (96 / 224 / 351). Does not replace the
  literal answer.

## Acceptance criteria

- AC-2.1 Exact-match filter on `tags`; a unit test covers `python`, `python|pandas`, `python-3.x`, `dbt`, `dbt|sql`.
- AC-2.2 One row per (tag, year) for 2013–2022; years with zero dbt questions shown as zero / not applicable, not dropped.
- AC-2.3 Every dbt rate is shown with n and an interval.
- AC-2.4 2022 marked partial in output.
- AC-2.5 Answers per question is the charted ratio; questions per answer appears once with "Q÷A = 1 / this"; each YoY
  change states whether it is absolute or relative.
- AC-2.6 Every row shows its tag exposure; the original-tags populations are produced and their warnings (AC-0.10) are
  listed in the README.

# 002 — python-only vs dbt-only, year over year (prompt 2)

Status: **draft**

> For posts which are tagged with only 'python' or 'dbt', what is the year over year change of question-to-answer ratio
> for the last 10 years? How about the rate of approved answers on questions for the same time period? How do posts
> tagged with only 'python' compare to posts only tagged with 'dbt'?

## Population

- **Only `python`**: `tags = 'python'` exactly. **Only `dbt`**: `tags = 'dbt'` exactly. Read literally: one tag, no others.
- **Last 10 years**: 2013 → 2022 (2022 partial, ends 09-25; flagged in every chart and table).
- Cohort by **question creation year**; answers are attributed to their question's year.

## Metrics

- **Question-to-answer ratio** = questions / answers (literal reading). Answers per question shown alongside, since it
  reads more naturally. YoY change as absolute and relative difference.
- **Accepted rate** per cohort year, YoY change in percentage points.

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

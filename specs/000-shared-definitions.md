# 000 — Shared definitions & data profile

Status: **draft**

## Source

`bigquery-public-data.stackoverflow` — `posts_questions`, `posts_answers`, `users`, `tags`. Static snapshot, last
question created 2022-09-25 05:56 UTC.

## Definitions (used by every prompt)

| Term | Definition | Note |
|---|---|---|
| Question | Row in `posts_questions` | |
| Answer | Row in `posts_answers` whose `parent_id` is a question | Deleted answers are absent from the snapshot |
| Answered question | Question with ≥ 1 answer | |
| Accepted ("approved") answer | `accepted_answer_id IS NOT NULL` | The brief says "approved"; Stack Overflow calls it accepted |
| Answer rate | answered questions / questions | |
| Accepted rate | questions with an accepted answer / questions | Denominator = all questions, not answered ones (open: report both?) |
| Answers per question | answers / questions | |
| Tag set | `tags` split on `|` | Questions only; answers carry no tags |

## Data quality checks to run first (profile → tests)

- Date range and row counts per table; volume per year.
- `answer_count` on the question vs answers actually joined from `posts_answers` — size and direction of the gap.
- `accepted_answer_id` points to an answer that exists and whose `parent_id` is that question.
- Null / empty `tags`; tag strings with odd delimiters or casing.
- Duplicate `id`s.

## Known limitations

- **Frozen snapshot**: no data after 2022-09-25.
- **Right-censoring**: newer questions had less time to collect answers and acceptance. Windowed metrics (e.g. answered
  within 30 days) need the answer's `creation_date`. The acceptance *time* is not in the data, only which answer was
  accepted; the accepted answer's creation date is a proxy.
- **Current-state attributes**: `users.reputation`, `score`, `view_count` reflect the snapshot date, not posting time.

## Acceptance criteria

- AC-0.1 Every question `id` is unique and not null.
- AC-0.2 Every answer's `parent_id` resolves to a question (or the orphan count is reported).
- AC-0.3 Every non-null `accepted_answer_id` resolves to an answer of that same question (or exceptions are reported).
- AC-0.4 The `answer_count` vs joined-answers gap is measured and documented; it does not silently change a result.

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
| Accepted rate | questions with an accepted answer / questions | The headline and ranking metric (D2). Denominator = **all** questions, the literal reading of "rate of approved answers on questions" |
| Accepted rate among answered | questions with an accepted answer / answered questions | Shown beside accepted rate, never ranked (D2) |
| Answers per question | answers / questions | |

**How the three rates fit together (D2).** A question goes through two steps: someone answers it (or not), then the
asker accepts an answer (or not). So **accepted rate = answer rate × accepted rate among answered**. Example: 100
questions, 60 answered, 30 accepted → 30% = 60% × 50%. Every table that shows accepted rate also shows the other two,
so a reader can tell "few people answer" apart from "askers rarely accept". Accepted rate among answered is not
ranked: its n is the number of answered questions, so ranking it would need its own floor, and that floor would
drop exactly the tags that are hardest to get answered (see `001`).
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
- AC-0.5 On every row that shows the three rates, accepted rate = answer rate × accepted rate among answered (to
  rounding), and accepted rate among answered is null when no question was answered.

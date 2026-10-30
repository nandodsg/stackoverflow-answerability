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
| Answers per question | total answers / total questions, for the group | The headline for "question-to-answer ratio" (P2, D3) and for "most answers" (P1). A ratio of the group's totals, never an average of per-question ratios (undefined for unanswered questions). Null only when the group has 0 questions |
| Questions per answer | total questions / total answers = 1 / answers per question | The literal reading of P2's "question-to-answer ratio". Shown once, with the sentence "Q÷A = 1 / this", never charted (D3). Null when the group has 0 answers |
| Tag set | `tags` split on `\|` | Questions only; answers carry no tags |

**How the three rates fit together (D2).** A question goes through two steps: someone answers it (or not), then the
asker accepts an answer (or not). So **accepted rate = answer rate × accepted rate among answered**. Example: 100
questions, 60 answered, 30 accepted → 30% = 60% × 50%. Every table that shows accepted rate also shows the other two,
so a reader can tell "few people answer" apart from "askers rarely accept". Accepted rate among answered is not
ranked: its n is the number of answered questions, so ranking it would need its own floor, and that floor would
drop exactly the tags that are hardest to get answered (see `001`).

**Answers per question splits the same way (D3).** **Answers per question = answer rate × answers per answered
question.** Example: 100 questions, 60 answered, 150 answers → 1.5 = 60% × 2.5. A change in answers per question can
then be read as "fewer questions answered" vs "fewer answers on each answered question". It uses all questions as the
denominator, like accepted rate (D2).

**Uncertainty of answers per question (D3).** It is an average of `answer_count`, so its 95% interval is
mean ± 1.96 × SE, with SE = SD / √n and the SD measured from the questions in the group. The interval for questions
per answer is the inverted interval (1 / upper, 1 / lower).

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
- **Edited questions (D4)**: `posts_questions` keeps only the latest title, body and tags; 45% of 2022 questions were
  edited (13.5% tags, 40% title/body; 9% had their title/body first edited after the first answer). Edited questions do
  better (2022 accepted rate 34% vs 28% never edited), so filtering to never-edited questions is biased and is used
  only as a robustness check. `post_history` keeps every version (types 1/2/3 = original title/body/tags); reading its
  text scans ~110 GB once. Rules: P1/P2 use current tags (the prompt's "are tagged"), with a check that drops
  tag-edited questions; P3 features come from the original title/body. EDA: [`eda/d4_edits`](../eda/d4_edits/README.md).
- **Leakage KPI (D4)**: share of questions whose title/body (or tags) were first edited after the first answer, per
  creation year, plus the share whose P3 features differ between the original and current version. Defined once in
  the semantic layer and tracked beside the answers, so the size of the problem is visible, not just described.
  *Exact definition and thresholds to detail with Nando.*

## Acceptance criteria

- AC-0.1 Every question `id` is unique and not null.
- AC-0.2 Every answer's `parent_id` resolves to a question (or the orphan count is reported).
- AC-0.3 Every non-null `accepted_answer_id` resolves to an answer of that same question (or exceptions are reported).
- AC-0.4 The `answer_count` vs joined-answers gap is measured and documented; it does not silently change a result.
- AC-0.5 On every row that shows the three rates, accepted rate = answer rate × accepted rate among answered (to
  rounding), and accepted rate among answered is null when no question was answered.
- AC-0.6 Answers per question is computed as total answers / total questions per group; questions per answer equals
  its inverse (unit test); answers per question = answer rate × answers per answered question per row (to rounding).
- AC-0.7 `last_edit_date IS NULL` agrees with "no title/body/tag edit in `post_history`" (2022 EDA: 32 differences out
  of ~638K edited questions); the difference is reported.
- AC-0.8 The leakage KPI is produced per creation year for every population used in P1–P3.

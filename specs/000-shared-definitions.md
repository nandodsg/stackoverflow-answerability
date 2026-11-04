# 000 — Shared definitions & data profile

Status: **implemented**. Decisions D2, D3 and D4 applied; each acceptance criterion is mapped to its check in
[TESTING.md](../TESTING.md#shared-definitions-specs000).

## Source

`bigquery-public-data.stackoverflow` — `posts_questions`, `posts_answers`, `post_history`, `users` (and `tags` for the
profile). Static snapshot, last question created 2022-09-25 05:56 UTC.

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

## Data profile (2022-09 snapshot)

Built by the dbt model `profile_by_year` (one row per year) and enforced by the tests listed with each AC below. Only
metadata columns are read; `body` and `post_history.text` never are.

| Table | Rows | First / last `creation_date` (UTC) | Notes |
|---|---|---|---|
| `posts_questions` | 23,020,127 | 2008-07-31 → 2022-09-25 05:56 | 1,268,788 in 2022 (partial year) |
| `posts_answers` | 34,024,119 | 2008-07-31 → 2022-09-25 05:56 | |
| `post_history` | 152,435,941 | 2008-07-31 → 2022-09-25 07:36 | Revisions of questions **and** answers: join to questions before counting question edits |
| `users` | 18,712,212 | 2008-07-31 → 2022-09-25 05:52 | |

- **`answer_count` vs joined answers (AC-0.4): no gap.** For every question, `answer_count` equals the answers present
  in `posts_answers` (0 questions differ, in every year), so answered/unanswered never depends on which one is used.
  The snapshot appears to count only the answers it contains; deleted answers are absent from both.
  Metrics use `answer_count`.
- **Orphan answers (AC-0.2): none.** Every answer's `parent_id` is a question; none is null.
- **Accepted answers (AC-0.3): 292 exceptions out of 11.8M**, all on questions created 2008–2012: 229 point to an
  answer missing from the snapshot, 62 to an answer now under another question (likely merged questions), 1 to a
  question id. No prompt uses those years (P1: 2021–2022; P2: 2013–2022), so they are kept as accepted, as the
  definition says, and listed by a warning test.
- **Keys (AC-0.1)**: `id` is unique and non-null in all four tables; no id is both a question and an answer.
- **Tags**: never null or empty, always lower-case, no empty segments or duplicate tags within a question; all 63,591
  distinct tags exist in the `tags` table. 119 old questions carry 6 tags (the current limit is 5).
- **Baseline check**: 2022 accepted rate = 386,683 / 1,268,788 = 30.5%, the figure quoted in `001`.
- **Frozen snapshot**: dbt source freshness compares the newest row with today, so it would fail on every run.
  Instead a test warns if the row count or newest `creation_date` of questions or answers ever differs from the
  values above, which would mean the README numbers are stale.

## Known limitations

- **Frozen snapshot**: no data after 2022-09-25.
- **Right-censoring**: newer questions had less time to collect answers and acceptance. Windowed metrics (e.g. answered
  within 30 days) need the answer's `creation_date`. The acceptance *time* is not in the data, only which answer was
  accepted; the accepted answer's creation date is a proxy.
- **Current-state attributes**: `users.reputation`, `score`, `view_count` reflect the snapshot date, not posting time.
- **Survivorship**: deleted questions are absent. Stack Overflow deletes inactive questions automatically, mainly
  unanswered, low-score ones ([help/deleted-questions](https://stackoverflow.com/help/deleted-questions)), and askers
  cannot delete a question with an accepted or upvoted answer. So answer and accepted rates are biased upward, more for
  older cohorts, which have had longer to be cleaned up; the P2 trend narrative states this.
- **Edited questions (D4)**: `posts_questions` keeps only the latest title, body and tags; 45% of 2022 questions were
  edited (13.5% tags, 40% title/body; 9% had their title/body first edited after the first answer). Edited questions do
  better (2022 accepted rate 34% vs 28% never edited), so filtering to never-edited questions is biased and is used
  only as a robustness check. `post_history` keeps every version (types 1/2/3 = original title/body/tags); reading its
  text takes one 106 GiB read. Rules: P1/P2 use current tags (the prompt's "are tagged"), with a check that drops
  tag-edited questions; P3 features come from the original title/body. EDA: [`eda/d4_edits`](../eda/d4_edits/README.md).
- **Leakage**: an edit made after a question was answered can be caused by the answer, so a tag or a text feature
  read from the current version may be an effect of the outcome rather than a quality of the question. Measured by
  the leakage KPI below.

## Leakage KPI (D4)

Tracked beside the answers so the size of the edit problem is visible, not just described. Two layers:

**Exposure** (every row of every result table). Share of the group's questions whose relevant field was first edited
after the question's first answer:

| Prompt | Relevant field | `post_history` types |
|---|---|---|
| P1, P2 | tags (group membership) | 6, 9 (tags edited, rolled back) |
| P3 | title or body (features) | 4, 5, 7, 8 (title/body edited, rolled back) |

- Reference event: the **first answer's** `creation_date`, the earliest moment an answer can influence an edit. The
  acceptance time is not in the data (see right-censoring).
- Any editor counts, the asker included: an asker adding "EDIT: solved" after an answer is leakage too.
- Denominator: all questions in the group, like every rate here (D2). An unanswered question cannot be exposed, so
  exposure is partly tied to answer rate; the README says so.
- Exposure on current tags misses questions that **left** a group after the answer (e.g. posted as `python`,
  retagged `python|pandas`), which is why the impact layer uses the original tags.
- Exposure is a lower bound: it looks at the **first** edit of the field, so a question edited before and again after
  its first answer counts as not exposed. The impact layer compares the original version with the current one, so it
  catches those questions.

**Impact** (one check per prompt). The headline recomputed on the original version from `post_history` (type 3 for
tags, types 1/2 for title/body, read in the same one-time text scan as AC-3.4) and compared with the current version.
Thresholds are dbt tests with `severity: warn`: they print a warning in `dbt build` without failing it, and every
warning is reported in the README.

| Prompt | Impact check | Threshold (warn) |
|---|---|---|
| P1 | rankings on original vs current tags | any tag or pair entering or leaving a top / bottom 10; any ranked row whose accepted rate moves > 2.5 points (half the ±5-point precision target behind the D1 floor) |
| P2 | answers per question and accepted rate per year, original vs current tags | the YoY change switches direction, or moves by more than the half-width of its 95% interval (D3) |
| P3 | each feature's effect, original vs current text; share of questions whose feature value differs between the two | the effect changes direction (labeled "leakage-sensitive", AC-3.5) |

2022 EDA ([`eda/d4_edits`](../eda/d4_edits/README.md)): tag exposure is 3.7% for the median ranked tag but rises with
accepted rate (rank correlation 0.67; 0.49 among answered questions). 8 of the 2022 top 10 tags by accepted rate are
above 10% (jq 19%), the whole bottom 10 below 3%, and `webdriverwait` reaches 62% (a tag answerers add). The leakage
sits where P1's headline is, so the impact check matters most there.

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
- AC-0.8 Leakage exposure is produced per creation year for every population used in P1–P3 and shown on every result
  row, with all questions in the group as denominator.
- AC-0.9 Exposure counts an edit only when its `post_history` type matches the prompt's field and its time is after
  the first answer (unit test: an edit before the first answer, a tag edit for P3, and a never-answered question are
  not exposed; a rollback after the first answer is).
- AC-0.10 Each impact check of P1–P3 runs as a `severity: warn` dbt test with the thresholds above, and every warning
  is listed in the README.

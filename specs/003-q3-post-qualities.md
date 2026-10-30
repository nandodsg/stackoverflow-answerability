# 003 — Non-tag qualities of a post (prompt 3)

Status: **draft**

> Other than tags, what qualities on a post correlate with the highest rate of answer and approved answer? Feel free to
> get creative.

## Outcomes

Answer rate and accepted rate (out of all questions, see `000`, D2), ideally within a fixed window to limit censoring.
Accepted rate among answered is reported beside them, so each feature's link to acceptance can be split into "helps
the question get answered" and "helps the asker accept". It is never the only outcome: it looks at answered questions
only, so a quality that helps a question get answered at all cannot show up in it.

## Candidate features (known at posting time)

Title and body features come from the **original** version in `post_history` (types 1 and 2), not from the edited
text in `posts_questions` (D4, see `000`): 40% of 2022 questions had title/body edits and 9% were first edited after
the first answer, so features measured on the current text can be caused by the answer.

| Feature | From | Leakage risk |
|---|---|---|
| Title length, title ends with "?" | original `title` (`post_history` type 1) | low once original text is used; current text would leak (edits after answers) |
| Body length, has code block, has image, link count | original `body` (`post_history` type 2, scanned once into a feature table, then dropped) | low once original text is used; current text would leak |
| Number of tags | original tags (`post_history` type 3) | low; current tags change after posting (13.5% of 2022 questions) |
| Hour of day / day of week posted (UTC) | `creation_date` | none |
| Asker's account age at posting | `users.creation_date` | none |
| Asker's prior questions count | history of `posts_questions` | none |

## Excluded or flagged as post-hoc

`score`, `view_count`, `comment_count`, `favorite_count`, current `users.reputation`, edits after posting — these are
partly *caused* by the question being answered, or measured at snapshot time. Reported, if at all, as "associated
after the fact", never as a quality of the post.

## Method

- Rates by feature bucket with n and intervals.
- Control for era and topic: compare within year cohorts and within large tags, so "code blocks help" is not just
  "Python questions have code".
- Optional: logistic regression (BigQuery ML) to see effects net of each other. Correlation language only.
- Sensitivity (D4): each feature's effect is also computed from the current text and on two subsets, never-edited
  questions and questions not edited after their first answer; a finding that changes direction is labeled.
- Leakage KPI (see `000`): text exposure (title/body first edited after the first answer) per year, and for each
  feature the share of questions whose value differs between the original and current text (e.g. "has code block").
  It shows how much reading the current text would have misled.

## Acceptance criteria

- AC-3.1 Every feature is computable from data available at posting time.
- AC-3.2 `body` is scanned once into a feature table; no downstream model reads `body`.
- AC-3.3 Each reported effect holds (same direction) in at least two year cohorts, or is labeled unstable.
- AC-3.4 Title/body features are computed from the original version in `post_history`; the `post_history` text is
  scanned once into a feature table, and its scan size is stated in the README.
- AC-3.5 Each effect is also reported on current text, never-edited and not-edited-after-first-answer subsets.
- AC-3.6 Text exposure and, per feature, the share of questions whose value changed between original and current text
  are reported; a direction change raises an AC-0.10 warning.

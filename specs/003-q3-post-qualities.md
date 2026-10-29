# 003 — Non-tag qualities of a post (prompt 3)

Status: **draft**

> Other than tags, what qualities on a post correlate with the highest rate of answer and approved answer? Feel free to
> get creative.

## Outcomes

Answer rate and accepted rate (see `000`), ideally within a fixed window to limit censoring.

## Candidate features (known at posting time)

| Feature | From | Leakage risk |
|---|---|---|
| Title length, title ends with "?" | `title` | none |
| Body length, has code block, has image, link count | `body` (scanned once, then dropped) | none |
| Number of tags | `tags` | none |
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

## Acceptance criteria

- AC-3.1 Every feature is computable from data available at posting time.
- AC-3.2 `body` is scanned once into a feature table; no downstream model reads `body`.
- AC-3.3 Each reported effect holds (same direction) in at least two year cohorts, or is labeled unstable.

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

## Feature table (decided 2026-10-30)

One model reads `post_history.text` once (~109 GB; the column bills in full whatever the row filter) and stores one
row per question with numbers and flags, never the body (plus one row per answer of the 5% sample, same columns).
Choices:

- **Cohorts**: every question created **2018–2022** (five years; 2022 is partial and censored, so the AC-3.3
  two-cohort check rests on full years). Plus the original tags of 2013–2017 questions originally tagged exactly
  `python` or `dbt`, for P2's impact check (see `002`).
- **Stored text**: the original **title** of every question in the cohorts (short; any later title feature is
  computed from it without a rescan). For a **5% random sample** of 2018–2022 questions (~425k), also the original
  and current title and body, and the original text of their answers (answer revisions are in the same
  `post_history` read, so they add storage, not scan). About 3 GB in all, inside the sandbox's 10 GB. Outside the
  sample the body is read, turned into features and dropped.
- **Features from the original text** (each one column):
  - Title: length in characters, word count, ends with "?", starts with a question word (how / why / what / …).
  - Body: length in characters, has code block, number of code blocks, has inline code, has image, link count,
    error or traceback text, "what I tried" effort phrases, greetings or thanks ("hi", "thanks in advance").
  - Tags: original tag set and tag count (type 3), also used by the P1/P2 impact checks.
- **Markdown vs HTML**: `post_history.text` holds the Markdown the asker typed (code fenced with ``` or indented);
  `posts_questions.body` holds rendered HTML (`<pre><code>`). Each feature has one rule per format, written once as a
  dbt macro, so original-vs-current differences are real and not a parsing artifact.
- **Current-text features** (AC-3.5): the same macros on `posts_questions.body` in a second tagged model (~36 GB).
  The two reads cannot share one query: together they bill ~145 GB, above the `full_scan` cap.
- **Sample first**: both models run once on a `TABLESAMPLE` of their source (`--vars '{sample_pct: 2}'`) to check the
  tag parsing and the rows per year before the full run. A sample takes whole storage blocks (a 0.1% sample was one
  block from one year), so the Markdown/HTML agreement is checked per question on the stored tables after the scan.
- **Markdown vs HTML agreement** (4.05M never-edited questions, 2018–2022; the two texts of such a question have the
  same content): title features 100%; has code block 98.0%; number of code blocks 94.2%; inline code 97.7%; image 99.9%;
  links 98.4%; error, effort and greeting text >= 99.95%. The remaining ~2% on code is the format floor (an indented
  block the stored text lost the first indent of, a fence the old site did not render, ...). Findings that use code
  blocks use "has a code block"; the count is the weaker feature. The leakage KPI (AC-3.6) subtracts this floor from
  the original-vs-current differences. Original tags equal the current tags for 99.9999% of never-edited questions.
- The macros live in `macros/text_features.sql`; `tests/assert_text_feature_rules.sql` holds hand-written examples of
  every rule (Markdown and HTML) and reads no table.
- Features that need no text (hour and weekday posted, asker account age, asker's prior questions, first question)
  come from metadata in regular models.

## Quality labels (decided 2026-10-31)

Text features measured by rules (length, code block, links) see the surface only. **Quality labels** describe how a
question is written: clarity, a reproducible example, a stated goal, effort shown. They are not topics, so they are
not tags in the sense of the prompt. They are judgments, made by a language model on the 5% sample, in three
separate sets that never mix:

1. **Discovery** (~200 questions, pairs from the same tag and year, one accepted and one unanswered): a large model
   reads them and proposes candidate labels with definitions; the list is curated by hand into a rubric.
2. **Gold** (~150 other questions): labeled by hand on the rubric. Each candidate labeling model (a typed decision
   model such as TypeSafe Jev, a Claude model, an open-weights model) is scored against it; a label is kept only if
   the chosen model agrees well enough, and the cheapest model that passes labels the rest.
3. **Analysis** (the rest of the sample): labeled by the chosen model; rates by label, as for every other feature.

Rule-based features and quality labels are not competing methods. Rule-based features cover every question and
are reproducible in `queries/q3.sql`; labels cover the sample and are stored as a table. They meet in two checks: a
label should agree with its rule-based neighbour where one exists (a "reproducible example" mostly has a code
block), and a joint view shows whether a label adds anything beyond the rules (e.g. among questions with code,
does a reproducible one do better?).

**Answer lens.** Answers are posts too. Among the answers in the sample, which qualities go with being the accepted
one (same rules and labels, original text, one row per answer). Answer text can never explain the question's answer
rate (an unanswered question has no answer), so this lens is reported separately, for acceptance only.

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

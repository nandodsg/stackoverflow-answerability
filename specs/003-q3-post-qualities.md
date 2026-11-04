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

**Discovery pass (run 2026-10-31).** The discovery set is the dbt model `int_label_discovery_pairs` (question ids
only): 200 pairs from the 5% sample, 2018–2021 (2022 is censored), each pair sharing primary tag, year and the
has-code-block value (so the model looks past the rule we already have), with an accepted answer written by someone
other than the asker on one side (self-accepted questions are left out) and no answer on the other; 50 pairs per year,
at most 3 per (tag, year), drawn in a fixed pseudo-random order; 87 tags in the result. A singular test re-checks every
pair against the source tables. `labels/discover_labels.py` runs two stages with Claude Opus 5.5:
**blind** (batches of 20 pairs, outcome hidden, A/B order shuffled: guess which question got the accepted answer and
list the differences) and **reveal** (all notes with the true outcomes: propose labels from the differences that
actually separated the outcomes). Hiding the outcome keeps the model from turning noise into reasons. The blind guess
was right on 144 of 200 pairs (72%; 15 of 16 when confident), an upper bound on what writing explains, since many
right guesses rested on topic. Ten candidates came back (`labels/output/discovery/candidate_labels.md`); effort shown,
links to research, polished prose, structure and tone were mixed or favored the unanswered side. Cost: US$ 3.35 of
API credit (`labels/spend_log.csv`; one call dropped mid-stream and was billed, US$ 0.49, read from the credit balance). The free `count` mode of the
script gives the exact input tokens before any paid run.

**Rubric and gold set (decided 2026-10-31).** The candidates were curated into six labels in `labels/rubric.md`, the
single source of the definitions (`labels/rubric.py` parses the keys and levels from it; its version is a hash of the
file): `worked_example`, `ask_scope` (narrow / broad, including opinion or recommendation requests / multiple / no clear
ask), `failure_description` (concrete / vague / not applicable), `code_focus` (focused / partial / dump /
not applicable), `environment_dependent` and `image_only_evidence` (judged from the text alone; nobody sees the
images). Each label is analyzed level by level against its first level, as the rule-based buckets are; `not_applicable`
is left out of that label's comparison. The gold set is the view `int_label_gold_questions` (ids only, with a test that
re-checks it against the sources): 120 questions from the 5% sample, 2018–2022, minus the discovery questions; 20 for a
**practice** round, whose disagreements with a model may tighten the rubric's wording, and 100 for **scoring** on the
frozen rubric; a third of each set has an image, so the image label has enough positives to score. Labels are made on
a local page (`labels/gold_page.py`) that shows the original title, tags, year and body, with no outcome and images as
placeholders; they are stored in `labels/gold/` with the rubric version on every row. `labels/label_questions.py` asks
a model for the same labels, one call per question, with a schema built from the rubric's levels and a short reason per
label (the model gets the definitions only, not the discovery table of which way each label leaned), and
`labels/agreement.py` scores any two labelers per label (agreement and Cohen's kappa) and lists every disagreement.

**Practice round and reviewed gold set (decided 2026-10-31).** The 20 practice questions were labeled blind by hand and
by Claude Opus 5.5. Agreement was low (kappa 0.14 to 0.75 by label), and in most disagreements the written rubric sided
with the model, so the wording was tightened before the scoring set: an input/output pair rather than any example,
clearer asks, `failure_description` reduced to concrete / vague / not applicable, logs are not code, the setup label
judged from what the post says, and a "cover the images" test (closing note of `labels/rubric.md`). The 100 scoring
questions are then labeled by **review**, not from scratch: two models from companies whose models do not compete to
label the analysis set, Google Gemini 4 Argon and xAI Grok 4.7 (called through the Vercel AI Gateway with one key),
label every gold question with a reason per label; the hand labeler keeps or changes each level both chose and breaks
each split (`labels/gold_page.py scoring --review ...`, saved as `gold_labels_scoring_reviewed.csv` with a
`<label>__decision` column). Reviewing anchors the reviewer on the suggestion, so this gold set is human-reviewed model
labels, not independent hand labels: the share of labels changed is reported with it, and the 20 blind practice labels
remain the one independent human check. Candidate labelers for the analysis set (Claude models, OpenAI GPT-6 Luna,
TypeSafe Jev) are scored against the reviewed set. The reference runs cost US$ 2.94 for both models on all 120
questions (Opus on the practice set, US$ 0.43); on the 100 scoring questions the two agree on 567 of 600 labels
(kappa 0.76 to 0.88 per label, 0.37 on the image label, whose positives are rare), leaving 33 tie-breaks. The review is done: all 567 agreed labels were kept (none changed) and the 33 splits went 18 to
Gemini and 15 to Grok. Zero changes is the anchoring risk named above, so the reviewed set is reported as the models'
labels with a human check on the splits, next to the independent blind practice result.

**Labeler and analysis set (decided 2026-11-01).** Three candidates were scored on the 100 reviewed scoring questions
(Cohen's kappa per label: worked example, ask scope, failure, code, environment, image). TypeSafe Jev: 0.81, 0.87, 0.98,
0.74, 0.72, 0.71 (mean 0.80). GPT-6 Luna: 0.63, 0.75, 0.83, 0.57, 0.79, 0.79 (0.72). Claude Haiku 5.5: 0.94, 0.61,
0.67, 0.73, 0.78, 0.40 (0.68). The three runs cost US$ 0.12 in all; Claude Sonnet and Opus were not run. The reviewed set
started from the reference models' labels, so these scores are optimistic (see above). Jev labels the analysis set:
30,000 questions drawn at random from the 5% sample, 2018–2022, minus the discovery and gold questions
(`int_label_analysis_questions`, a view, checked by `tests/assert_label_analysis_questions.sql`), at US$ 3.82. The analysis
set is sized to a US$ 4 budget; labeling the whole sample (~422k) would cost about US$ 54 at Jev's measured US$ 0.00013
per question (an estimate before the runs, US$ 400–550, priced Haiku and Luna at an assumed 1,500 output tokens per
question; `eda/d6_labelers`). The draw is not stratified, so label rates describe the
sample as it is (image-only evidence is about 2% here against 6% in the image-oversampled gold set). Jev answers each
label with a level and its probabilities, with no reason.

Rule-based features and quality labels are not competing methods. Rule-based features cover every question and
are reproducible in `queries/q3.sql`; labels cover the sample and are stored as a table. They meet in two checks: a
label should agree with its rule-based neighbour where one exists (a "reproducible example" mostly has a code
block), and a joint view shows whether a label adds anything beyond the rules (e.g. among questions with code,
does a reproducible one do better?).

**Answer lens.** Answers are posts too. Among the answers in the sample, which qualities go with being the accepted
one (same rules and labels, original text, one row per answer). Answer text can never explain the question's answer
rate (an unanswered question has no answer), so this lens is reported separately, for acceptance only.

## Analysis models (decided and built 2026-10-31)

- **No-text features** (`int_question_posting_context`, one row per 2018–2022 question): hour and weekday posted (UTC,
  not the asker's local time), the asker's account age at posting, and the asker's earlier questions since 2008 (a
  lower bound: deleted questions are not in the data). A deleted account gives "unknown"; so does a negative age (607
  askers have an account created after their question, probably merged accounts). The "unknown" bucket is reported
  but not read as a quality: whether an account is deleted is known only later.
- **One question table** (`int_p3_questions`, a view): outcomes, original-text features, current-text features, no-text
  features, primary tag (the first original tag) and the edit flags. 30 questions with no history row are left out.
- **Buckets** (`macros/p3_features.sql`): fixed cut points, not deciles, so the original and current text of a question
  land in the same buckets. Bucket `1:` is the reference (no / zero / smallest / Monday / 00–05 UTC / first question).

  | Feature | Buckets |
  |---|---|
  | Title length | <40, 40–59, 60–79, 80+ |
  | Body length | <500, 500–999, 1,000–1,999, 2,000–3,999, 4,000+ |
  | Code blocks | 0, 1, 2, 3+ |
  | Links | 0, 1, 2+ |
  | Original tag count | 1, 2, 3, 4, 5+ |
  | Hour posted (UTC) | 00–05, 06–11, 12–17, 18–23 |
  | Weekday posted | each day, and weekday vs weekend |
  | Account age | under 1 day, 1–29 days, 1–12 months, 1–3 years, 3+ years |
  | Prior questions | 0 (first question), 1–4, 5–19, 20+ |
  | Yes/no features | no, yes |

- **Versions** (AC-3.5): `original` (the headline), `current` (current text), `never_edited` (title and body never
  edited), `not_edited_after_answer` (no title/body edit after the first answer).
- **Rates** (`mart_p3_feature_rates`): per version × feature × bucket × cohort (each year 2018–2022 and the four full
  years together), answer rate and accepted rate out of all questions, accepted among answered, Wilson bounds.
- **Effects** (`mart_p3_feature_effects`): a bucket's rate minus the reference bucket's, with the 95% margin of the
  difference. A bucket or reference below 385 questions in a cohort is not reported (the D1 floor).
  - **Stable** (AC-3.3, stricter than "two cohorts"): same sign in each full year, 2018, 2019, 2020 and 2021. 2022 is
    partial (censored) and shown, not used.
  - **Topic control**: the same difference inside each primary-tag stratum (the 20 most common primary tags, plus
    "other"), averaged with weights = the bucket's questions in the stratum; strata with fewer than 30 questions on
    either side are skipped. If the adjusted effect shrinks towards zero, the raw effect was mostly topic.
  - **Direction vs original**: each effect in the other three versions is flagged when it points the other way.
- **Leakage KPI** (`mart_p3_leakage`, AC-3.6): per year and text feature, the share of questions whose **bucket**
  differs between original and current text, the same share on never-edited questions (the format floor), and the
  difference. Buckets, not raw values: Markdown and HTML lengths differ by a few characters on every post.
- **AC-0.10 warning** (`assert_p3_original_text_stable`): an effect over 2018–2021 that points one way on the original
  text and the other way on the current text, where at least one of the two is clearly not zero.
- **Answer lens** (`mart_p3_answer_rates`): the 5% sample's answers, acceptance rate by body-feature bucket.
- **AC-3.2 / AC-3.4 check** (`assert_text_columns_read_once`): reads dbt's project graph and fails if any model other
  than the staging view and the scan model reads `posts_questions` or `post_history` straight from the source.
- Not built: a 30-day window for P3 (each comparison is within one year and stability rests on full years, so
  censoring mostly cancels out) and the optional logistic regression.

## Label analysis models (decided and built 2026-11-01)

- **Labels as data.** The 30,000 labels are a dbt seed (`seeds/quality_labels_analysis.csv`, id + rubric version + six
  labels; tests: unique ids, allowed levels, and `assert_quality_labels_match_analysis_set` = exactly the analysis set).
  A view over inline values cannot hold them (about 2 MB of SQL against BigQuery's 1 MB query limit).
- **Same method as the rule-based features**, on the labeled questions only: `int_p3_label_questions` (view) →
  `int_p3_label_bucket_counts` → `mart_p3_label_rates` → `mart_p3_label_effects` (copies of the rule-based marts on the
  label counts). Each label level is compared with the label's reference level (bucket `1:`, the first level in the
  rubric); `not_applicable` is left out. Versions: `original` (the headline; the labels judge the original text, so no
  current-text version exists), `never_edited`, `not_edited_after_answer`. Same 385 floor, same stability rule (same
  sign in each of 2018-2021), same topic control (20 largest primary tags among the labeled questions).
- **Rare levels (option A).** A level needs more than ~6% of questions to reach 385 in a single year, so rare levels
  (multiple asks, dump code, image-only evidence, no clear ask) are reported in the pooled 2018-2021 cohort only if they
  reach the floor, and `full_years_with_effect` (0 to 4) says how many full years did: below 4 their stability is **not
  assessable** (the `*_stable` flags are false for that reason, not because the effect flips). No clear ask (98
  questions in 2018-2021) is not reportable.
- **AC-3.7, label against its rule neighbour** (`mart_p3_label_vs_rules`): worked example ~ has a code block, code focus
  ~ code-block count, image-only evidence ~ has an image, setup dependence ~ has error text.
- **AC-3.8, does a label add anything beyond the rules** (`mart_p3_label_incremental`): the accepted-rate effect of each
  level overall and inside has-a-code-block x body-length strata (strata with fewer than 30 questions on either side are
  skipped; the coverage is reported).
- **First reading** (original text, 2018-2021, accepted rate, difference in points against the reference level):
  worked example yes **+17.2** (tag-adjusted +16.6, rules-adjusted +15.5, stable in all four years); setup-dependent
  yes **-14.9** (tag-adjusted -13.3, rules-adjusted -12.3, stable); partial code focus -7.1 (stable); broad ask -9.5
  (rules-adjusted -6.0; floor reached in 2 of 4 years); dump code -6.3, image-only evidence -6.5 (rules-adjusted -1.7)
  and multiple asks -3.8 are not assessable for stability; a vague failure description is about 0 (-0.1). Rules explain
  part of each effect (about 1.5 to 4.5 points), but the main ones survive; image-only evidence mostly does not.
  Labeled "yes" for image-only evidence, 46% of the questions have no image in the original text (the rule finds
  none), a label to question before the README leans on it.
- **Caveats.** The labels are one model's judgments (kappa 0.71 to 0.98 against the reviewed set); labeling errors blur
  effects towards zero, so the effects are probably understated, and the reviewed set's agreement scores are optimistic
  (see above). The answer lens by label is not built: it would need the sample's answers labeled.

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
- AC-3.7 Each quality label is reported against the rule-based feature closest to it; a label that does not line up with
  its rule neighbour is flagged.
- AC-3.8 Each label level's accepted-rate effect is reported overall and inside strata of the closest rule-based features,
  so the README says which labels add something beyond the rules; rare levels carry `full_years_with_effect` < 4.

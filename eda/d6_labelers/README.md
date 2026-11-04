# EDA — D6: which language model labels the questions

Supports the quality labels in [`specs/003`](../../specs/003-q3-post-qualities.md#quality-labels-decided-2026-10-31)
and D6 in the [decisions log](../../PLAN.md#decisions-log). P3's rules count what is easy to count (a code block, the
length); how a question is written (a worked example, a broad ask) needs a reader, so six labels from a written rubric
([`labels/rubric.md`](../../labels/rubric.md)) are judged by a language model. Models differ in price by about 100×
per token, and a model can't be scored against its own labels. This EDA puts the choice's numbers in one place: what
each model agreed with, what it cost per question, and where every dollar went.

## Run it

```bash
.venv/Scripts/python eda/d6_labelers/run_eda.py
```

Free: it reads only files already in the repo, never BigQuery and never a model API.

| Input | What |
|---|---|
| [`labels/spend_log.csv`](../../labels/spend_log.csv) | every paid call: run, model, tokens, US$ (30,572 calls) |
| [`labels/gold/`](../../labels/gold/), [`labels/output/gold/`](../../labels/output/gold/) | the gold labels and each model's labels; kappa computed with `labels/agreement.py`'s function |
| [`labels/common.py`](../../labels/common.py) | the price list the labeling script used (Sonnet's estimate) |

| Output | What |
|---|---|
| `output/summary.md` | spend by stage and route, agreement per label, cost per question and projections |
| `output/labelers.csv`, `output/spend_by_stage.csv` | the same numbers for [`presentation/eda_charts.py`](../../presentation/eda_charts.py) |

## The review page

[`gold_scoring_review.html`](gold_scoring_review.html) ([open it as a page][review-page]) is the page the 100 scoring
questions were reviewed on, written by [`labels/gold_page.py`](../../labels/gold_page.py) as it stood before the
review: each question's original text, Gemini's and Grok's labels with a reason for each, the labels both chose
filled in and the ties left open. The review itself, every kept label and every broken tie, is
[`labels/gold/gold_labels_scoring_reviewed.csv`](../../labels/gold/gold_labels_scoring_reviewed.csv). The page is a
copy of the one the script writes to the ignored `labels/.cache/` (which holds the question text); it is published here
because the text is Stack Overflow content, (c) Stack Exchange Inc. and its contributors, licensed
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), and the copy carries that line at the top. Labels
picked on the page stay in the browser; "Save CSV" downloads them.

[review-page]: https://nandodsg.github.io/stackoverflow-answerability/eda/gold_scoring_review.html

## What it found

1. **The best labeler was also the cheapest.** Against the reviewed gold set, TypeSafe Jev's mean Cohen's kappa is
   0.80, GPT-6 Luna's 0.72 and Claude Haiku 5.5's 0.68 ([agreement][s-kappa]). Jev costs US$ 0.00013 a question, Luna
   2.4× that, Haiku 6× ([cost per question][s-cost]). All three scores are optimistic: the gold set started from two
   reference models' labels, and its review changed none of the 567 they agreed on.
2. **US$ 10.65 for every model call in the project** ([by stage][s-stage]): US$ 3.35 for the discovery pass (Claude
   Opus reading 200 pairs), US$ 0.94 for the practice round, US$ 2.43 for the reference labels (Gemini and Grok on 100
   questions), US$ 0.12 to score the three candidates, US$ 3.82 to label 30,000 questions with Jev.
3. **The gateway carried the models of three other companies with one key** ([by route][s-route]): Gemini 4 Argon,
   Grok 4.7 and GPT-6 Luna through the Vercel AI Gateway, US$ 2.96 (28%). Claude went direct to Anthropic (US$ 3.86,
   paid from promotional credits; its API counts input tokens exactly, for free, before a run) and Jev direct to
   TypeSafe's API (US$ 3.83), whose choice questions return a level and its probabilities.
4. **The analysis set was a budget choice, not a necessity.** 30,000 questions were sized to a US$ 4 budget. At Jev's
   measured price the whole 5% sample (about 422,000 questions) would cost about US$ 54; the estimate made before the
   candidates ran, US$ 400–550, priced Haiku and Luna at an assumed 1,500 output tokens per question, and they wrote
   far fewer ([projections][s-cost]).
5. **A bigger model was not worth a run.** Claude Sonnet 5.5, priced on Haiku's measured tokens, would cost about
   US$ 460–730 for the same 30,000 questions, 120–190× Jev, to beat an agreement that was already 0.80. The references
   cost 74× (Gemini) and 117× (Grok) Jev per question: right for 100 questions a person reviews, not for 30,000.

[s-kappa]: output/summary.md#agreement-with-the-reviewed-gold-set
[s-cost]: output/summary.md#measured-cost-per-question-and-what-more-labels-would-cost
[s-stage]: output/summary.md#spend-by-stage
[s-route]: output/summary.md#spend-by-route

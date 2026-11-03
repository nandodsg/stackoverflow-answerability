# EDA — D1: sample size per tag and tag pair

Supports the ranking decision in [`specs/001`](../../specs/001-q1-tag-answerability.md): how to keep small tags from
topping (or bottoming) the accepted-rate lists by luck. Year: 2022 (the "current year", partial to 2022-09-25).

## Run it

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # macOS/Linux: .venv/bin/python
.venv/Scripts/python eda/d1_sample_size/run_eda.py         # add --refresh to requery BigQuery
```

Needs Google application-default credentials (`gcloud auth application-default login`) and the
`so-answerability` project for query billing (BigQuery sandbox is enough). The three queries scan about 3.4 GB in
total; `title` and `body` are never read. Results are cached in `output/`, so a rerun without `--refresh` is free.

| File | What |
|---|---|
| `sql/tag_stats.sql` | one row per tag: questions, answered, accepted, answers |
| `sql/tag_pair_size_distribution.sql` | frequency table: how many tag pairs have n questions (935K pairs, not downloaded one by one) |
| `sql/tag_pair_stats.sql` | one row per tag pair with ≥ 30 questions |
| `run_eda.py` | dry-runs and runs the SQL, then writes `output/*.png` and `output/summary.md` |
| `floor_precision.py` | follow-up on the cached tag CSV (no BigQuery): how precise is a tag's accepted rate at the floor, what does the confidence level change, how are tag sizes spread, and which tags does the floor leave out? Writes `output/09_rate_sampling_distribution.png` and `output/floor_precision.md` |

## What it found (2022)

1. **Most tags are tiny.** Tags: median 6 questions, mean 90, max 202,689 ([size histograms][h01]); tag pairs:
   median 1. At the median tag, one more accepted answer moves the accepted rate by 17 points.
2. **A few big tags hold most of the questions.** 1,162 tags (2.7%) have ≥ 385 questions and hold 76% of all
   question–tag links (a link is one question counted under one of its tags: a question with 3 tags makes 3 links);
   ≥ 100 keeps 3,442 tags and 87%. For pairs, ≥ 385 keeps 1,026 pairs and 27% of pair links; ≥ 100 keeps 5,046 pairs
   and 42% ([tag coverage chart][h03], [pair coverage chart][h04]). Half the tags (1–6 questions) hold 1.5% of the
   links; the 0.6% with 2,000+ questions hold 57% ([tag sizes table][fp4]).
3. **Unfiltered rankings are pure noise.** The top 10 and bottom 10 tags by raw accepted rate all have 1–2 questions
   (accepted rates of exactly 100% and 0%).
4. **Tags really do differ.** In the [funnel plot][h05], 82% of tags with ≥ 2,000 questions fall outside the 99.8%
   limits around the pooled accepted rate (30.2%); about 0.2% would if all tags shared one accepted rate. Below 30
   questions, only 6.7% fall outside the 95% limits (about 5% expected by chance): at that size, signal and noise
   can't be told apart.
5. **With a floor, the method barely matters.** At ≥ 385 questions, the raw accepted rate (A) and empirical-Bayes (C)
   top and bottom 10 tags share 9–10 of 10 with the Wilson lists; for pairs, 9–10 at the top and 8 at the bottom. The
   fitted empirical-Bayes prior is weak (18 "virtual questions"), because real differences between tags are large
   ([summary][sum]).

## Follow-up: how precise is the accepted rate at the floor? (`floor_precision.py`)

6. **A tag's accepted rate has a known margin.** Each question gets an accepted answer or doesn't, like a coin flip
   weighted by the tag's true accepted rate, so the accepted rate is the share of heads in n flips. Measured again, it
   would land within ±1.96 standard errors of the true accepted rate 95% of the time, with SE = √(p(1 − p) / n), and
   that band narrows as n grows. Simulated with 100,000 runs of a 385-question tag: 94.8% within ±1.96 SE, 99.0%
   within ±2.58, 99.7% within ±3 ([simulation chart][h09], [simulation table][fp1]). Finding 4 shows the real tags
   behave that way.
7. **The floor follows from the target.** The smallest n whose ±1.96 SE is at most 5 points when p = 50% (the worst
   case): (1.96 × 0.5 / 0.05)² = 384.2, so 385, the textbook poll size. The same target needs 271 questions at 90%,
   664 at 99% and 900 at 99.73% ([floors table][fp2]).
8. **The confidence level barely moves the lists; the floor does.** At the 385 floor, ranking with 99% or 99.73%
   bounds keeps 10/10 of the top tags and 9 or 8 of the bottom 10. Raising the floor to 664 or 900 with 95% bounds
   replaces 9 of the bottom 10, because tags with low accepted rates are small (9 of the bottom 10 have under 664
   questions, median 518). The floor decides which tags can be ranked; 95% is the level used by every interval in the
   project ([level vs floor tables][fp3]).
9. **The floor is about precision, not quality.** Six tags with 100–384 questions have a higher accepted rate than
   every ranked tag (67.6%) but are not ranked, led by `google-query-language` (277 questions, 89.9%). Two of them,
   `stringr` and `purrr`, were #3 and #1 in 2021 and fell under the floor in 2022 (270 and 368 questions). The lists
   answer "which tags do best among those measured to ±5 points" ([tags left out][fp5]).

**Decision (D1, [`specs/001`][spec]):** rank tags and pairs with ≥ 385 questions (±5 pt worst-case margin of error),
by the Wilson lower bound for "highest" and the upper bound for "lowest"; methods A and C are robustness checks. The
[summary][sum] shows the resulting 2022 lists for accepted rate.

[h01]: output/01_tag_size_histograms.png
[h03]: output/03_tag_cutoff_coverage.png
[h04]: output/04_pair_cutoff_coverage.png
[h05]: output/05_tag_funnel.png
[h09]: output/09_rate_sampling_distribution.png
[sum]: output/summary.md
[fp1]: output/floor_precision.md#1-the-measured-accepted-rate-of-one-tag-385-questions-simulated-again-and-again
[fp2]: output/floor_precision.md#2-the-floor-each-confidence-level-gives-for-the-same-5-point-target
[fp3]: output/floor_precision.md#3-which-move-changes-the-lists-the-wider-interval-or-the-higher-floor
[fp4]: output/floor_precision.md#4-how-tag-sizes-are-spread
[fp5]: output/floor_precision.md#5-who-the-floor-leaves-out-tags-with-100-to-384-questions-above-every-ranked-tag
[spec]: ../../specs/001-q1-tag-answerability.md

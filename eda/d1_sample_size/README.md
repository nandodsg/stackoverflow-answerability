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
| `floor_precision.py` | follow-up on the cached tag CSV (no BigQuery): how precise is a tag's accepted rate at the floor, and what does the confidence level change? Writes `output/09` and `output/floor_precision.md` |

## What it found (2022)

1. **Most tags are tiny.** Tags: median 6 questions, mean 90, max 202,689 (`01_tag_size_histograms.png`); tag
   pairs: median 1. At the median tag, one more accepted answer moves the accepted rate by 17 points.
2. **A few big tags hold most of the questions.** 1,162 tags (2.7%) have ≥ 385 questions and hold 76% of all
   question–tag links; ≥ 100 keeps 3,442 tags and 87%. For pairs, ≥ 385 keeps 1,026 pairs and 27% of pair links;
   ≥ 100 keeps 5,046 pairs and 42% (`03`, `04`).
3. **Unfiltered rankings are pure noise.** The top 10 and bottom 10 tags by raw accepted rate all have 1–2 questions
   (rates of exactly 100% and 0%).
4. **Tags really do differ.** In the funnel plot (`05_tag_funnel.png`), 82% of tags with ≥ 2,000 questions fall
   outside the 99.8% limits around the pooled rate (30.2%); about 0.2% would if all tags shared one rate. Below 30
   questions, only 6.7% fall outside the 95% limits (about 5% expected by chance): at that size, signal and noise
   can't be told apart.
5. **With a floor, the method barely matters.** At ≥ 385 questions, the raw-rate (A) and empirical-Bayes (C) top and
   bottom 10 tags share 9–10 of 10 with the Wilson lists; for pairs, 9–10 at the top and 8 at the bottom. The
   fitted empirical-Bayes prior is weak (18 "virtual questions"), because real differences between tags are large.

## Follow-up: how precise is the accepted rate at the floor? (`floor_precision.py`)

6. **A tag's accepted rate has a known margin.** Each question is a yes/no draw (accepted or not), so the accepted
   rate is a share of n draws. Measured again, it would land within ±1.96 standard errors of the true rate 95% of the
   time, with SE = √(p(1 − p) / n), and that band narrows as n grows. Simulated with 100,000 draws of a 385-question
   tag: 94.8% within ±1.96 SE, 99.0% within ±2.58, 99.7% within ±3 (`09_rate_sampling_distribution.png`,
   `output/floor_precision.md` section 1). Finding 4 shows the real tags behave that way.
7. **The floor follows from the target.** The smallest n whose ±1.96 SE is at most 5 points when p = 50% (the worst
   case): (1.96 × 0.5 / 0.05)² = 384.2, so 385, the textbook poll size. The same target needs 271 questions at 90%,
   664 at 99% and 900 at 99.73% (section 2).
8. **The confidence level barely moves the lists; the floor does.** At the 385 floor, ranking with 99% or 99.73%
   bounds keeps 10/10 of the top tags and 9 or 8 of the bottom 10. Raising the floor to 664 or 900 with 95% bounds
   replaces 9 of the bottom 10, because low-rate tags are small (9 of the bottom 10 have under 664 questions,
   median 518). The floor decides which tags can be ranked; 95% is the level used by every interval in the project.

**Decision (D1, `specs/001`):** rank tags and pairs with ≥ 385 questions (±5 pt worst-case margin of error), by the
Wilson lower bound for "highest" and the upper bound for "lowest"; methods A and C are robustness checks.
`output/summary.md` shows the resulting 2022 lists for accepted rate.

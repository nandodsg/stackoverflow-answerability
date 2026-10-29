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

## What it found (2022)

1. **Group size is nowhere near a bell curve.** Tags: median 6 questions, mean 90, sd 1,543, skewness 81, max
   202,689. Mean ± 3 sd is −4,538 … 4,717, so a cutoff of "3 sd below the mean" is negative and removes nothing.
   On a log scale the shape is closer to normal, but with a spike at n = 1 and a heavier right tail
   (`01_tag_size_histograms.png`). Tag pairs are even more skewed: median 1, skewness 182.
2. **A few big tags hold most of the questions.** 897 tags (2.1%) have ≥ 500 questions and hold 73% of all
   question–tag links; ≥ 100 keeps 3,442 tags and 87%. For pairs, ≥ 100 keeps 5,046 pairs and 42%
   (`03`, `04`).
3. **Unfiltered rankings are pure noise.** The top 10 and bottom 10 tags by raw accepted rate all have 1–2 questions
   (rates of exactly 100% and 0%).
4. **Tags really do differ.** In the funnel plot (`05_tag_funnel.png`), 82% of tags with ≥ 2,000 questions fall
   outside the 99.8% limits around the pooled rate (30.2%); about 0.2% would if all tags shared one rate. Below 30
   questions, only 6.7% fall outside the 95% limits (about 5% expected by chance): at that size, signal and noise
   can't be told apart.
5. **With a 500-question floor, the method barely matters.** Top 10 by raw rate vs Wilson lower bound: 9 of 10 tags
   in common; raw vs empirical Bayes: 10 of 10. Without a floor, Wilson and empirical Bayes both produce sensible
   lists that include mid-size tags (e.g. `google-query-language`, 277 questions, 90% accepted). The fitted
   empirical-Bayes prior is weak (18 "virtual questions"), because real differences between tags are large.

Decision: pending — see `specs/001`.

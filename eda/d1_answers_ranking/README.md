# EDA — D1: ranking answers per question

Supports the answers-per-question ranking rule in [`specs/001`](../../specs/001-q1-tag-answerability.md). D1 ranks
rates (answer rate, accepted rate) with a 385-question floor and Wilson bounds. Answers per question is a **mean** of
`answer_count`, not a yes/no rate, so Wilson does not apply; its interval is mean ± 1.96 × SE (D3,
[`specs/000`](../../specs/000-shared-definitions.md)). This EDA compares three rules for ranking it, all with the same
floor, and asks what a heavier rule would buy. Year: 2022 (partial, to 2022-09-25).

| Rule | "Highest" sorted by | "Lowest" sorted by |
|---|---|---|
| **Bounds (chosen)** | lower bound of mean ± 1.96 × SE | upper bound |
| Raw mean | the mean | the mean |
| Bootstrap | lower bound of a 95% percentile bootstrap interval (no normal approximation) | upper bound |

The empirical-Bayes mean, which D1 keeps as a robustness check, is compared too.

## Run it

```bash
.venv/Scripts/python eda/d1_answers_ranking/run_eda.py              # add --refresh to requery BigQuery
```

Same setup as [`d1_sample_size`](../d1_sample_size/README.md). The four queries scan about 4.4 GB in total; `title`
and `body` are never read.

| File | What |
|---|---|
| `sql/tag_answer_moments.sql` | one row per tag with ≥ 30 questions: n, answered, Σ answer_count, Σ answer_count², Σ answer_count³, max |
| `sql/tag_pair_answer_moments.sql` | the same per tag pair |
| `sql/tag_answer_distribution.sql` | one row per (tag, answer_count) for tags with ≥ 385 questions: the frequency table a bootstrap resamples |
| `sql/tag_pair_answer_distribution.sql` | the same per tag pair |
| `run_eda.py` | bounds, skewness and Cochran's rule; bootstrap intervals; coverage simulation; ranking overlap; writes `output/summary.md` |

## What it found (2022)

1. **The interval is tight at the floor.** Median 95% half-width ±0.05 answers per question for tags (p90 ±0.07, worst
   ±0.11) and ±0.06 for pairs, on values from 0.3 to 2.5. For this metric the floor is not the binding constraint; the
   rates set it.
2. **The normal approximation holds.** `answer_count` is skewed (median skewness ~1), but Cochran's rule
   (n > 25 × skewness²) fails for only 6 of 1,162 tags and 8 of 1,026 pairs, each driven by one viral question
   (`ios + xcode`: one question with 37 answers). None of them is in a top or bottom 10. A simulation that takes each
   group's own distribution as the truth shows mean ± 1.96 × SE covering the true mean 95% of the time for the median
   group; the lowest reach 92–93%, and the groups failing Cochran's rule cover 92–94%: slightly overconfident, by a
   few points, and only mid-table.
3. **The three rules give the same lists.** Against the bounds' top and bottom 10: bootstrap 10/10 and 9/10 for tags,
   10/10 and 9/10 for pairs; raw mean 9/10 for tags, 9–10/10 for pairs; empirical Bayes 9–10/10. Rank correlation with
   the lower bound over every ranked group: 0.995–1.000. The bootstrap bounds sit a median 0.002 answers per question
   from mean ± 1.96 × SE (3.5% of the half-width), at most 0.016.
4. **The heavier rules cost more than they change.**
   - Bootstrap: as a dbt model on BigQuery it is either a SQL row explosion (2,000 resamples × 2.9M question–tag links
     = 5.8B rows for tags alone) or a Python model, which runs on Dataproc and needs a billing account, so not in the
     BigQuery sandbox this project uses. BigQuery's `RAND()` takes no seed, so results would change on every build and
     tests could not pin them. Here it runs in 1.7 s only because the counts were pre-aggregated outside dbt.
   - Empirical Bayes: a second model to fit the prior on every group with ≥ 30 questions, and results that move when
     that set moves; it also needs a paragraph on "virtual questions" for the reader. It stays a one-line check.
   - Bounds: n, Σx and Σx² from the same `GROUP BY` as the raw mean, deterministic, unit-testable by hand.
5. **Why bounds over the raw mean, when the lists are almost the same:** one rule for every P1 metric (a group ranks
   high only if its value is high *and* well measured), so a reader learns it once; and the raw mean has no guard if a
   later year brings a tag near the floor with a few viral questions.
6. **"Most answers" is not "most often answered".** The answer-rate ranking shares only 6 of the top 10 tags and 4 of
   the top 10 pairs: `awk` (2.45) and `sed` (2.19) lead because each question collects several answers. At the bottom
   the two agree (8–9 of 10). This supports D3: answers per question and answer rate are both shown.

**Decision:** bounds, with the 385 floor; raw mean and empirical Bayes as one-line robustness checks; every ranked row
carries the Cochran flag, and a flagged row in a top or bottom 10 is labeled "interval approximate" (none in 2022).

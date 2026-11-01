# Stack Overflow answerability

What makes a Stack Overflow question get answered, and get an accepted answer? Analysis of the
[`bigquery-public-data.stackoverflow`](https://console.cloud.google.com/marketplace/product/stack-exchange/stack-overflow)
dataset.

> Work in progress. Results land here first; method and limits follow each answer.

## Read this first

The public snapshot ends on **2022-09-25**. "Current year" in this analysis means **2022** (partial year). Details in
[`specs/000`](specs/000-shared-definitions.md).

## 1. Which tags get the most answers and accepted answers?

Sort every 2022 tag by accepted rate and the top 10 is ten tags with one or two questions each, all at 100%. The bottom
10 is the same story at 0%. So before any list, a rule for "enough questions to believe the rate"
([`eda/d1_sample_size`](eda/d1_sample_size/README.md)).

### The short answer

In 2022 the tags whose questions get answered and accepted are **text processing and data wrangling**: `jq`, `awk`,
`sed`, `regex`, R's `dplyr` / `tidyr` / `data.table`, `pandas-groupby`. Between 58% and 68% of their questions end with
an accepted answer, and `awk` and `sed` collect more than two answers per question. At the other end sit
**platforms and integrations**: `magento2`, `appium`, `facebook` and its Graph API, `ckeditor`, `elementor`, Chrome
extensions, `webview`, `cpanel`, `usb`. About one in ten of their questions gets an accepted answer, and most of them
never get any answer at all. For comparison, the whole of 2022 sits at **30.5%** (386,683 accepted out of 1,268,788
questions). Tag pairs tell the same story: R and pandas pairs, `jq + json` and `awk + bash` on top; Android, Chrome
extensions, WordPress plugins and websockets at the bottom.

My reading of the pattern (association, not cause): the tags on top are about small, self-contained problems where the
asker can paste an input and the expected output, someone can test an answer in a minute, and the asker can tell when it
worked. The tags at the bottom depend on an environment the person answering doesn't have (a store, an app review, a
browser build, a device on a USB port). P3 looks at this kind of question quality directly, without tags.

### How I measured it

- **Population**: questions created in 2022, the latest year in the snapshot (2022-01-01 to 2022-09-25, so a partial
  year). Tags are the tags each question has today.
- **Accepted rate** = questions with an accepted answer / **all** questions in the group. It is the ranking metric for
  "highest rate of approved answers". Two columns sit beside it so each row tells *why* it is high or low: **answer
  rate** (answered / all questions) and **accepted among answered** (accepted / answered). They multiply back:
  accepted rate = answer rate × accepted among answered.
- **Answers per question** = total answers / total questions in the group. It is my reading of "most answers"; the plain
  total of answers mostly measures how popular a tag is.
- **Floor: 385 questions** in the year. 385 is the smallest sample whose worst-case 95% margin of error is ±5 points.
  It leaves 1,162 tags and 1,026 tag pairs in 2022 (2.7% of the tags, but 76% of the question–tag links).
- **Ranking by the interval, not by the rate.** Each group gets a 95% interval (Wilson for the two rates, mean ±
  1.96 × standard error for answers per question). "Highest" lists sort by the **lower** bound, "lowest" lists by the
  **upper** bound, so a group only makes a list if it is high (or low) *and* well measured. That's why `jq` (67.6%,
  824 questions) ranks above `tidyr` (66.5%, 412 questions) even though their rates are close.
- **Combinations** are unordered tag pairs: a question tagged `r|dplyr|tidyverse` counts for `dplyr + r`,
  `dplyr + tidyverse` and `r + tidyverse`. Same floor, same rules.
- **Tag exposure** is the share of the group's questions whose tags were first edited *after* the first answer arrived
  (more on it below).

### Single tags, 2022

_Highest accepted rate_

| # | Tag | Questions | Accepted rate (95% interval) | Answer rate | Accepted among answered | Tag exposure |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `jq` | 824 | 67.6% (64.3–70.7) | 97.3% | 69.5% | 19.2% |
| 2 | `awk` | 1,266 | 66.0% (63.4–68.6) | 95.3% | 69.3% | 14.5% |
| 3 | `data.table` | 696 | 66.5% (62.9–69.9) | 87.5% | 76.0% | 9.6% |
| 4 | `dplyr` | 4,093 | 64.2% (62.7–65.6) | 89.8% | 71.4% | 10.3% |
| 5 | `tidyr` | 412 | 66.5% (61.8–70.9) | 87.6% | 75.9% | 14.6% |
| 6 | `tidyverse` | 1,409 | 61.7% (59.1–64.2) | 85.1% | 72.5% | 6.9% |
| 7 | `pandas-groupby` | 997 | 62.1% (59.0–65.0) | 85.0% | 73.1% | 16.8% |
| 8 | `data-manipulation` | 476 | 63.4% (59.0–67.6) | 85.5% | 74.2% | 13.0% |
| 9 | `sed` | 1,085 | 61.8% (58.9–64.7) | 93.6% | 66.0% | 16.4% |
| 10 | `regex` | 7,394 | 58.5% (57.4–59.6) | 87.4% | 66.9% | 11.2% |

_Lowest accepted rate_

| # | Tag | Questions | Accepted rate (95% interval) | Answer rate | Accepted among answered | Tag exposure |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `magento2` | 488 | 8.6% (6.4–11.4) | 41.2% | 20.9% | 0.6% |
| 2 | `appium` | 588 | 9.5% (7.4–12.2) | 40.5% | 23.5% | 0.3% |
| 3 | `facebook` | 962 | 10.2% (8.4–12.3) | 27.2% | 37.4% | 0.7% |
| 4 | `ckeditor` | 414 | 9.4% (7.0–12.6) | 27.8% | 33.9% | 0.5% |
| 5 | `elementor` | 557 | 10.1% (7.8–12.8) | 47.2% | 21.3% | 1.6% |
| 6 | `facebook-graph-api` | 548 | 10.4% (8.1–13.2) | 26.8% | 38.8% | 1.3% |
| 7 | `cpanel` | 422 | 10.2% (7.7–13.4) | 37.2% | 27.4% | 2.6% |
| 8 | `usb` | 387 | 10.3% (7.7–13.8) | 35.7% | 29.0% | 1.8% |
| 9 | `object-detection` | 618 | 11.2% (8.9–13.9) | 36.6% | 30.5% | 3.1% |
| 10 | `tableau-desktop` | 404 | 10.9% (8.2–14.3) | 42.8% | 25.4% | 0.2% |

The two side columns split the bottom in two kinds of trouble. `facebook`, `ckeditor` and the Graph API are mostly
**not answered** (about 27% answer rate; when they are, more than a third get accepted). `magento2`, `appium` and
`elementor` get answered more often (40–47%) but **rarely accepted** (21–24% of the answered ones). Different
problems, same rank (sorry, `magento2`).

_Most answers per question_

| # | Tag | Questions | Answers per question (95% interval) | Answer rate | Tag exposure |
|---:|---|---:|---:|---:|---:|
| 1 | `awk` | 1,266 | 2.45 (2.37–2.54) | 95.3% | 14.5% |
| 2 | `sed` | 1,085 | 2.19 (2.10–2.28) | 93.6% | 16.4% |
| 3 | `grep` | 643 | 1.79 (1.68–1.90) | 85.8% | 15.6% |
| 4 | `java-stream` | 820 | 1.70 (1.62–1.78) | 91.3% | 37.1% |
| 5 | `list-comprehension` | 491 | 1.69 (1.59–1.79) | 91.0% | 10.8% |
| 6 | `list` | 10,067 | 1.52 (1.50–1.54) | 84.2% | 8.7% |
| 7 | `dplyr` | 4,093 | 1.49 (1.46–1.52) | 89.8% | 10.3% |
| 8 | `data.table` | 696 | 1.53 (1.45–1.61) | 87.5% | 9.6% |
| 9 | `jq` | 824 | 1.49 (1.43–1.54) | 97.3% | 19.2% |
| 10 | `split` | 1,304 | 1.50 (1.43–1.56) | 84.7% | 12.8% |

_Fewest answers per question_

| # | Tag | Questions | Answers per question (95% interval) | Answer rate | Tag exposure |
|---:|---|---:|---:|---:|---:|
| 1 | `facebook-graph-api` | 548 | 0.31 (0.26–0.35) | 26.8% | 1.3% |
| 2 | `facebook` | 962 | 0.32 (0.29–0.36) | 27.2% | 0.7% |
| 3 | `ckeditor` | 414 | 0.31 (0.26–0.36) | 27.8% | 0.5% |
| 4 | `chrome-extension-manifest-v3` | 423 | 0.33 (0.28–0.38) | 30.0% | 1.9% |
| 5 | `google-chrome-extension` | 2,032 | 0.37 (0.34–0.39) | 32.1% | 1.3% |
| 6 | `soap` | 832 | 0.37 (0.33–0.41) | 33.7% | 1.2% |
| 7 | `proxy` | 1,206 | 0.39 (0.36–0.42) | 34.8% | 1.2% |
| 8 | `webview` | 993 | 0.41 (0.37–0.45) | 34.1% | 0.9% |
| 9 | `usb` | 387 | 0.39 (0.34–0.45) | 35.7% | 1.8% |
| 10 | `reverse-proxy` | 484 | 0.40 (0.35–0.45) | 35.7% | 1.0% |

The answer-rate lists (in [`queries/q1.sql`](queries/q1.sql)) add one useful case: `jmeter` has the second-highest
answer rate (96.0%) but only 31.6% accepted, a tag where almost everything gets a reply and few replies get the tick.

### Tag pairs, 2022

The same rules on pairs. Short version: R and pandas pairs plus `jq + json` and `awk + bash` on top; Android, Chrome
extensions, WordPress and websockets at the bottom. `arrays + google-sheets` leads with 85.8%, but read the edits
section before quoting it.

<details>
<summary>The four pair tables</summary>

_Highest accepted rate_

| # | Pair | Questions | Accepted rate (95% interval) | Answer rate | Accepted among answered | Tag exposure |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `arrays + google-sheets` | 400 | 85.8% (82.0–88.8) | 96.8% | 88.6% | 64.0% |
| 2 | `dataframe + dplyr` | 645 | 72.7% (69.1–76.0) | 94.6% | 76.9% | 21.2% |
| 3 | `jq + json` | 518 | 68.7% (64.6–72.6) | 96.9% | 70.9% | 25.3% |
| 4 | `dplyr + tidyverse` | 515 | 68.0% (63.8–71.8) | 91.8% | 74.0% | 9.1% |
| 5 | `data.table + r` | 680 | 67.2% (63.6–70.6) | 87.9% | 76.4% | 9.9% |
| 6 | `dplyr + r` | 3,963 | 64.7% (63.2–66.2) | 90.1% | 71.9% | 10.5% |
| 7 | `r + tidyr` | 398 | 67.8% (63.1–72.2) | 88.4% | 76.7% | 15.1% |
| 8 | `regex + string` | 461 | 67.5% (63.1–71.6) | 93.1% | 72.5% | 17.4% |
| 9 | `dataframe + pandas-groupby` | 576 | 66.5% (62.5–70.2) | 88.9% | 74.8% | 24.0% |
| 10 | `awk + bash` | 514 | 66.0% (61.8–69.9) | 95.5% | 69.0% | 15.0% |

_Lowest accepted rate_

| # | Pair | Questions | Accepted rate (95% interval) | Answer rate | Accepted among answered | Tag exposure |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `android + webview` | 485 | 9.9% (7.5–12.9) | 30.9% | 32.0% | 1.2% |
| 2 | `google-chrome + google-chrome-extension` | 477 | 10.3% (7.9–13.3) | 27.0% | 38.0% | 0.8% |
| 3 | `elementor + wordpress` | 442 | 11.5% (8.9–14.9) | 48.9% | 23.6% | 1.4% |
| 4 | `android + python` | 387 | 11.6% (8.8–15.2) | 35.4% | 32.8% | 1.6% |
| 5 | `plugins + wordpress` | 399 | 11.8% (9.0–15.3) | 33.6% | 35.1% | 0.5% |
| 6 | `amazon-web-services + aws-amplify` | 406 | 12.6% (9.7–16.1) | 43.1% | 29.1% | 1.2% |
| 7 | `android + unity3d` | 445 | 12.8% (10.0–16.2) | 44.7% | 28.6% | 1.1% |
| 8 | `google-chrome-extension + javascript` | 1,151 | 14.2% (12.3–16.4) | 34.6% | 41.2% | 1.3% |
| 9 | `ios + javascript` | 484 | 13.2% (10.5–16.5) | 38.0% | 34.8% | 0.4% |
| 10 | `android + react-native` | 2,274 | 15.1% (13.7–16.7) | 44.1% | 34.3% | 1.3% |

_Most answers per question_

| # | Pair | Questions | Answers per question (95% interval) | Answer rate | Tag exposure |
|---:|---|---:|---:|---:|---:|
| 1 | `awk + bash` | 514 | 2.59 (2.44–2.73) | 95.5% | 15.0% |
| 2 | `bash + sed` | 503 | 2.32 (2.18–2.46) | 94.4% | 13.5% |
| 3 | `list + string` | 557 | 1.88 (1.77–1.99) | 91.2% | 11.1% |
| 4 | `java + java-stream` | 754 | 1.77 (1.69–1.85) | 93.2% | 39.9% |
| 5 | `r + string` | 532 | 1.79 (1.68–1.90) | 89.3% | 18.0% |
| 6 | `list + python` | 6,336 | 1.69 (1.66–1.72) | 87.9% | 8.6% |
| 7 | `list-comprehension + python` | 413 | 1.77 (1.66–1.88) | 91.5% | 11.4% |
| 8 | `dictionary + list` | 1,187 | 1.72 (1.66–1.79) | 90.6% | 9.3% |
| 9 | `regex + string` | 461 | 1.75 (1.65–1.86) | 93.1% | 17.4% |
| 10 | `dataframe + dplyr` | 645 | 1.71 (1.63–1.79) | 94.6% | 21.2% |

_Fewest answers per question_

| # | Pair | Questions | Answers per question (95% interval) | Answer rate | Tag exposure |
|---:|---|---:|---:|---:|---:|
| 1 | `google-chrome + google-chrome-extension` | 477 | 0.30 (0.25–0.34) | 27.0% | 0.8% |
| 2 | `android + webview` | 485 | 0.36 (0.31–0.42) | 30.9% | 1.2% |
| 3 | `google-chrome-extension + javascript` | 1,151 | 0.40 (0.36–0.43) | 34.6% | 1.3% |
| 4 | `plugins + wordpress` | 399 | 0.38 (0.33–0.44) | 33.6% | 0.5% |
| 5 | `python + websocket` | 463 | 0.39 (0.34–0.45) | 35.2% | 1.1% |
| 6 | `android + python` | 387 | 0.39 (0.34–0.45) | 35.4% | 1.6% |
| 7 | `amazon-cognito + amazon-web-services` | 455 | 0.42 (0.37–0.48) | 37.6% | 1.1% |
| 8 | `node.js + websocket` | 397 | 0.43 (0.37–0.48) | 37.8% | 0.3% |
| 9 | `google-chrome + javascript` | 955 | 0.46 (0.41–0.50) | 36.8% | 1.5% |
| 10 | `nginx + nginx-reverse-proxy` | 440 | 0.45 (0.40–0.50) | 40.7% | 1.4% |

</details>

### How sure can we be about these lists?

- **Every list is sorted by a 95% interval**, shown on every row. For answers per question the interval assumes the
  mean is close to normal, which a skewed count like answers can break. Each row carries a flag for that (Cochran's
  rule, n > 25 × skewness²): it fails for 6 tags and 8 pairs in 2022, all in the middle of the table. **No flagged row
  lands in any top or bottom 10**, so none of the rows above needs the "interval approximate" label.
- **Two other ranking methods agree.** Ranking by the raw rate (same floor) and by an empirical-Bayes rate, which pulls
  small groups toward the average, give almost the same accepted-rate lists: 9 of 10 at the top and 10 of 10 at the
  bottom for tags; 9–10 of 10 at the top and 8 of 10 at the bottom for pairs. For answers per question a bootstrap
  interval changed nothing either ([`eda/d1_answers_ranking`](eda/d1_answers_ranking/README.md)).
- **2021 as a check year.** Of the 2022 top 10 tags by accepted rate, 8 were also in the 2021 top 10; at the bottom, 4.
  Pairs move more (3 of 10 at the top, 6 at the bottom), which is expected: a pair near the 385 floor drifts in and out
  of the ranked set. No tag or pair jumps from a top 10 to a bottom 10 between the years. Two 2021 leaders, `purrr` and
  `stringr`, vanish from 2022 because they fell under the floor, not because their rate dropped.
- **Time to collect answers (censoring).** A question from late September 2022 had days, not months, to get answered.
  Counting only answers that arrived within 30 days, on questions old enough to have had those 30 days, keeps 1,020 of
  the 1,162 tags; 9 of the top 10 and 6 of the bottom 10 by accepted rate stay the same (answers per question: 9 and 7).

### Do tag edits change the lists?

Tags get edited, and sometimes the edit comes after the answer: someone answers a question about filtering rows, then
adds `dplyr` because that's what the answer used. Read naively, the tag "led to" the answer, when the answer led to the
tag. That is what **tag exposure** measures, and it sits right where the headline is: the median ranked tag has 3.7%,
but the top 10 by accepted rate has 7–19% (`jq`: 19.2%), while the bottom 10 stays at or under 3.1%. `webdriverwait` is the
extreme case at 62%, a tag mostly added by the people answering.

To size the effect, the dbt project rebuilds every 2022 ranking on the **original** tags (the version the asker posted,
from `post_history`) and a `warn` test lists every tag or pair that enters or leaves a top / bottom 10, or whose accepted
rate moves by more than 2.5 points (half of the ±5-point precision target). Result: **46 tags and 65 pairs**.

- **Tags: 9 of 10 stay in both accepted-rate lists.** `tidyr` (#5) has fewer than 385 questions on the original tags:
  a good part of its questions got the tag later. `java-stream` takes its place. At the bottom, `usb` (#8) drops under
  the floor and `video-streaming` comes in. The largest moves are mid-table: `macros` 46.4% → 32.2%, `cuda` 45.5% →
  32.1%.
- **Pairs: 7 of 10 stay at the top, 8 of 10 at the bottom.** The #1 pair, `arrays + google-sheets` (85.8%, exposure
  64%), has fewer than 385 questions on the original tags, so **I wouldn't quote it as a finding**: most of that pair is
  made by retagging after an answer. `r + tidyr` goes the same way.

The single-tag answer above holds on the original tags; the pair list is softer at the top.

<details>
<summary>Every warning of the original-tags check (46 tags, 65 pairs)</summary>

**Single tags: 46 warnings**

| Tag | Why | Accepted rate, current tags | Accepted rate, original tags | Tag exposure |
|---|---|---:|---:|---:|
| `video-streaming` | bottom 10 changes (rank 13 → 8) | 11.5% | 11.0% | 0.8% |
| `java-stream` | top 10 changes (rank 11 → 10) | 59.8% | 59.3% | 37.1% |
| `tidyr` | top 10 changes (below the floor on original tags) | 66.5% | n/a | 14.6% |
| `usb` | bottom 10 changes (below the floor on original tags) | 10.3% | n/a | 1.8% |
| `macros` | moves > 2.5 pt | 46.4% | 32.2% | 4.7% |
| `cuda` | moves > 2.5 pt | 45.5% | 32.1% | 5.4% |
| `rstudio` | moves > 2.5 pt | 19.4% | 25.8% | 2.1% |
| `lambda` | moves > 2.5 pt | 46.4% | 40.4% | 7.3% |
| `vim` | moves > 2.5 pt | 39.2% | 33.3% | 5.9% |
| `match` | moves > 2.5 pt | 51.3% | 45.5% | 15.8% |
| `sum` | moves > 2.5 pt | 50.7% | 44.9% | 16.4% |
| `url-rewriting` | moves > 2.5 pt | 30.0% | 24.4% | 14.1% |
| `google-sheets-api` | moves > 2.5 pt | 39.8% | 34.3% | 20.7% |
| `gatsby` | moves > 2.5 pt | 39.7% | 34.4% | 7.1% |
| `sql-update` | moves > 2.5 pt | 43.9% | 38.8% | 20.0% |
| `ssms` | moves > 2.5 pt | 23.5% | 28.5% | 7.1% |
| `tradingview-api` | moves > 2.5 pt | 12.6% | 17.2% | 0.9% |
| `count` | moves > 2.5 pt | 51.3% | 46.8% | 15.1% |
| `django-queryset` | moves > 2.5 pt | 41.4% | 36.9% | 14.3% |
| `apache-spark-sql` | moves > 2.5 pt | 37.7% | 33.3% | 19.5% |
| `css-selectors` | moves > 2.5 pt | 46.1% | 41.8% | 31.6% |
| `aggregation-framework` | moves > 2.5 pt | 52.3% | 48.2% | 16.3% |
| `stream` | moves > 2.5 pt | 28.2% | 32.2% | 3.6% |
| `oracle-sqldeveloper` | moves > 2.5 pt | 30.1% | 34.0% | 8.0% |
| `flutter-layout` | moves > 2.5 pt | 39.1% | 35.5% | 13.1% |
| `max` | moves > 2.5 pt | 52.4% | 48.8% | 15.3% |
| `opengl` | moves > 2.5 pt | 38.6% | 35.0% | 9.4% |
| `angularjs` | moves > 2.5 pt | 16.1% | 19.6% | 2.0% |
| `asp.net-core-mvc` | moves > 2.5 pt | 37.2% | 33.8% | 12.2% |
| `extract` | moves > 2.5 pt | 39.1% | 35.7% | 9.7% |
| `apache` | moves > 2.5 pt | 20.7% | 17.3% | 8.1% |
| `google-oauth` | moves > 2.5 pt | 24.8% | 21.6% | 15.8% |
| `group-by` | moves > 2.5 pt | 55.5% | 52.3% | 14.0% |
| `slice` | moves > 2.5 pt | 49.7% | 46.6% | 12.8% |
| `case` | moves > 2.5 pt | 46.1% | 43.2% | 13.3% |
| `apache-spark` | moves > 2.5 pt | 28.1% | 25.2% | 11.5% |
| `kql` | moves > 2.5 pt | 60.3% | 57.4% | 6.8% |
| `web-applications` | moves > 2.5 pt | 20.5% | 17.7% | 7.1% |
| `react-router-dom` | moves > 2.5 pt | 46.1% | 43.3% | 19.5% |
| `tensor` | moves > 2.5 pt | 40.2% | 37.5% | 10.9% |
| `filter` | moves > 2.5 pt | 42.3% | 39.6% | 9.1% |
| `etl` | moves > 2.5 pt | 22.0% | 19.3% | 9.7% |
| `cors` | moves > 2.5 pt | 30.0% | 27.4% | 5.9% |
| `query-optimization` | moves > 2.5 pt | 33.8% | 31.2% | 11.2% |
| `json.net` | moves > 2.5 pt | 47.3% | 44.8% | 14.0% |
| `xpath` | moves > 2.5 pt | 49.6% | 47.1% | 26.0% |

**Tag pairs: 65 warnings**

| Pair | Why | Accepted rate, current tags | Accepted rate, original tags | Tag exposure |
|---|---|---:|---:|---:|
| `dataframe + pandas-groupby` | top 10 changes (rank 9 → 12) | 66.5% | 63.4% | 24.0% |
| `ios + javascript` | bottom 10 changes (rank 9 → 11) | 13.2% | 13.8% | 0.4% |
| `python + regex` | top 10 changes (rank 13 → 8) | 62.9% | 63.4% | 10.4% |
| `list + r` | top 10 changes (rank 16 → 10) | 62.5% | 62.9% | 9.0% |
| `r + tidyverse` | top 10 changes (rank 15 → 9) | 62.3% | 62.1% | 7.1% |
| `heroku + reactjs` | bottom 10 changes (rank 12 → 9) | 13.4% | 13.5% | 2.2% |
| `reactjs + webpack` | bottom 10 changes (rank 13 → 10) | 14.9% | 15.0% | 1.8% |
| `android + python` | bottom 10 changes (below the floor on original tags) | 11.6% | n/a | 1.6% |
| `arrays + google-sheets` | top 10 changes (below the floor on original tags) | 85.8% | n/a | 64.0% |
| `r + tidyr` | top 10 changes (below the floor on original tags) | 67.8% | n/a | 15.1% |
| `apache-spark + apache-spark-sql` | moves > 2.5 pt | 39.2% | 29.6% | 26.3% |
| `.htaccess + apache` | moves > 2.5 pt | 45.5% | 37.0% | 29.6% |
| `django-templates + python` | moves > 2.5 pt | 46.7% | 39.1% | 23.6% |
| `dataframe + pyspark` | moves > 2.5 pt | 47.5% | 41.4% | 27.2% |
| `apache-spark-sql + pyspark` | moves > 2.5 pt | 43.2% | 37.2% | 24.5% |
| `apache-spark + pyspark` | moves > 2.5 pt | 34.5% | 28.8% | 18.0% |
| `django-views + python` | moves > 2.5 pt | 45.2% | 39.6% | 19.2% |
| `dart + flutter-layout` | moves > 2.5 pt | 43.5% | 38.2% | 21.0% |
| `arrays + filter` | moves > 2.5 pt | 54.8% | 49.6% | 13.9% |
| `javascript + vuejs2` | moves > 2.5 pt | 42.3% | 37.2% | 15.3% |
| `apache-spark + python` | moves > 2.5 pt | 35.7% | 30.8% | 16.3% |
| `amazon-web-services + terraform` | moves > 2.5 pt | 41.8% | 36.9% | 19.6% |
| `google-cloud-firestore + javascript` | moves > 2.5 pt | 42.7% | 38.0% | 16.8% |
| `javascript + react-router-dom` | moves > 2.5 pt | 45.8% | 41.2% | 25.4% |
| `django-templates + django-views` | moves > 2.5 pt | 42.9% | 38.3% | 14.2% |
| `django-models + django-templates` | moves > 2.5 pt | 43.4% | 39.0% | 12.8% |
| `react-router + react-router-dom` | moves > 2.5 pt | 50.6% | 46.3% | 26.1% |
| `django + django-queryset` | moves > 2.5 pt | 42.7% | 38.3% | 15.1% |
| `firebase + java` | moves > 2.5 pt | 31.0% | 26.9% | 20.0% |
| `json + sql` | moves > 2.5 pt | 46.2% | 42.1% | 11.4% |
| `aggregation-framework + mongodb` | moves > 2.5 pt | 52.4% | 48.3% | 16.5% |
| `amazon-cloudformation + amazon-web-services` | moves > 2.5 pt | 38.8% | 34.7% | 12.8% |
| `django-models + python` | moves > 2.5 pt | 40.7% | 36.7% | 14.9% |
| `javascript + vuejs3` | moves > 2.5 pt | 41.7% | 37.9% | 13.9% |
| `flutter + flutter-layout` | moves > 2.5 pt | 39.6% | 35.9% | 13.3% |
| `lambda + python` | moves > 2.5 pt | 48.6% | 44.9% | 5.5% |
| `azure + terraform` | moves > 2.5 pt | 41.0% | 37.3% | 12.3% |
| `keras + machine-learning` | moves > 2.5 pt | 26.3% | 22.7% | 8.1% |
| `vue.js + vuejs3` | moves > 2.5 pt | 40.8% | 37.3% | 13.3% |
| `selenium + xpath` | moves > 2.5 pt | 53.2% | 49.8% | 42.6% |
| `vue.js + vuejs2` | moves > 2.5 pt | 39.0% | 35.7% | 11.8% |
| `tensorflow + tensorflow2.0` | moves > 2.5 pt | 32.2% | 29.0% | 13.7% |
| `keras + python` | moves > 2.5 pt | 29.2% | 25.9% | 7.9% |
| `firebase + kotlin` | moves > 2.5 pt | 33.1% | 29.9% | 18.2% |
| `firebase + javascript` | moves > 2.5 pt | 35.5% | 32.3% | 12.6% |
| `algorithm + arrays` | moves > 2.5 pt | 50.9% | 47.8% | 14.5% |
| `django-forms + django-views` | moves > 2.5 pt | 38.4% | 35.3% | 7.3% |
| `wpf + xaml` | moves > 2.5 pt | 44.4% | 41.3% | 14.1% |
| `javascript + string` | moves > 2.5 pt | 47.3% | 44.3% | 10.3% |
| `dataframe + dplyr` | moves > 2.5 pt | 72.7% | 69.7% | 21.2% |
| `sql + stored-procedures` | moves > 2.5 pt | 33.5% | 30.5% | 7.7% |
| `java + list` | moves > 2.5 pt | 46.9% | 44.0% | 26.3% |
| `react-router-dom + reactjs` | moves > 2.5 pt | 47.0% | 44.1% | 20.0% |
| `date + r` | moves > 2.5 pt | 56.1% | 59.0% | 8.6% |
| `asp.net-core-webapi + c#` | moves > 2.5 pt | 36.8% | 34.0% | 9.1% |
| `django-models + django-views` | moves > 2.5 pt | 41.8% | 39.0% | 11.1% |
| `pandas-groupby + python` | moves > 2.5 pt | 64.0% | 61.2% | 20.4% |
| `amazon-ecs + amazon-web-services` | moves > 2.5 pt | 32.4% | 29.7% | 5.6% |
| `discord + node.js` | moves > 2.5 pt | 40.1% | 37.5% | 9.7% |
| `html + web` | moves > 2.5 pt | 24.7% | 27.3% | 1.4% |
| `java + javascript` | moves > 2.5 pt | 20.1% | 22.7% | 4.3% |
| `join + sql` | moves > 2.5 pt | 53.4% | 50.9% | 16.3% |
| `jupyter-notebook + pandas` | moves > 2.5 pt | 33.3% | 35.9% | 3.1% |
| `android-studio + java` | moves > 2.5 pt | 18.2% | 20.7% | 1.6% |
| `android + firebase` | moves > 2.5 pt | 25.7% | 23.2% | 13.3% |

</details>

### Assumptions and limitations

- **"Lead to" is read as association.** A tag is a label for a kind of problem; this does not show that adding `jq` to
  a question would get it answered.
- **A question counts once for each of its tags**, so lists overlap: most `dplyr` questions are also `r` questions, and
  `dplyr + r` is close to `dplyr`.
- **2022 is partial** (to 09-25) and its newest questions are censored; the 30-day check above covers it.
- **Survivorship.** Deleted questions are not in the data, and Stack Overflow deletes mostly unanswered, low-score ones.
  So every rate here is biased upward, probably more for the tags at the bottom, which means the real gap between top
  and bottom is likely a bit wider than shown.
- **Current tags**, with the exposure column and the original-tags check above as the measure of the edit problem.
- **Pairs only.** Triples and exact tag sets were left out: at a 385-question floor very few of them qualify.

Spec, acceptance criteria and their tests: [`specs/001`](specs/001-q1-tag-answerability.md),
[`TESTING.md`](TESTING.md). Run it yourself: [`queries/q1.sql`](queries/q1.sql) (BigQuery console, about 9 GB, no dbt
needed).

## 2. python-only vs dbt-only, year over year

Two populations with very different sizes: python-only has 7,800 to 16,300 questions per year; dbt-only exists only
from 2020, with **31, 58 and 79 questions**. So the python half of this answer is a trend and the dbt half is mostly
an interval.

### The short answer

- **python-only answers per question fell from 2.31 in 2013 to 1.52 in 2021** (and 1.26 in 2022, a partial year). The
  accepted rate fell from 65.2% to 43.0% (35.4% in 2022). The decline happens almost every year; the biggest single
  drop is 2021 → 2022, and most of that one is not a quality signal (see censoring below).
- **dbt-only: 1.39, 1.14 and 1.06 answers per question** (2020 to 2022), with an accepted rate of 41.9%, 25.9% and
  27.8%. The intervals overlap year to year, so **I can't claim a dbt trend** in either metric.
- **Compared, dbt-only questions got fewer answers per question than python-only in 2021 and 2022** (the intervals don't
  touch) and a lower accepted rate in 2021 (25.9% vs 43.0%). In 2020, and for the 2022 accepted rate, the dbt intervals
  are too wide to separate them.

### How I read the prompt

- **"Only python" / "only dbt"** means the question's tags are *exactly* `python` or *exactly* `dbt`: one tag, nothing
  else (`python|pandas` and `python-3.x` are out). Literal, and it makes the python group small and peculiar: most
  Python questions carry more than one tag.
- **Last 10 years** = 2013 to 2022, by the question's creation year; answers count in their question's year. 2022 ends
  on 09-25.
- **Question-to-answer ratio.** I report it as **answers per question** (total answers / total questions), the same
  metric as "most answers" in P1, because "higher = more answers" reads naturally. For the literal ratio,
  **Q÷A = 1 / this**: python-only had 0.43 questions per answer in 2013 and 0.79 in 2022.
- **Year over year** for answers per question is the **absolute** difference, with the relative one in parentheses.
  Relative changes don't survive the inversion: python 2021 → 2022 is −17% in answers per question and +21% in questions
  per answer. Accepted-rate changes are in percentage points.
- **Accepted rate** is over all questions, with answer rate and accepted among answered beside it (same as P1).

### python-only

| Year | Questions | Answers per question (95% interval) | YoY, absolute (relative) | Accepted rate (95% interval) | YoY, points | Answer rate | Accepted among answered | Tag exposure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2013 | 7,819 | 2.31 (2.27–2.35) |  | 65.2% (64.1–66.2) |  | 97.2% | 67.0% | 4.5% |
| 2014 | 8,537 | 1.97 (1.94–2.00) | -0.34 (-15%) | 61.5% (60.4–62.5) | -3.7 | 95.6% | 64.3% | 3.9% |
| 2015 | 9,781 | 1.90 (1.87–1.93) | -0.07 (-3%) | 56.9% (55.9–57.9) | -4.6 | 93.7% | 60.7% | 3.7% |
| 2016 | 10,344 | 1.83 (1.81–1.86) | -0.07 (-3%) | 52.5% (51.6–53.5) | -4.4 | 91.8% | 57.2% | 3.6% |
| 2017 | 11,683 | 1.70 (1.68–1.72) | -0.13 (-7%) | 49.1% (48.2–50.0) | -3.4 | 88.9% | 55.2% | 3.6% |
| 2018 | 11,614 | 1.69 (1.67–1.72) | -0.01 (-0.4%) | 49.2% (48.3–50.1) | +0.1 | 89.2% | 55.2% | 4.0% |
| 2019 | 14,503 | 1.70 (1.68–1.72) | +0.01 (+1%) | 48.8% (48.0–49.6) | -0.4 | 89.5% | 54.5% | 3.7% |
| 2020 | 16,256 | 1.65 (1.63–1.67) | -0.05 (-3%) | 45.5% (44.7–46.3) | -3.3 | 88.0% | 51.7% | 5.1% |
| 2021 | 15,811 | 1.52 (1.50–1.54) | -0.13 (-8%) | 43.0% (42.2–43.8) | -2.5 | 84.8% | 50.7% | 4.3% |
| 2022 (to 09-25) | 12,809 | 1.26 (1.24–1.28) | -0.26 (-17%) | 35.4% (34.6–36.2) | -7.6 | 73.5% | 48.1% | 3.8% |

### dbt-only

| Year | Questions | Answers per question (95% interval) | YoY, absolute (relative) | Accepted rate (95% interval) | YoY, points | Answer rate | Accepted among answered | Tag exposure |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2013–2019 | 0 | | | | | | | |
| 2020 | 31 | 1.39 (1.06–1.71) |  | 41.9% (26.4–59.2) |  | 93.5% | 44.8% | 3.2% |
| 2021 | 58 | 1.14 (0.94–1.34) | -0.25 (-18%) | 25.9% (16.3–38.4) | -16.1 | 84.5% | 30.6% | 0.0% |
| 2022 (to 09-25) | 79 | 1.06 (0.91–1.21) | -0.07 (-7%) | 27.8% (19.2–38.6) | +2.0 | 84.8% | 32.8% | 0.0% |

For the record, Q÷A = 1 / this gives dbt-only 0.72, 0.88 and 0.94 questions per answer (2020 to 2022).

### How sure can we be?

- **Censoring explains most of the 2022 drop.** Answers per question = answer rate × answers per answered question.
  From 2021 to 2022 the answer rate fell from 84.8% to 73.5% while answers per *answered* question barely moved (1.80 →
  1.71): about **three quarters** of the drop is questions that had not been answered yet when the data stops. Same
  thing on acceptance: accepted rate fell 7.6 points, accepted among answered only 2.6 (50.7% → 48.1%).
  ([`eda/d3_ratio`](eda/d3_ratio/README.md), [`eda/d2_denominator`](eda/d2_denominator/README.md))
- **Survivorship makes the long decline look steeper than it was.** Deleted questions are missing, Stack Overflow
  deletes mostly unanswered ones, and older years have had more time to be cleaned up. So 2013's 2.31 and 65.2% are
  inflated more than 2021's numbers. The direction of the decline is clear (7 of the 9 yearly steps go down, with intervals
  that don't overlap; 2018 and 2019 are flat); its exact size isn't, and this data can't size the bias.
- **dbt's sample size is the whole story for dbt.** With 31 to 79 questions a year, the accepted-rate intervals are
  19 to 33 points wide. A wider definition (dbt among other tags: 96, 224 and 351 questions) shows the same direction,
  1.46 → 1.17 → 0.93 answers per question and 49.0% → 41.5% → 32.5% accepted, but it is a different population and
  doesn't replace the literal answer.

### Do tag edits change it?

Tag exposure is small here (python-only 3.6–5.1% per year, dbt-only 0–3.2%), and the check on the **original** tags
raises **3 warnings**:

- **python 2019**: the YoY change in answers per question is +0.01 on current tags and −0.02 on original tags. It
  switches sign, but both are basically zero.
- **python 2021**: answers per question is 1.52 on current tags and 1.50 on original tags, a move bigger than half the
  interval width (0.019). The original-tags population is bigger (17,104 vs 15,811): questions posted as python-only that got
  a second tag later.
- **dbt 2022**: the accepted-rate YoY is +2.0 points on current tags and −0.6 on original tags (81 questions instead of
  79). Inside dbt's interval either way.

Dropping every question whose tags were ever edited changes nothing visible (python 2022: 1.25 instead of 1.26 answers
per question, 35.2% instead of 35.4% accepted).

### Assumptions and limitations

- **Exact-match tags** ("only python" read literally); a reader who means "python among other tags" is answering a
  different question.
- **2022 is partial and censored**, flagged on every row (and the reason the last YoY step is mostly not a trend).
- **Survivorship** inflates older years more than recent ones (above).
- **Current tags**, with the original-tags check above.
- **dbt has 2.7 years of data, not ten**, on 168 questions in total; read its intervals, not its point values.

Spec, acceptance criteria and their tests: [`specs/002`](specs/002-q2-python-vs-dbt.md), [`TESTING.md`](TESTING.md).
Run it yourself: [`queries/q2.sql`](queries/q2.sql) (BigQuery console, about 7 GB).

## 3. Non-tag qualities that correlate with answers

_TBD — spec: [`specs/003`](specs/003-q3-post-qualities.md)_

## How this was built

_TBD — spec-first, with an AI coding agent; decisions in [`PLAN.md`](PLAN.md)._

## How this repo is organized

- `specs/` — definitions and acceptance criteria, written before the SQL
- `PLAN.md` — scope, schedule, decisions

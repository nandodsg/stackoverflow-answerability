# Testing

Every acceptance criterion (AC) in [`specs/`](specs/) points to the test that covers it. A test is one of:

- **Generic test**: `not_null`, `unique`, `relationships`, `accepted_values` or a `dbt_utils` test, declared in a
  `models/**/_*.yml` file. The AC is written beside it as `meta: {ac: AC-x.y}`.
- **Singular test**: a SQL file in [`tests/`](tests/) that returns the rows that break the rule; no rows = pass.
- **Unit test**: a `unit_tests:` block in a model YAML file: hand-written input rows and the rows the model must return.
  They read no table, so they cost nothing.
- **Check script**: [`tests/semantic/check_semantic_layer.py`](tests/semantic/check_semantic_layer.py) runs `mf query`
  (MetricFlow) and compares the results with the numbers quoted in the README.
- **Compiled query**: each file in [`queries/`](queries/) is run in the BigQuery console and must return the README
  numbers (section "Compiled queries" below).

A test with severity `warn` is an impact check: it flags rows for the README to discuss and does not fail the build.

## How to run

```bash
dbt deps                                  # once: installs dbt_utils
dbt build                                 # models + tests, everything except the one-time text scans
dbt build --select tag:needs_full_scan    # after the one-time scan: the original-tags impact checks
dbt test --select mart_p1_tags            # the tests of one model
python tests/semantic/check_semantic_layer.py
```

The text scans (`dbt run --target full_scan --select tag:full_scan`) read ~145 GB and are never part of the default
build. The cost guardrails, and what the project billed: [README, "Running on a free
tier"](README.md#running-on-a-free-tier).

## Shared definitions ([`specs/000`](specs/000-shared-definitions.md))

| AC | What it checks | Test | Kind |
|---|---|---|---|
| AC-0.1 | Question `id` is unique and not null | `stg_stackoverflow__questions.question_id`: `unique`, `not_null` | generic |
| AC-0.2 | Every answer's `parent_id` resolves to a question | `stg_stackoverflow__answers.question_id`: `not_null`, `relationships` | generic |
| AC-0.3 | Every accepted answer belongs to its question (292 legacy exceptions, 2008–2012, are reported) | [`assert_accepted_answer_belongs_to_question`](tests/assert_accepted_answer_belongs_to_question.sql) (warns up to 292, fails above) | singular |
| AC-0.4 | `answer_count` equals the joined answers | [`assert_answer_count_matches_joined_answers`](tests/assert_answer_count_matches_joined_answers.sql) | singular |
| AC-0.5 | Accepted rate = answer rate × accepted rate among answered | `expression_is_true` on `mart_p1_tags`, `mart_p1_pairs`, `mart_p2_python_dbt` (also the 30-day marts and `mart_p3_feature_rates`); check script, check `AC-0.5` | generic + check script |
| AC-0.6 | Answers per question = total answers / total questions; questions per answer is its inverse | `expression_is_true` on `mart_p1_tags`, `mart_p1_pairs`, `mart_p2_python_dbt`; check script, check `AC-0.6` (every python / dbt year) | generic + check script |
| AC-0.7 | `last_edit_date IS NULL` agrees with "no edit in `post_history`" | **Not a dbt test.** Measured once in [`eda/d4_edits`](eda/d4_edits/README.md) (32 differences out of ~638K edited questions) | EDA |
| AC-0.8 | Exposure on every result row, all questions as denominator | Column `tag_exposure` on the P1 and P2 marts, built from [`int_question_exposure`](models/intermediate/int_question_exposure.sql); the semantic layer defines it as a metric. No dedicated test on the column | model + metric |
| AC-0.9 | Exposure counts only edits after the first answer, of the right type | Unit test `exposure_counts_only_edits_after_the_first_answer` | unit |
| AC-0.10 | Impact checks run as `severity: warn` tests | [`assert_p1_original_tags_stable`](tests/assert_p1_original_tags_stable.sql), [`assert_p2_original_tags_stable`](tests/assert_p2_original_tags_stable.sql) (P1 and P2); P3's is in the P3 section | singular (warn) |

## Prompt 1 ([`specs/001`](specs/001-q1-tag-answerability.md))

| AC | What it checks | Test | Kind |
|---|---|---|---|
| AC-1.1 | Only 2022 (and 2021 for the robustness check) | `creation_year` `accepted_values` [2021, 2022] on `mart_p1_tags` and `mart_p1_pairs`; the cutoff date is printed by `queries/q1.sql` (`newest_question_at`) | generic + query |
| AC-1.2 | Every ranked group has at least 385 questions | `n_questions` `accepted_range` ≥ 385 on both marts, their 30-day and original-tags versions; `expression_is_true` on `mart_p1_tags_robustness`; check script (1,162 tags and 1,026 pairs in 2022) | generic + check script |
| AC-1.3 | Rates are between 0 and 1, n is next to each rate | `accepted_range` 0–1 on the rate columns, `not_null` on `n_questions` | generic |
| AC-1.4 | The 2021 ranking is produced and rank changes are listed | `mart_p1_rank_flips` (`metric` `accepted_values`); the list itself is the model | model + generic |
| AC-1.5 | Wilson bounds match the reference values (9/10, 850/1,000, 1/1, 0/1) | [`assert_wilson_reference_values`](tests/assert_wilson_reference_values.sql) | singular |
| AC-1.6 | "Highest" sorts by the lower bound, "lowest" by the upper bound | [`assert_p1_rank_order`](tests/assert_p1_rank_order.sql); `expression_is_true` (lower ≤ rate ≤ upper) on both marts | singular + generic |
| AC-1.7 | Raw-rate (A) and empirical-Bayes (C) rankings, overlap with the Wilson lists | `expression_is_true` on `mart_p1_tags_robustness`, `mart_p1_pairs_robustness`, `mart_p1_robustness_overlap` | generic |
| AC-1.8 | Every accepted-rate row shows answer rate and accepted rate among answered | Same test as AC-0.5 (`also: AC-1.8`) | generic |
| AC-1.9 | Exposure on every ranked row; original-tags ranking and its warnings | `tag_exposure` column; [`assert_p1_original_tags_stable`](tests/assert_p1_original_tags_stable.sql) (warn, needs the scan: `tag:needs_full_scan`) | model + singular (warn) |
| AC-1.10 | Answers-per-question lists use the lower / upper bound; Cochran flag on every row | Bounds: `expression_is_true` on both marts (same test as AC-1.6); flag: column `answers_interval_reliable`. **No unit test on a hand-computed group**, as the spec asks: the flag is checked against the EDA ([`eda/d1_answers_ranking`](eda/d1_answers_ranking/README.md): 6 tags and 8 pairs fail Cochran's rule) | generic + EDA (gap) |

## Prompt 2 ([`specs/002`](specs/002-q2-python-vs-dbt.md))

| AC | What it checks | Test | Kind |
|---|---|---|---|
| AC-2.1 | Exact-match tag filter (`python`, `python\|pandas`, `python-3.x`, `dbt`, `dbt\|sql`) | Unit test `mart_p2_exact_tag_match` | unit |
| AC-2.2 | One row per (tag, year) 2013–2022, empty years kept | `unique_combination_of_columns` on `mart_p2_python_dbt` and its three sensitivity versions; the same unit test | generic + unit |
| AC-2.3 | Every dbt rate has n and an interval | `n_questions` `not_null` and `expression_is_true` on `mart_p2_python_dbt` | generic |
| AC-2.4 | 2022 marked partial | `expression_is_true` (`is_partial_year`) on `mart_p2_python_dbt` and its three sensitivity versions | generic |
| AC-2.5 | Answers per question is the charted ratio; Q÷A = 1 / this | `expression_is_true` on `mart_p2_python_dbt` (`also: AC-2.5`); check script, check `AC-0.6`; the sentence itself is README text | generic + check script |
| AC-2.6 | Exposure on every row; original-tags populations and their warnings | `tag_exposure` column; [`assert_p2_original_tags_stable`](tests/assert_p2_original_tags_stable.sql) (warn, `tag:needs_full_scan`) | model + singular (warn) |

## Prompt 3 ([`specs/003`](specs/003-q3-post-qualities.md))

| AC | What it checks | Test | Kind |
|---|---|---|---|
| AC-3.1 | Every feature is known at posting time | No-text features (`asker_account_age_days`, `asker_prior_questions`, hour and weekday posted) are built from posting-time metadata in [`int_question_posting_context`](models/intermediate/int_question_posting_context.sql); `accepted_range` ≥ 0 on `asker_account_age_days` in `_intermediate_p3__models.yml` (`severity: warn`, `meta: ac: AC-3.1`). Text features come from the original text, see AC-3.4 | model + generic |
| AC-3.2 | `body` and `post_history` text are read once; no downstream model reads them | [`assert_text_columns_read_once`](tests/assert_text_columns_read_once.sql): reads dbt's project graph and fails if any model other than the staging view and the one-time scan reads `posts_questions` or `post_history` from the source (reads no table) | singular |
| AC-3.3 | An effect that does not point the same way in each full year is labeled unstable | `accepted_rate_effect_stable` and `answer_rate_effect_stable` on `mart_p3_feature_effects` (`meta: ac: AC-3.3`); unit tests `mart_p3_effect_stability` and `mart_p3_label_effect_stability` (a level with only 3 full years above the floor is "not stable" and shows `full_years_with_effect` = 3) | generic + unit |
| AC-3.4 | Title / body features come from the original text; the scan is done once and its size is stated | Models `int_post_history_scan` (original) and `int_question_body_scan` (current) behind the `full_scan` tag, never in a default build; [`assert_text_feature_rules`](tests/assert_text_feature_rules.sql) and [`assert_p3_bucket_rules`](tests/assert_p3_bucket_rules.sql) hold hand-written examples of every rule (read no table). The scan size is README text | model + singular |
| AC-3.5 | Each effect is also reported on current text, never-edited and not-edited-after-first-answer | `version` `accepted_values` [original, current, never_edited, not_edited_after_answer] on `mart_p3_feature_rates` and `mart_p3_label_rates` (`meta: ac: AC-3.5`); `_effect_flips_vs_original` column on both effects marts; check script, section 7 (the semantic layer rebuilds the original-text counts of a few buckets and labels) | generic + check script |
| AC-3.6 | Text exposure and the share of values changed between original and current text; a direction change warns | `not_null` on `text_exposure` and `share_changed` of `mart_p3_leakage` (`meta: ac: AC-3.6`); [`assert_p3_original_text_stable`](tests/assert_p3_original_text_stable.sql) (warn, `tag:needs_full_scan`, closes the P3 part of AC-0.10) | generic + singular (warn) |
| AC-3.7 | Each label level is reported against its rule-based neighbour | `mart_p3_label_vs_rules`: `unique_combination_of_columns` (label, level, rule value) and `accepted_range` 0–1 on both shares; the flag for a label that does not line up is README text read from this mart | model + generic |
| AC-3.8 | Each label level's effect is reported overall and inside rule-based strata; rare levels carry `full_years_with_effect` < 4 | `mart_p3_label_incremental`: `unique_combination_of_columns` (label, level) and `accepted_range` 0–1 on `adjusted_coverage`; `full_years_with_effect` `accepted_range` 0–4 on `mart_p3_label_effects`; unit test `mart_p3_label_effect_stability`; check script, section 7 (worked-example raw effect = +17.2 points, rebuilt through `mf query`) | model + generic + unit + check script |

The labels themselves have their own checks, outside the AC list: [`assert_quality_labels_match_analysis_set`](tests/assert_quality_labels_match_analysis_set.sql)
(the seed covers exactly the 30,000-question analysis set), the seed's `accepted_values` on every label level
(`seeds/_seeds.yml`), and [`assert_p3_label_buckets`](tests/assert_p3_label_buckets.sql) (the label layer accounts for every
labeled question and every rubric level). Tests that read the scans or the seed are tagged `needs_full_scan`.

## Compiled queries

[`queries/`](queries/) holds `q1.sql`, `q2.sql` and `q3.sql`: one BigQuery script per prompt, self-contained
(every dbt model inlined down to `bigquery-public-data.stackoverflow`), generated by
[`queries/build_queries.py`](queries/build_queries.py) from the models and the hand-written headers in `queries/src/`.
Never edit a generated file: change the model or the source and run the script again.

`q3.sql` is the one exception to "self-contained": it reads three stored tables by name (`int_post_history_scan`,
`int_question_body_scan` and the seed `quality_labels_analysis`), because the text scans cost ~145 GB to rebuild and the
labels are a CSV, not SQL. The file carries the placeholder `YOUR_PROJECT`.`so_answerability`, and its header says how
to build the three tables and replace it.

| File | Prompt | Expected result | Status |
|---|---|---|---|
| `q1.sql` | 1 | 2022 accepted rate 30.5%; 1,162 ranked tags; 1,026 ranked pairs; top / bottom 10 lists | run as delivered in a fresh sandbox project on 2026-10-31 (8.92 GiB billed, temp tables dropped, 1,162 tags and 1,026 pairs); numbers also checked on the CTE variant |
| `q2.sql` | 2 | python-only answers per question 2.31 / 1.52 / 1.26 (2013 / 2021 / 2022); dbt-only 1.39 / 1.14 / 1.06 (2020–2022) | run as delivered in a fresh sandbox project on 2026-10-31 (31 / 58 / 79 dbt questions in 2020–2022, python 7,819 / 15,811 / 12,809 in 2013 / 2021 / 2022); numbers also checked on the CTE variant |
| `q3.sql` | 3 | Eight results, one per P3 mart: 1,509 / 1,032 / 60 / 144 rows (rule-based rates, effects, leakage, answer lens) and 270 / 69 / 24 / 9 rows (label rates, effects, label vs rules, incremental) | compiled 2026-11-01; each of the 8 result statements run on a storage-free copy with the real project prefix and compared with the built marts: all 8 identical (31.4 GiB billed, 38 GiB uncached). The temp-table script as delivered has not been run end to end (it needs the stored tables, below) |

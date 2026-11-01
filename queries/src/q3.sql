-- Prompt 3: other than tags, what qualities of a question go with the highest rate of answer and of accepted answer?
-- Runs in the BigQuery console, but NOT as-is: unlike q1 and q2 it reads three stored tables by name (see below).
-- @models: mart_p3_feature_rates, mart_p3_feature_effects, mart_p3_leakage, mart_p3_answer_rates, mart_p3_label_rates, mart_p3_label_effects, mart_p3_label_vs_rules, mart_p3_label_incremental
-- @stored: int_post_history_scan, int_question_body_scan
--
-- STORED TABLES (set up once, then replace the placeholder). Everything else is inlined down to
-- bigquery-public-data.stackoverflow. These three cannot be:
--   * int_post_history_scan, int_question_body_scan: the original and the current text features of every 2018-2022
--     question (plus the text of a 5% sample). Building them reads post_history.text and posts_questions.body, ~145 GB
--     in all, so the dbt project builds them once, on purpose, and never in a default build.
--   * quality_labels_analysis: the 30,000 quality labels (a dbt seed, seeds/quality_labels_analysis.csv in the repo).
-- To run this file: build them with `dbt seed` and `dbt run --target full_scan --select tag:full_scan` (see PLAN.md and
-- TESTING.md), then replace `YOUR_PROJECT`.`so_answerability` below (find and replace, every occurrence) with the
-- project and dataset where they were built. The seed alone can instead be loaded from its CSV (BigQuery console, Create
-- table, upload, same column names and types as seeds/_seeds.yml); the two scan tables cannot be skipped.
--
-- One result per mart, eight in all, in this order: (1) rates by bucket of every rule-based feature, (2) their effects
-- against the reference bucket, with the stability, topic and sensitivity controls, (3) the leakage KPI, (4) the answer
-- lens (acceptance among the answers of the 5% sample), (5-6) the same rates and effects for the six quality labels,
-- (7) each label against the rule-based feature closest to it, (8) what each label adds beyond those rules. The console
-- shows the results as separate tabs of the job.
--
-- Assumptions (definitions and reasons: specs/000 and specs/003 in the repo):
--   * Outcomes are the answer rate and the accepted rate, both out of ALL questions, and accepted-among-answered beside
--     them. Features are measured on the ORIGINAL title / body (what the asker posted), because the current text can be
--     changed by the answers (D4). `version` says which text and population: original, current, never_edited,
--     not_edited_after_answer.
--   * Cohorts are each creation year 2018-2022 and the four full years together ('2018-2021'). 2022 is partial and
--     censored: use '2018-2021' for effects. A bucket (or its reference) under 385 questions in a cohort has no row.
--   * Effects are differences from the reference bucket (`_effect`), with a 95% margin: an effect is clearly not zero
--     when |effect| > margin. `_effect_stable` is AC-3.3 (same direction in each full year); `_effect_tag_adjusted` is
--     the same difference inside each primary-tag stratum, averaged (a topic control); `_effect_flips_vs_original` is
--     the check against the current text.
--   * The quality labels are judgments of a language model (TypeSafe Jev) on 30,000 random questions of the 5% sample,
--     not facts, and the effects are correlations. For a label, `feature` is the label and `bucket` its level;
--     `not_applicable` is left out of a label's comparison; a rare level has no row in a cohort under the floor, and its
--     stability is "not assessable" (`full_years_with_effect` < 4), not "flipping".
--   * Cost: the inlined part reads the public tables' metadata columns and the stored tables, never body or text:
--     nothing here rescans the text. As a script (temp tables, each stage built once) it has not been measured; the
--     eight result statements, each rebuilt from scratch without temp tables, read 38 GiB in all (1.4 to 6.8 GiB each).

-- 1. Rates by bucket: version x feature x bucket x cohort.
select * from mart_p3_feature_rates
order by version, feature, bucket, cohort;

-- 2. Effects against the reference bucket (bucket '1:').
select * from mart_p3_feature_effects
order by version, feature, bucket, cohort;

-- 3. Leakage KPI: how much reading the current text would have changed the features, per year x text feature.
select * from mart_p3_leakage
order by creation_year, feature;

-- 4. Answer lens: which body qualities go with being the accepted answer (5% sample, original answer text).
select * from mart_p3_answer_rates
order by feature, bucket, cohort;

-- 5. Quality labels, rates by level: version x label x level x cohort.
select * from mart_p3_label_rates
order by version, feature, bucket, cohort;

-- 6. Quality labels, effects against each label's first level.
select * from mart_p3_label_effects
order by version, feature, bucket, cohort;

-- 7. Each label level against the rule-based value that measures something close to it (AC-3.7).
select * from mart_p3_label_vs_rules
order by label, level, rule_value;

-- 8. Does a label add anything beyond the rules? Raw and rules-adjusted effect per level (AC-3.8).
select * from mart_p3_label_incremental
order by label, level;

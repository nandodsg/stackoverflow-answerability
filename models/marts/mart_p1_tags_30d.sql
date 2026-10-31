-- Materialized as a table: project default in dbt_project.yml.
-- Prompt 1 on the 30-day window (specs/001 "Metrics"): the mart_p1_tags rules on questions that had the full 30 days, with
-- answers and acceptance counted only when they came within those 30 days. Shows how much of the plain result is censoring.
{{ p1_ranked_groups(ref('int_question_tags_30d'), ['tag']) }}

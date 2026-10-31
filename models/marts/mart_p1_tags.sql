-- Materialized as a table: project default in dbt_project.yml.
-- Prompt 1, single tags (specs/001): one row per (year, tag) with at least 385 questions, for 2022 (the answer) and
-- 2021 (the robustness check). Rates, Wilson bounds, answers per question with its interval, tag exposure and the
-- top / bottom ranks. The rules live in macros/p1_ranked_groups.sql so tags and pairs cannot drift apart.
{{ p1_ranked_groups(ref('int_question_tags'), ['tag']) }}

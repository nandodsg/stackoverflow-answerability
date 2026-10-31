-- Materialized as a table: project default in dbt_project.yml.
-- Prompt 1, tag combinations (specs/001): the same table as mart_p1_tags, one row per (year, unordered tag pair)
-- with at least 385 questions. Same macro, so the same rules.
{{ p1_ranked_groups(ref('int_question_tag_pairs'), ['tag_a', 'tag_b']) }}

-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag).
-- Prompt 1 impact check (specs/000, AC-1.9): the mart_p1_tags rules on the ORIGINAL tags. The warn test
-- assert_p1_original_tags_stable compares it with mart_p1_tags. Tagged needs_full_scan (reads the one-time text scan).
{{ config(tags=['needs_full_scan']) }}
{{ p1_ranked_groups(ref('int_question_original_tags'), ['tag']) }}

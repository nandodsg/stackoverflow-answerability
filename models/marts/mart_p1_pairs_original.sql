-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag).
-- Prompt 1 impact check for tag pairs: the mart_p1_pairs rules on the ORIGINAL tags (AC-1.9).
{{ config(tags=['needs_full_scan']) }}
{{ p1_ranked_groups(ref('int_question_original_tag_pairs'), ['tag_a', 'tag_b']) }}

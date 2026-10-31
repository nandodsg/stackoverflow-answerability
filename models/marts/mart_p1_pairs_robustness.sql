-- Materialized as a table: project default in dbt_project.yml.
-- Prompt 1 robustness, tag pairs (specs/001, AC-1.7): the same three rankings as mart_p1_tags_robustness.
{{ p1_robustness(ref('int_question_tag_pairs'), ref('mart_p1_pairs'), ['tag_a', 'tag_b']) }}

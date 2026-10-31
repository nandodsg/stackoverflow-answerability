-- Materialized as a table: project default in dbt_project.yml.
-- Prompt 1 tag pairs on the 30-day window: the mart_p1_pairs rules on questions that had the full 30 days.
{{ p1_ranked_groups(ref('int_question_tag_pairs_30d'), ['tag_a', 'tag_b']) }}

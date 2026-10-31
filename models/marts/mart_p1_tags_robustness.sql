-- Materialized as a table: project default in dbt_project.yml.
-- Prompt 1 robustness, single tags (specs/001, AC-1.7): for every ranked tag, the accepted-rate rank by the Wilson bound
-- (the answer), by the raw rate (method A) and by the empirical-Bayes rate (method C), plus the fitted prior.
{{ p1_robustness(ref('int_question_tags'), ref('mart_p1_tags'), ['tag']) }}

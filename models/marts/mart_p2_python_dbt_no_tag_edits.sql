-- Materialized as a table: project default in dbt_project.yml.
-- Prompt 2 sensitivity view (specs/002 Population): the mart_p2_python_dbt rules, dropping every question whose tags were
-- ever edited (post_history types 6 and 9). It is a robustness check, not the answer: edited questions do better, so
-- dropping them is biased (specs/000, D4).
{{ p2_python_dbt(ref('int_questions'), extra_where='e.first_tag_edit_at is null') }}

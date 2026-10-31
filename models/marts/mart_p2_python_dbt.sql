-- Materialized as a table: project default in dbt_project.yml.
-- Prompt 2 (specs/002): questions whose current tags are EXACTLY `python` or EXACTLY `dbt` (one tag, no others), one row
-- per (tag, creation year) for 2013-2022. Years with no question stay as rows of zeros (AC-2.2). Answers per question
-- is the headline ratio (D3) with its 95% interval; questions per answer (Q÷A = 1 / answers per question) is kept as
-- the inverse, shown once in the README. 2022 stops on 2022-09-25 and is flagged partial (AC-2.4).
-- The rules live in macros/p2_python_dbt.sql so the sensitivity views cannot drift from this table.
{{ p2_python_dbt(ref('int_questions')) }}

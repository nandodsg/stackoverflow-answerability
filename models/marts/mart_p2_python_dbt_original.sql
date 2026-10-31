-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag).
-- Prompt 2 impact check (specs/000, AC-2.6): the mart_p2_python_dbt rules on the ORIGINAL tags, so a question posted as
-- `python` and later retagged `python|pandas` still counts here. Compared with mart_p2_python_dbt by the warn test
-- assert_p2_original_tags_stable.
{{ config(tags=['needs_full_scan']) }}
{{ p2_python_dbt(ref('int_questions_original')) }}

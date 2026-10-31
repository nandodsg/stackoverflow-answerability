-- Materialized as a table: project default in dbt_project.yml.
-- Prompt 2 sensitivity view (specs/002 "The dbt problem"): questions tagged `dbt` among other tags (dbt-only plus `dbt|sql`
-- and so on), 2013-2022, with the same rules as mart_p2_python_dbt. It does not replace the literal dbt-only answer; it
-- shows whether the tiny dbt-only sample behaves like the larger group of dbt questions.
{{ p2_python_dbt(ref('int_question_tags'), tag_column='tag', tag_list=['dbt']) }}

-- Materialized as a view: set for the semantic folder in dbt_project.yml. Tagged needs_full_scan (reads the one-time scan).
-- Semantic layer input for the original-tags variant (specs/000 AC-0.10, specs/001 AC-1.9), one row per (question, ORIGINAL
-- tag), 2021-2022: the rows of int_question_original_tags with the question's creation time and the outcome flags as 0/1
-- integers.
{{ config(tags=['needs_full_scan']) }}

select
    t.question_id,
    t.tag,
    q.created_at,
    t.creation_year,
    t.answer_count,
    cast(t.is_answered as int64) as answered_flag,
    cast(t.has_accepted_answer as int64) as accepted_flag
from {{ ref('int_question_original_tags') }} as t
inner join {{ ref('int_questions') }} as q
    on q.question_id = t.question_id

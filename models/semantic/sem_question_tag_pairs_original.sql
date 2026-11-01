-- Materialized as a view: set for the semantic folder in dbt_project.yml. Tagged needs_full_scan (reads the one-time scan).
-- Semantic layer input for the original-tags variant, one row per (question, unordered pair of ORIGINAL tags), tag_a < tag_b,
-- 2021-2022: the rows of int_question_original_tag_pairs with the question's creation time and 0/1 outcome flags.
{{ config(tags=['needs_full_scan']) }}

select
    p.question_id,
    p.tag_a,
    p.tag_b,
    q.created_at,
    p.creation_year,
    p.answer_count,
    cast(p.is_answered as int64) as answered_flag,
    cast(p.has_accepted_answer as int64) as accepted_flag
from {{ ref('int_question_original_tag_pairs') }} as p
inner join {{ ref('int_questions') }} as q
    on q.question_id = p.question_id

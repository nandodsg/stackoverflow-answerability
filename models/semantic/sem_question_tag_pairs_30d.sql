-- Materialized as a view: set for the semantic folder in dbt_project.yml.
-- Semantic layer input for the 30-day-window variant, one row per (question, unordered tag pair), tag_a < tag_b: the rows
-- of int_question_tag_pairs_30d with the question's creation time and the outcome flags as 0/1 integers.
select
    p.question_id,
    p.tag_a,
    p.tag_b,
    q.created_at,
    p.creation_year,
    p.answer_count,
    cast(p.is_answered as int64) as answered_flag,
    cast(p.has_accepted_answer as int64) as accepted_flag
from {{ ref('int_question_tag_pairs_30d') }} as p
inner join {{ ref('int_questions') }} as q
    on q.question_id = p.question_id

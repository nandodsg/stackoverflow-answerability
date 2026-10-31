-- Materialized as a view: set for the semantic folder in dbt_project.yml.
-- Semantic layer input for the 30-day-window variant (specs/001 "Metrics"), one row per (question, current tag): the rows
-- of int_question_tags_30d (2021-2022 questions that had the full 30 days; answer_count, answered and accepted all count
-- only what came within 30 days) with the question's creation time and the outcome flags as 0/1 integers.
select
    t.question_id,
    t.tag,
    q.created_at,
    t.creation_year,
    t.answer_count,
    cast(t.is_answered as int64) as answered_flag,
    cast(t.has_accepted_answer as int64) as accepted_flag
from {{ ref('int_question_tags_30d') }} as t
inner join {{ ref('int_questions') }} as q
    on q.question_id = t.question_id

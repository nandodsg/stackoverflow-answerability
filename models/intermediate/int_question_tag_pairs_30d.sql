-- Materialized as a view: set in the inline config() below (overrides the project default, table).
-- int_question_tag_pairs with the 30-day-window outcomes (answer_count here means answers within 30 days), limited to
-- questions that had the full window. Same columns as int_question_tag_pairs.
{{ config(materialized='view') }}

select
    w.question_id,
    w.creation_year,
    w.answers_30d as answer_count,
    w.answers_30d > 0 as is_answered,
    w.accepted_30d as has_accepted_answer,
    least(a, b) as tag_a,
    greatest(a, b) as tag_b
from {{ ref('int_question_window30') }} as w
inner join {{ ref('int_questions') }} as q
    on q.question_id = w.question_id
cross join unnest(split(q.tags, '|')) as a with offset as i
cross join unnest(split(q.tags, '|')) as b with offset as j
where w.has_full_window
    and i < j

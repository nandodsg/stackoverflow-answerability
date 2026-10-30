-- Materialized as a view: set in the inline config() below (overrides the project default, table).
-- One row per (question, current tag): a question with 3 tags appears 3 times. P1 groups this by tag.
-- A view: it stores nothing, and a filter on creation_year still reads only that partition of int_questions.
{{ config(materialized='view') }}

select
    q.question_id,
    tag,
    q.creation_year,
    q.tag_count,
    q.answer_count,
    q.is_answered,
    q.has_accepted_answer,
    q.first_answer_at
from {{ ref('int_questions') }} as q
cross join unnest(split(q.tags, '|')) as tag

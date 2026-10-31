-- Materialized as a view: set in the inline config() below (overrides the project default, table).
-- One row per (question, unordered pair of current tags): a question with 3 tags appears 3 times, with 5 tags 10 times.
-- The pair is stored alphabetically (tag_a < tag_b), so "python + pandas" and "pandas + python" are the same group.
{{ config(materialized='view') }}

select
    q.question_id,
    q.creation_year,
    q.answer_count,
    q.is_answered,
    q.has_accepted_answer,
    least(a, b) as tag_a,
    greatest(a, b) as tag_b
from {{ ref('int_questions') }} as q
cross join unnest(split(q.tags, '|')) as a with offset as i
cross join unnest(split(q.tags, '|')) as b with offset as j
where i < j

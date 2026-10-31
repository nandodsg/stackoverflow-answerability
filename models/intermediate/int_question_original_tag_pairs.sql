-- Materialized as a view: set in the inline config() below (overrides the project default, table).
-- Same shape as int_question_tag_pairs (one row per question and unordered tag pair) but from the ORIGINAL tags, for 2021-2022.
{{ config(materialized='view', tags=['needs_full_scan']) }}

select
    q.question_id,
    q.creation_year,
    q.answer_count,
    q.is_answered,
    q.has_accepted_answer,
    least(a, b) as tag_a,
    greatest(a, b) as tag_b
from {{ ref('int_questions_original') }} as q
cross join unnest(split(q.tags, '|')) as a with offset as i
cross join unnest(split(q.tags, '|')) as b with offset as j
where q.creation_year in (2021, 2022)
    and q.tags is not null
    and i < j

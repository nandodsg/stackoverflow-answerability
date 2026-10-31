-- Materialized as a view: set in the inline config() below (overrides the project default, table).
-- Same shape as int_question_tags (one row per question and tag) but from the ORIGINAL tags, for 2021-2022, the years P1 ranks.
{{ config(materialized='view', tags=['needs_full_scan']) }}

select
    q.question_id,
    tag,
    q.creation_year,
    q.answer_count,
    q.is_answered,
    q.has_accepted_answer
from {{ ref('int_questions_original') }} as q
cross join unnest(split(q.tags, '|')) as tag
where q.creation_year in (2021, 2022)
    and q.tags is not null

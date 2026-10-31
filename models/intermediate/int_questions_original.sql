-- Materialized as a view: set in the inline config() below (overrides the project default, table).
-- int_questions with the ORIGINAL tags (post_history type 3, read once by int_post_history_scan) in place of the current
-- ones: the population of the leakage impact checks (specs/000, AC-0.10). Reads only post_id / original_tags / post_kind
-- of the scan, never its text columns. Tagged needs_full_scan: it cannot build until the one-time scan exists.
-- Fallbacks: from 2018 a question with no history row (29 in 2022) keeps its current tags; before 2018 the scan holds only
-- originally `python`-only or `dbt`-only questions, so any other 2013-2017 question has null tags here (P2 reads this
-- view only for exact python / dbt, so that is all it needs).
{{ config(materialized='view', tags=['needs_full_scan']) }}

select
    q.question_id,
    q.creation_year,
    coalesce(nullif(s.original_tags, ''), if(q.creation_year >= 2018, q.tags, null)) as tags,
    q.answer_count,
    q.is_answered,
    q.has_accepted_answer
from {{ ref('int_questions') }} as q
left join (
    select post_id, original_tags
    from {{ ref('int_post_history_scan') }}
    where post_kind = 'question'
) as s
    on s.post_id = q.question_id
where q.creation_year between 2013 and 2022

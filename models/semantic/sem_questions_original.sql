-- Materialized as a view: set for the semantic folder in dbt_project.yml. Tagged needs_full_scan (reads the one-time scan).
-- Semantic layer input for the original-tags variant, one row per question, 2013-2022, with the ORIGINAL tag string (the
-- whole string, matched exactly for P2: `python` = python-only as posted). The rows of int_questions_original with the
-- question's creation time and 0/1 outcome flags.
{{ config(tags=['needs_full_scan']) }}

select
    o.question_id,
    q.created_at,
    o.creation_year,
    o.tags,
    array_length(split(o.tags, '|')) as tag_count,
    o.answer_count,
    cast(o.is_answered as int64) as answered_flag,
    cast(o.has_accepted_answer as int64) as accepted_flag
from {{ ref('int_questions_original') }} as o
inner join {{ ref('int_questions') }} as q
    on q.question_id = o.question_id
where o.tags is not null

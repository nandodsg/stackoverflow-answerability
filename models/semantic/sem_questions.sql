-- Materialized as a view: set for the semantic folder in dbt_project.yml.
-- Semantic layer input, one row per question: int_questions plus the tag-exposure flag, with the outcome flags as 0/1
-- integers so MetricFlow can add them up. A view: it stores nothing, and a filter on creation_year still reads only
-- that partition of int_questions.
select
    q.question_id,
    q.created_at,
    q.creation_year,
    q.tags,
    q.tag_count,
    q.answer_count,
    cast(q.is_answered as int64) as answered_flag,
    cast(q.has_accepted_answer as int64) as accepted_flag,
    cast(e.tags_exposed as int64) as tags_exposed_flag,
    cast(e.first_tag_edit_at is not null as int64) as tag_ever_edited
from {{ ref('int_questions') }} as q
inner join {{ ref('int_question_exposure') }} as e
    on e.question_id = q.question_id

-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the partition).
-- Leakage exposure (specs/000, AC-0.8/0.9): one row per question saying whether its tags, or its title/body, were
-- first edited AFTER the first answer. Reads only revision metadata (ids, types, times), never `text`.
--   tags:        post_history types 6 (edit tags) and 9 (rollback tags)
--   title/body:  types 4, 5 (edit title, body) and 7, 8 (rollbacks)
-- Any editor counts, the asker included. A question with no answer cannot be exposed.
{{
    config(
        partition_by={
            'field': 'creation_year',
            'data_type': 'int64',
            'range': {'start': 2008, 'end': 2023, 'interval': 1},
        }
    )
}}

with edits as (
    select
        post_id,
        min(if(post_history_type_id in (6, 9), created_at, null)) as first_tag_edit_at,
        min(if(post_history_type_id in (4, 5, 7, 8), created_at, null)) as first_text_edit_at
    from {{ ref('stg_stackoverflow__post_history') }}
    where post_history_type_id in (4, 5, 6, 7, 8, 9)
    group by post_id
)

select
    q.question_id,
    q.creation_year,
    e.first_tag_edit_at,
    e.first_text_edit_at,
    coalesce(e.first_tag_edit_at > q.first_answer_at, false) as tags_exposed,
    coalesce(e.first_text_edit_at > q.first_answer_at, false) as text_exposed
from {{ ref('int_questions') }} as q
left join edits as e
    on e.post_id = q.question_id

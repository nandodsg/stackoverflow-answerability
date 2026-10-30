-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the partition).
-- The question hub: one row per question with everything the three prompts share (cohort year, current tags,
-- outcomes, first-answer time). A table, partitioned by creation year, so a query on 2022 reads only 2022.
{{
    config(
        partition_by={
            'field': 'creation_year',
            'data_type': 'int64',
            'range': {'start': 2008, 'end': 2023, 'interval': 1},
        }
    )
}}

with answers_per_question as (
    select
        question_id,
        count(*) as n_answers_joined,
        min(created_at) as first_answer_at
    from {{ ref('stg_stackoverflow__answers') }}
    group by question_id
)

select
    q.question_id,
    q.created_at,
    q.creation_year,
    q.tags,
    array_length(split(q.tags, '|')) as tag_count,
    q.answer_count,
    -- Kept beside answer_count only so AC-0.4 can check they agree (they do: gap 0 in the 2022-09 snapshot).
    coalesce(a.n_answers_joined, 0) as n_answers_joined,
    q.answer_count > 0 as is_answered,
    q.accepted_answer_id is not null as has_accepted_answer,
    q.accepted_answer_id,
    q.owner_user_id,
    q.last_edited_at,
    -- Earliest moment an answer can influence an edit: the reference event of the leakage KPI (AC-0.8).
    a.first_answer_at
from {{ ref('stg_stackoverflow__questions') }} as q
left join answers_per_question as a
    on a.question_id = q.question_id

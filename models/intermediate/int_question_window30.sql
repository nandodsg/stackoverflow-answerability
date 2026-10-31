-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the partition).
-- The 30-day-window version of the outcomes (specs/001 "Metrics", censoring). One row per 2021-2022 question:
--   answers_30d    answers created within 30 days of the question
--   accepted_30d   the accepted answer was created within 30 days (the acceptance time is not in the data; the accepted
--                  answer's creation date is the proxy, specs/000)
--   has_full_window  the question is at least 30 days older than the newest question in the snapshot, so it had the whole
--                  window to collect answers. Computed from the data, not hard-coded, so it follows the snapshot.
-- Only 2021-2022 because only P1 uses it. Reads answer ids and times, never `body`.
{{
    config(
        partition_by={
            'field': 'creation_year',
            'data_type': 'int64',
            'range': {'start': 2008, 'end': 2023, 'interval': 1},
        }
    )
}}

select
    q.question_id,
    q.creation_year,
    q.created_at <= timestamp_sub((select max(created_at) from {{ ref('int_questions') }}), interval 30 day) as has_full_window,
    q.answer_count,
    q.has_accepted_answer,
    countif(a.created_at <= timestamp_add(q.created_at, interval 30 day)) as answers_30d,
    countif(a.answer_id = q.accepted_answer_id and a.created_at <= timestamp_add(q.created_at, interval 30 day)) > 0 as accepted_30d
from {{ ref('int_questions') }} as q
left join {{ ref('stg_stackoverflow__answers') }} as a
    on a.question_id = q.question_id
where q.creation_year in (2021, 2022)
group by q.question_id, q.creation_year, q.created_at, q.answer_count, q.has_accepted_answer

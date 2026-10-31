-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the partition).
-- The P3 features that need no text (specs/003): when the question was posted and who asked it, all known at posting
-- time. One row per question created 2018-2022. A table, not a view: counting each asker's earlier questions sorts all
-- 23M questions since 2008, which is worth doing once rather than on every read.
--   hour_posted_utc, weekday_posted  from creation_date, in UTC (not the asker's local time)
--   asker_account_age_days           days from the asker's account creation to the question; null if the account is gone
--   asker_prior_questions            the asker's questions posted before this one; a lower bound, since deleted questions
--                                    are not in the dataset; null if the account is gone
-- Current reputation is left out on purpose: it is measured at snapshot time, partly caused by the answers (specs/003).
{{
    config(
        partition_by={
            'field': 'creation_year',
            'data_type': 'int64',
            'range': {'start': 2018, 'end': 2023, 'interval': 1},
        }
    )
}}

with asker_order as (
    select
        question_id,
        creation_year,
        created_at,
        owner_user_id,
        row_number() over (partition by owner_user_id order by created_at, question_id) - 1 as prior_questions
    from {{ ref('int_questions') }}
    where owner_user_id is not null
)

select
    q.question_id,
    q.creation_year,
    extract(hour from q.created_at) as hour_posted_utc,
    -- 1 = Sunday ... 7 = Saturday (BigQuery's numbering).
    extract(dayofweek from q.created_at) as weekday_posted,
    timestamp_diff(q.created_at, u.created_at, second) / 86400 as asker_account_age_days,
    o.prior_questions as asker_prior_questions
from {{ ref('int_questions') }} as q
left join asker_order as o
    on o.question_id = q.question_id
left join {{ ref('stg_stackoverflow__users') }} as u
    on u.user_id = q.owner_user_id
where q.creation_year between 2018 and 2022

-- Replaces dbt source freshness, which would fail on every run of a frozen snapshot. This checks the opposite: the
-- snapshot is still the one the README numbers come from. A row here means Google changed the public dataset, so
-- the README numbers are stale. A warning, not an error: a newer snapshot is still worth building.
{{ config(severity='warn') }}

with expected as (
    select 'posts_questions' as source_table, 23020127 as n_rows,
        timestamp '2022-09-25 05:56:32.863 UTC' as max_created_at
    union all
    select 'posts_answers', 34024119, timestamp '2022-09-25 05:56:36.210 UTC'
),

observed as (
    select 'posts_questions' as source_table, count(*) as n_rows, max(created_at) as max_created_at
    from {{ ref('stg_stackoverflow__questions') }}
    union all
    select 'posts_answers', count(*), max(created_at)
    from {{ ref('stg_stackoverflow__answers') }}
)

select
    e.source_table,
    e.n_rows as expected_rows,
    o.n_rows as observed_rows,
    e.max_created_at as expected_max_created_at,
    o.max_created_at as observed_max_created_at
from expected as e
left join observed as o
    on o.source_table = e.source_table
where o.n_rows != e.n_rows
    or o.max_created_at != e.max_created_at

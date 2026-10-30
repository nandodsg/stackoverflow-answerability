-- Materialized as a view: set for the staging folder in dbt_project.yml.
-- One row per user. Reputation is the value at snapshot time, not at posting time (see specs/000).
select
    id as user_id,
    creation_date as created_at,
    reputation
from {{ source('stackoverflow', 'users') }}

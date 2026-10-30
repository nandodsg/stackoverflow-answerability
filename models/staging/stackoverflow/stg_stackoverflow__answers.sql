-- Materialized as a view: set for the staging folder in dbt_project.yml.
-- One row per answer. `body` is left out on purpose.
select
    id as answer_id,
    parent_id as question_id,
    creation_date as created_at,
    owner_user_id
from {{ source('stackoverflow', 'posts_answers') }}

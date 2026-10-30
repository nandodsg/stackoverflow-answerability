-- Materialized as a view: set for the staging folder in dbt_project.yml.
-- One row per question. `body` is left out on purpose: no model downstream of staging can scan it by accident.
select
    id as question_id,
    creation_date as created_at,
    extract(year from creation_date) as creation_year,
    title,
    tags,
    answer_count,
    accepted_answer_id,
    owner_user_id,
    last_edit_date as last_edited_at
from {{ source('stackoverflow', 'posts_questions') }}

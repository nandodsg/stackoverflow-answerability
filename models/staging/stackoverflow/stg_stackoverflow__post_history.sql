-- Materialized as a view: set for the staging folder in dbt_project.yml.
-- One row per revision, metadata only. `text` (108 GB) is left out on purpose: the original title, body and tags are
-- read once by the full-scan models, which select from the source directly.
-- Holds revisions of answers too, so join to questions before counting question edits.
select
    id as post_history_id,
    post_id,
    post_history_type_id,
    creation_date as created_at,
    user_id
from {{ source('stackoverflow', 'post_history') }}

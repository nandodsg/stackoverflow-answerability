-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag and the partition).
-- THE ONE-TIME TEXT SCAN of posts_questions.body (~36 GB, `full_scan` target only; tagged out of default builds).
-- One row per question created 2018-2022: the same text features as int_post_history_scan, but read from the CURRENT
-- title and body (rendered HTML), so the effect of edits can be compared with the original text (AC-3.5, AC-3.6).
-- For the 5% text sample, the current title and body are stored as well. It cannot share a query with the other scan:
-- the two text reads together bill ~145 GB, above the full_scan cap.
{{
    config(
        tags=['full_scan'],
        partition_by={
            'field': 'creation_year',
            'data_type': 'int64',
            'range': {'start': 2018, 'end': 2023, 'interval': 1},
        }
    )
}}

with inputs as (
    select
        q.id as question_id,
        extract(year from q.creation_date) as creation_year,
        {{ in_text_sample('q.id') }} as is_text_sample,
        q.title as title_raw,
        {{ normalize_text('q.body', 'html') }} as body_norm
    from {{ scan_source(source('stackoverflow', 'posts_questions'), 'q') }}
    where extract(year from q.creation_date) between 2018 and 2022
)

select
    question_id,
    creation_year,
    is_text_sample,
    {{ title_features('title_raw') }},
    {{ body_features('body_norm', 'html') }},
    if(is_text_sample, title_raw, null) as current_title,
    if(is_text_sample, body_norm, null) as current_body_text
from inputs

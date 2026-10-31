-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag and the partition).
-- THE ONE-TIME TEXT SCAN of post_history.text (~109 GB, `full_scan` target only; tagged out of default builds).
-- One row per post: every question created 2018-2022 (the P3 cohort), the 2013-2017 questions whose ORIGINAL tags are
-- exactly `python` or `dbt` (tags only, for P2's impact check), and the answers of the 5% text sample. For each row:
-- the original tags and title, the text features of the original body (Markdown rules), and, for the sample only, the
-- original body text itself. The body is never stored outside the sample.
{{
    config(
        tags=['full_scan'],
        partition_by={
            'field': 'creation_year',
            'data_type': 'int64',
            'range': {'start': 2013, 'end': 2023, 'interval': 1},
        }
    )
}}

with questions as (
    select
        question_id,
        creation_year,
        creation_year >= 2018 as in_p3_cohort,
        creation_year >= 2018 and {{ in_text_sample('question_id') }} as is_text_sample
    from {{ ref('int_questions') }}
    where creation_year between 2013 and 2022
),

sampled_answers as (
    select
        a.answer_id,
        q.creation_year
    from {{ ref('stg_stackoverflow__answers') }} as a
    inner join questions as q
        on q.question_id = a.question_id
    where q.is_text_sample
),

posts as (
    select question_id as post_id, 'question' as post_kind, creation_year, in_p3_cohort, is_text_sample
    from questions
    union all
    select answer_id, 'answer', creation_year, true, true
    from sampled_answers
),

-- Initial title (type 1), initial body (type 2) and initial tags (type 3): the version the asker posted.
-- If a post has two rows of a type, the earliest wins.
initial_versions as (
    select
        h.post_id,
        h.post_history_type_id,
        h.text
    from {{ scan_source(source('stackoverflow', 'post_history'), 'h') }}
    where h.post_history_type_id in (1, 2, 3)
        and h.post_id in (select post_id from posts)
    qualify row_number() over (partition by h.post_id, h.post_history_type_id order by h.creation_date, h.id) = 1
),

versions as (
    select
        post_id,
        max(if(post_history_type_id = 1, text, null)) as title_raw,
        max(if(post_history_type_id = 2, text, null)) as body_raw,
        -- Tags may be stored as |a|b|, <a><b> or ["a","b"]: split on all of those separators.
        regexp_extract_all(max(if(post_history_type_id = 3, text, null)), r'[^|<>\[\]",\s]+') as tag_array
    from initial_versions
    group by post_id
),

inputs as (
    select
        p.post_id,
        p.post_kind,
        p.creation_year,
        p.in_p3_cohort,
        p.is_text_sample,
        v.title_raw,
        v.body_raw,
        {{ normalize_text('v.body_raw', 'markdown') }} as body_norm,
        array_to_string(v.tag_array, '|') as original_tags,
        array_length(v.tag_array) as original_tag_count
    from posts as p
    inner join versions as v
        on v.post_id = p.post_id
)

select
    post_id,
    post_kind,
    creation_year,
    in_p3_cohort,
    is_text_sample,
    if(post_kind = 'question', original_tags, null) as original_tags,
    if(post_kind = 'question', original_tag_count, null) as original_tag_count,
    if(post_kind = 'question' and in_p3_cohort, title_raw, null) as original_title,
    {{ title_features('if(post_kind = "question", title_raw, null)') }},
    {{ body_features('body_norm', 'markdown') }},
    if(is_text_sample, body_raw, null) as original_body_text
from inputs
-- A 2013-2017 question is kept only for its tags, and only if it was originally `python`-only or `dbt`-only.
where in_p3_cohort
    or post_kind = 'answer'
    or original_tags in ('python', 'dbt')

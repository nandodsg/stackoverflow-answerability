-- Materialized as a view: set by the inline config() below (the project default in dbt_project.yml is table).
-- The ANALYSIS set of the P3 quality labels (specs/003, "Quality labels"): a plain random draw of 30,000 questions from
-- the 5% text sample, 2018-2022, that the chosen labeling model labels so the labels can be related to the outcome.
-- One row per question; ids only, never the outcome and never text. The draw is NOT stratified by image (unlike the gold
-- set), so label rates describe the sample as it is.
--   pool       2018-2022 questions of the 5% sample with an original title and body, minus the discovery questions
--              and the 120 gold questions (the labeler was scored on those, so they stay out of the analysis)
-- A view stores nothing (the sandbox storage is full); the order uses farm_fingerprint with its own salt, so the same
-- 30,000 ids come back on every read.
{{ config(materialized='view', tags=['needs_full_scan']) }}

{%- set analysis_size = 30000 %}

with excluded as (
    select accepted_question_id as question_id from {{ ref('int_label_discovery_pairs') }}
    union all
    select unanswered_question_id from {{ ref('int_label_discovery_pairs') }}
    union all
    select question_id from {{ ref('int_label_gold_questions') }}
),

candidates as (
    select
        o.post_id as question_id,
        o.creation_year,
        farm_fingerprint(concat('analysis-question-', cast(o.post_id as string))) as draw
    from {{ ref('int_post_history_scan') }} as o
    inner join {{ ref('int_questions') }} as q
        on q.question_id = o.post_id
    where o.post_kind = 'question'
        and o.is_text_sample
        and o.creation_year between 2018 and 2022
        and o.original_title is not null
        and o.body_length is not null
        and o.post_id not in (select question_id from excluded)
),

ranked as (
    select
        *,
        row_number() over (order by draw, question_id) as analysis_rank
    from candidates
)

select
    question_id,
    analysis_rank,
    creation_year
from ranked
where analysis_rank <= {{ analysis_size }}

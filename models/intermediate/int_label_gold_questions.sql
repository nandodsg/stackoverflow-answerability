-- Materialized as a view: set by the inline config() below (the project default in dbt_project.yml is table).
-- The GOLD set of the P3 quality labels (specs/003, "Quality labels"): 120 questions from the 5% text sample that are
-- labeled by hand on labels/rubric.md, so each candidate labeling model can be scored against them. One row per
-- question; ids and the sampling stratum only, never the outcome (the labeling is blind to it) and never text.
--   pool       2018-2022 questions of the 5% sample with an original title and body, minus the discovery questions
--   practice   20 questions labeled first; disagreements with a model refine the rubric's wording, then it is frozen
--   scoring    100 questions labeled on the frozen rubric; the agreement scores come from these only
--   images     a third of each set has an image (has_image), so image_only_evidence has enough positives to score;
--              everywhere else the draw is plain random
-- A view stores nothing (the sandbox storage is full); the order uses farm_fingerprint with its own salt, so the same
-- 120 ids come back on every read.
{{ config(materialized='view', tags=['needs_full_scan']) }}

{%- set image_quota = {'practice': 7, 'scoring': 33} %}
{%- set other_quota = {'practice': 13, 'scoring': 67} %}

with discovery as (
    select accepted_question_id as question_id from {{ ref('int_label_discovery_pairs') }}
    union all
    select unanswered_question_id from {{ ref('int_label_discovery_pairs') }}
),

candidates as (
    select
        o.post_id as question_id,
        o.creation_year,
        o.has_image,
        farm_fingerprint(concat('gold-question-', cast(o.post_id as string))) as draw
    from {{ ref('int_post_history_scan') }} as o
    inner join {{ ref('int_questions') }} as q
        on q.question_id = o.post_id
    where o.post_kind = 'question'
        and o.is_text_sample
        and o.creation_year between 2018 and 2022
        and o.original_title is not null
        and o.body_length is not null
        and o.post_id not in (select question_id from discovery)
),

-- The first questions of each stratum in draw order go to practice, the next ones to scoring.
ranked as (
    select
        *,
        row_number() over (partition by has_image order by draw, question_id) as rank_in_stratum
    from candidates
),

assigned as (
    select
        *,
        case
            when has_image and rank_in_stratum <= {{ image_quota.practice }} then 'practice'
            when has_image and rank_in_stratum <= {{ image_quota.practice + image_quota.scoring }} then 'scoring'
            when not has_image and rank_in_stratum <= {{ other_quota.practice }} then 'practice'
            when not has_image and rank_in_stratum <= {{ other_quota.practice + other_quota.scoring }} then 'scoring'
        end as gold_set
    from ranked
)

select
    question_id,
    gold_set,
    row_number() over (partition by gold_set order by draw, question_id) as gold_rank,
    creation_year,
    has_image
from assigned
where gold_set is not null

-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag).
-- The DISCOVERY set of the P3 quality labels (specs/003, "Quality labels"): ~200 contrastive pairs from the 5% text
-- sample. Each pair is two questions with the same primary tag, the same year and the same has-code-block value, one
-- with an accepted answer and one with no answer at all, so what differs between them is mostly how they are written.
-- A language model reads the pairs and proposes candidate labels. One row per pair; question ids only, never text
-- (the labeling script reads the text of these ids from int_post_history_scan).
--   years          2018-2021: a 2022 question may be unanswered only because it is young (data ends 2022-09-25)
--   accepted       accepted answer written by someone else; self-accepted questions ("how I solved it") are left out
--   unanswered     answer_count = 0; answered-but-not-accepted questions are in neither group
--   spread         50 pairs per year, at most 3 per (primary tag, year), chosen in a fixed pseudo-random order
-- The order uses farm_fingerprint with a salt, so it is the same on every run and unrelated to the 5% sample's own hash.
-- The gold and analysis sets are drawn later from the sample questions NOT in this table.
{{ config(tags=['needs_full_scan']) }}

{%- set pairs_per_year = 50 %}
{%- set max_pairs_per_tag_year = 3 %}

with candidates as (
    select
        q.question_id,
        q.creation_year,
        split(o.original_tags, '|')[safe_offset(0)] as primary_tag,
        o.has_code_block,
        if(q.has_accepted_answer, 'accepted', 'unanswered') as outcome,
        farm_fingerprint(concat('discovery-question-', cast(q.question_id as string))) as draw
    from {{ ref('int_questions') }} as q
    inner join {{ ref('int_post_history_scan') }} as o
        on o.post_id = q.question_id
        and o.post_kind = 'question'
        and o.creation_year between 2018 and 2021
    left join {{ ref('stg_stackoverflow__answers') }} as a
        on a.answer_id = q.accepted_answer_id
    where q.creation_year between 2018 and 2021
        and o.is_text_sample
        and o.original_title is not null
        and o.original_body_text is not null
        and (
            (q.has_accepted_answer and a.owner_user_id is distinct from q.owner_user_id)
            or not q.is_answered
        )
),

-- Within each (year, tag, code) cell, the n-th accepted question in draw order is paired with the n-th unanswered one.
ranked as (
    select
        *,
        row_number() over (
            partition by creation_year, primary_tag, has_code_block, outcome order by draw, question_id
        ) as rank_in_cell
    from candidates
),

all_pairs as (
    select
        acc.creation_year,
        acc.primary_tag,
        acc.has_code_block,
        acc.question_id as accepted_question_id,
        una.question_id as unanswered_question_id,
        farm_fingerprint(concat('discovery-pair-', cast(acc.question_id as string), '-', cast(una.question_id as string)))
            as pair_draw
    from ranked as acc
    inner join ranked as una
        on una.creation_year = acc.creation_year
        and una.primary_tag = acc.primary_tag
        and una.has_code_block = acc.has_code_block
        and una.rank_in_cell = acc.rank_in_cell
        and una.outcome = 'unanswered'
    where acc.outcome = 'accepted'
),

capped as (
    select *
    from all_pairs
    qualify row_number() over (partition by creation_year, primary_tag order by pair_draw) <= {{ max_pairs_per_tag_year }}
),

chosen as (
    select
        *,
        row_number() over (partition by creation_year order by pair_draw) as pair_rank_in_year
    from capped
    qualify pair_rank_in_year <= {{ pairs_per_year }}
)

select
    concat(cast(creation_year as string), '-', format('%02d', pair_rank_in_year)) as pair_id,
    creation_year,
    pair_rank_in_year,
    primary_tag,
    has_code_block,
    accepted_question_id,
    unanswered_question_id
from chosen

-- Re-checks the gold set of the quality labels against the source tables, not against the model's own logic.
-- Any row returned names a question (or a set) and the rule it breaks.
{{ config(tags=['needs_full_scan']) }}

with gold as (
    select * from {{ ref('int_label_gold_questions') }}
),

discovery as (
    select accepted_question_id as question_id from {{ ref('int_label_discovery_pairs') }}
    union all
    select unanswered_question_id from {{ ref('int_label_discovery_pairs') }}
),

question_checks as (
    select
        cast(g.question_id as string) as item,
        case
            when q.question_id is null or o.post_id is null then 'question missing from the sources'
            when not o.is_text_sample then 'question outside the 5% text sample'
            when o.creation_year not between 2018 and 2022 then 'year outside 2018-2022'
            when o.original_title is null or o.body_length is null then 'no original title or body'
            when g.question_id in (select question_id from discovery) then 'question is in the discovery set'
            when g.has_image != o.has_image then 'has_image differs from the scan'
        end as problem
    from gold as g
    left join {{ ref('int_questions') }} as q
        on q.question_id = g.question_id
    left join {{ ref('int_post_history_scan') }} as o
        on o.post_id = g.question_id
        and o.post_kind = 'question'
),

set_sizes as (
    select
        gold_set as item,
        'wrong size or image share' as problem
    from gold
    group by gold_set
    having not (
        (gold_set = 'practice' and count(*) = 20 and countif(has_image) = 7)
        or (gold_set = 'scoring' and count(*) = 100 and countif(has_image) = 33)
    )
)

select * from question_checks where problem is not null
union all
select * from set_sizes

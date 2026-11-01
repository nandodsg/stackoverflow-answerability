-- Re-checks the analysis set of the quality labels against the source tables, not against the model's own logic.
-- Any row returned names a question (or the set) and the rule it breaks.
{{ config(tags=['needs_full_scan']) }}

with analysis as (
    select * from {{ ref('int_label_analysis_questions') }}
),

excluded as (
    select accepted_question_id as question_id from {{ ref('int_label_discovery_pairs') }}
    union all
    select unanswered_question_id from {{ ref('int_label_discovery_pairs') }}
    union all
    select question_id from {{ ref('int_label_gold_questions') }}
),

question_checks as (
    select
        cast(a.question_id as string) as item,
        case
            when q.question_id is null or o.post_id is null then 'question missing from the sources'
            when not o.is_text_sample then 'question outside the 5% text sample'
            when o.creation_year not between 2018 and 2022 then 'year outside 2018-2022'
            when o.creation_year != a.creation_year then 'creation_year differs from the scan'
            when o.original_title is null or o.body_length is null then 'no original title or body'
            when a.question_id in (select question_id from excluded) then 'question is in the discovery or gold set'
        end as problem
    from analysis as a
    left join {{ ref('int_questions') }} as q
        on q.question_id = a.question_id
    left join {{ ref('int_post_history_scan') }} as o
        on o.post_id = a.question_id
        and o.post_kind = 'question'
),

set_size as (
    select 'set size' as item, 'not 30,000 rows' as problem
    from (select count(*) as n from analysis)
    where n != 30000
)

select item, problem from question_checks where problem is not null
union all
select item, problem from set_size

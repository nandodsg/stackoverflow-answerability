-- Re-checks the discovery pairs of the quality labels against the source tables, not against the model's own logic.
-- Any row returned names a pair (or a year, or a tag) and the rule it breaks.
{{ config(tags=['needs_full_scan']) }}

with pairs as (
    select * from {{ ref('int_label_discovery_pairs') }}
),

question_facts as (
    select
        q.question_id,
        q.creation_year,
        q.answer_count,
        q.has_accepted_answer,
        q.owner_user_id,
        a.owner_user_id as accepted_answer_owner_id,
        o.is_text_sample,
        o.has_code_block,
        split(o.original_tags, '|')[safe_offset(0)] as primary_tag
    from {{ ref('int_questions') }} as q
    inner join {{ ref('int_post_history_scan') }} as o
        on o.post_id = q.question_id
        and o.post_kind = 'question'
    left join {{ ref('stg_stackoverflow__answers') }} as a
        on a.answer_id = q.accepted_answer_id
    where q.question_id in (
        select accepted_question_id from pairs
        union all
        select unanswered_question_id from pairs
    )
),

pair_checks as (
    select
        p.pair_id,
        case
            when acc.question_id is null or una.question_id is null then 'question missing from the sources'
            when not (acc.is_text_sample and una.is_text_sample) then 'question outside the 5% text sample'
            when acc.creation_year != p.creation_year or una.creation_year != p.creation_year then 'year differs'
            when acc.primary_tag != p.primary_tag or una.primary_tag != p.primary_tag then 'primary tag differs'
            when acc.has_code_block != una.has_code_block then 'has_code_block differs'
            when not acc.has_accepted_answer then 'accepted side has no accepted answer'
            when acc.accepted_answer_owner_id = acc.owner_user_id then 'accepted side is self-accepted'
            when una.answer_count != 0 then 'unanswered side has answers'
        end as problem
    from pairs as p
    left join question_facts as acc
        on acc.question_id = p.accepted_question_id
    left join question_facts as una
        on una.question_id = p.unanswered_question_id
),

reused as (
    select cast(question_id as string) as pair_id, 'question in two pairs' as problem
    from (
        select accepted_question_id as question_id from pairs
        union all
        select unanswered_question_id from pairs
    )
    group by question_id
    having count(*) > 1
),

per_year as (
    select cast(creation_year as string) as pair_id, 'not 50 pairs in the year' as problem
    from pairs
    group by creation_year
    having count(*) != 50
),

per_tag as (
    select concat(cast(creation_year as string), ' ', primary_tag) as pair_id, 'more than 3 pairs in a (tag, year)' as problem
    from pairs
    group by creation_year, primary_tag
    having count(*) > 3
)

select * from pair_checks where problem is not null
union all
select * from reused
union all
select * from per_year
union all
select * from per_tag

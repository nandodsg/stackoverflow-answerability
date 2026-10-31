-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag).
-- Prompt 3, answer lens (specs/003): among the answers of the 5% text sample, which body qualities go with being the
-- accepted answer. One row per feature x bucket x cohort (each year of the QUESTION, 2018-2022, and '2018-2021'), with
-- the acceptance rate, its Wilson bounds, and the difference from the reference bucket. Original answer text only
-- (int_post_history_scan, Markdown rules). Answer text cannot explain whether a question is answered at all, so this
-- lens is about acceptance only and is reported apart from the question features.
{{ config(tags=['needs_full_scan']) }}

{%- set features = p3_answer_features() %}

with answers as (
    select
        s.creation_year,
        q.accepted_answer_id = s.post_id as is_accepted,
        {%- for feature in features %}
        {{ p3_bucket(feature, 's.' ~ feature) }} as {{ feature }}{% if not loop.last %},{% endif %}
        {%- endfor %}
    from {{ ref('int_post_history_scan') }} as s
    inner join {{ ref('stg_stackoverflow__answers') }} as a
        on a.answer_id = s.post_id
    inner join {{ ref('int_questions') }} as q
        on q.question_id = a.question_id
        and q.creation_year between 2018 and 2022
    where s.post_kind = 'answer'
        and s.creation_year between 2018 and 2022
),

by_year as (
    select
        feature,
        bucket,
        cast(creation_year as string) as cohort,
        count(*) as n_answers,
        countif(coalesce(is_accepted, false)) as n_accepted
    from answers
    unpivot (bucket for feature in ({{ features | join(', ') }}))
    group by feature, bucket, creation_year
),

cohorts as (
    select * from by_year
    union all
    select feature, bucket, '2018-2021', sum(n_answers), sum(n_accepted)
    from by_year
    where cohort in ('2018', '2019', '2020', '2021')
    group by feature, bucket
),

rates as (
    select
        *,
        starts_with(bucket, '1:') as is_reference_bucket,
        cohort = '2022' as is_partial_year,
        {{ p3_rate_with_bounds('n_accepted', 'n_answers', 'acceptance_rate') }}
    from cohorts
)

select
    b.*,
    if(b.is_reference_bucket, null, b.acceptance_rate - r.acceptance_rate) as acceptance_rate_effect,
    if(b.is_reference_bucket, null,
        {{ p3_difference_margin('b.acceptance_rate', 'b.n_answers', 'r.acceptance_rate', 'r.n_answers') }})
        as acceptance_rate_effect_margin
from rates as b
left join rates as r
    on r.feature = b.feature
    and r.cohort = b.cohort
    and r.is_reference_bucket

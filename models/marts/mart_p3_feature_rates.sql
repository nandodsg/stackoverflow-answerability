-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag).
-- Prompt 3, rates by bucket: one row per version x feature x bucket x cohort, with n, answer rate, accepted rate (both
-- out of all questions, D2) and accepted among answered, each with its 95% Wilson bounds. Cohorts are each year 2018-2022
-- and the four full years together ('2018-2021'); 2022 is partial (censored) and flagged.
{{ config(tags=['needs_full_scan']) }}

with by_year as (
    select
        version,
        feature,
        bucket,
        cast(creation_year as string) as cohort,
        sum(n_questions) as n_questions,
        sum(n_answered) as n_answered,
        sum(n_accepted) as n_accepted
    from {{ ref('int_p3_bucket_counts') }}
    group by version, feature, bucket, creation_year
),

full_years as (
    select
        version,
        feature,
        bucket,
        '2018-2021' as cohort,
        sum(n_questions) as n_questions,
        sum(n_answered) as n_answered,
        sum(n_accepted) as n_accepted
    from by_year
    where cohort in ('2018', '2019', '2020', '2021')
    group by version, feature, bucket
),

cohorts as (
    select * from by_year
    union all
    select * from full_years
)

select
    version,
    feature,
    bucket,
    cohort,
    starts_with(bucket, '1:') as is_reference_bucket,
    cohort = '2022' as is_partial_year,
    n_questions,
    n_answered,
    n_accepted,
    {{ p3_rate_with_bounds('n_answered', 'n_questions', 'answer_rate') }},
    {{ p3_rate_with_bounds('n_accepted', 'n_questions', 'accepted_rate') }},
    {{ p3_rate_with_bounds('n_accepted', 'n_answered', 'accepted_rate_among_answered') }}
from cohorts

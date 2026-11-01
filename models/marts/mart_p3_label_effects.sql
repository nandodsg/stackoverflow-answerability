-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag).
-- Prompt 3, effects of the quality labels (`feature` = label, `bucket` = level; a copy of mart_p3_feature_effects on the
-- 30,000 labeled questions, whose versions are original / never_edited / not_edited_after_answer). One row per version x
-- label x non-reference level x cohort.
--   full_years_with_effect  how many of the four full years reach the floor (bucket and reference >= 385 questions);
--                     only 4 can show stability: a rare level (e.g. multiple asks, dump code) has fewer, and its
--                     *_stable flags are false because stability is NOT ASSESSABLE there, not because it flips
-- Prompt 3, effects: one row per version x feature x non-reference bucket x cohort. For each rate:
--   *_effect          the bucket's rate minus the reference bucket's rate (bucket '1:'), in the same version and cohort
--   *_effect_margin   half-width of its 95% interval: the effect is clearly not zero when |effect| > margin
--   *_effect_stable   AC-3.3: the effect points the same way in each full year 2018-2021 (2022 is partial, not used)
--   *_effect_tag_adjusted  the topic control: the same difference measured inside each primary-tag stratum (20 largest
--                     tags + '(other)'), then averaged with each stratum weighted by its questions in the bucket. Strata
--                     where the bucket or the reference has fewer than 30 questions are skipped; tag_adjusted_coverage
--                     is the share of the bucket's questions kept. If the adjusted effect shrinks towards 0, most of the
--                     raw effect was topic.
--   *_effect_flips_vs_original  AC-3.5: the effect points the other way than on the original text (same feature,
--                     bucket and cohort); false on the original version itself
-- A bucket (or its reference) with fewer than 385 questions in a cohort has no row there: the same floor as P1 (D1),
-- which keeps a rate within about +-5 points. So the 2 questions with no original body are not reported as a bucket.
{{ config(tags=['needs_full_scan']) }}

{%- set rates = ['answer_rate', 'accepted_rate', 'accepted_rate_among_answered'] %}
{%- set denominators = {'answer_rate': 'n_questions', 'accepted_rate': 'n_questions', 'accepted_rate_among_answered': 'n_answered'} %}
{%- set full_years = "('2018', '2019', '2020', '2021')" %}

with rates as (
    select * from {{ ref('mart_p3_label_rates') }}
),

raw_effects as (
    select
        b.version,
        b.feature,
        b.bucket,
        b.cohort,
        b.is_partial_year,
        b.n_questions,
        r.n_questions as reference_n_questions,
        {%- for rate in rates %}
        b.{{ rate }} - r.{{ rate }} as {{ rate }}_effect,
        {{ p3_difference_margin('b.' ~ rate, 'b.' ~ denominators[rate], 'r.' ~ rate, 'r.' ~ denominators[rate]) }}
            as {{ rate }}_effect_margin{% if not loop.last %},{% endif %}
        {%- endfor %}
    from rates as b
    inner join rates as r
        on r.version = b.version
        and r.feature = b.feature
        and r.cohort = b.cohort
        and r.is_reference_bucket
    where not b.is_reference_bucket
        and b.n_questions >= {{ var('min_questions', 385) }}
        and r.n_questions >= {{ var('min_questions', 385) }}
),

-- Stratum counts per year, plus the four full years summed, as in mart_p3_label_rates.
strata as (
    select version, feature, bucket, cast(creation_year as string) as cohort, tag_stratum,
        n_questions, n_answered, n_accepted
    from {{ ref('int_p3_label_bucket_counts') }}
    union all
    select version, feature, bucket, '2018-2021', tag_stratum,
        sum(n_questions), sum(n_answered), sum(n_accepted)
    from {{ ref('int_p3_label_bucket_counts') }}
    where creation_year between 2018 and 2021
    group by version, feature, bucket, tag_stratum
),

stratum_rates as (
    select
        *,
        safe_divide(n_answered, n_questions) as answer_rate,
        safe_divide(n_accepted, n_questions) as accepted_rate,
        safe_divide(n_accepted, n_answered) as accepted_rate_among_answered
    from strata
),

tag_adjusted as (
    select
        b.version,
        b.feature,
        b.bucket,
        b.cohort,
        {%- for rate in rates %}
        safe_divide(
            sum(if(b.n_questions >= 30 and r.n_questions >= 30, b.n_questions * (b.{{ rate }} - r.{{ rate }}), 0)),
            sum(if(b.n_questions >= 30 and r.n_questions >= 30 and b.{{ rate }} is not null and r.{{ rate }} is not null, b.n_questions, 0))
        ) as {{ rate }}_effect_tag_adjusted,
        {%- endfor %}
        safe_divide(sum(if(b.n_questions >= 30 and r.n_questions >= 30, b.n_questions, 0)), sum(b.n_questions))
            as tag_adjusted_coverage
    from stratum_rates as b
    left join stratum_rates as r
        on r.version = b.version
        and r.feature = b.feature
        and r.cohort = b.cohort
        and r.tag_stratum = b.tag_stratum
        and starts_with(r.bucket, '1:')
    where not starts_with(b.bucket, '1:')
    group by b.version, b.feature, b.bucket, b.cohort
),

combined as (
    select
        e.*,
        {%- for rate in rates %}
        a.{{ rate }}_effect_tag_adjusted,
        {%- endfor %}
        a.tag_adjusted_coverage
    from raw_effects as e
    left join tag_adjusted as a
        on a.version = e.version
        and a.feature = e.feature
        and a.bucket = e.bucket
        and a.cohort = e.cohort
),

with_flips as (
    select
        c.*,
        {%- for rate in rates %}
        coalesce(sign(c.{{ rate }}_effect) != sign(o.{{ rate }}_effect), false)
            as {{ rate }}_effect_flips_vs_original{% if not loop.last %},{% endif %}
        {%- endfor %}
    from combined as c
    left join combined as o
        on o.feature = c.feature
        and o.bucket = c.bucket
        and o.cohort = c.cohort
        and o.version = 'original'
)

select
    *,
    countif(cohort in {{ full_years }} and accepted_rate_effect is not null)
        over (partition by version, feature, bucket) as full_years_with_effect,
    -- Stable = same sign in all four full years: four positive or four negative effects.
    {%- for rate in rates %}
    {%- set rate_loop = loop %}
    {%- for kind in ['', '_tag_adjusted'] %}
    countif(cohort in {{ full_years }} and {{ rate }}_effect{{ kind }} > 0)
        over (partition by version, feature, bucket) = 4
    or countif(cohort in {{ full_years }} and {{ rate }}_effect{{ kind }} < 0)
        over (partition by version, feature, bucket) = 4
        as {{ rate }}_effect{{ kind }}_stable{% if not (loop.last and rate_loop.last) %},{% endif %}
    {%- endfor %}
    {%- endfor %}
from with_flips

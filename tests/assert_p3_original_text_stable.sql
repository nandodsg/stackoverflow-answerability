-- AC-0.10 / AC-3.6, prompt 3 impact check (severity: warn). Each feature effect on the ORIGINAL text against the same
-- effect on the CURRENT text, over the four full years (2018-2021). A row returned here is an effect that points one way
-- on one text and the other way on the other, where at least one of the two is clearly not zero (|effect| > margin),
-- so noise around zero does not count as a flip. It warns instead of failing: every warning is listed in the README.
{{ config(severity='warn', tags=['needs_full_scan'], meta={'ac': 'AC-0.10', 'also': 'AC-3.6'}) }}

with effects as (
    select * from {{ ref('mart_p3_feature_effects') }}
    where cohort = '2018-2021'
),

compared as (
    {%- for rate in ['answer_rate', 'accepted_rate', 'accepted_rate_among_answered'] %}
    select
        o.feature,
        o.bucket,
        '{{ rate }}' as rate,
        o.{{ rate }}_effect as original_effect,
        c.{{ rate }}_effect as current_effect,
        o.{{ rate }}_effect_margin as original_margin,
        c.{{ rate }}_effect_margin as current_margin
    from effects as o
    inner join effects as c
        on c.feature = o.feature
        and c.bucket = o.bucket
        and c.version = 'current'
    where o.version = 'original'
    {% if not loop.last %}union all{% endif %}
    {%- endfor %}
)

select *
from compared
where sign(original_effect) != sign(current_effect)
    and (abs(original_effect) > original_margin or abs(current_effect) > current_margin)

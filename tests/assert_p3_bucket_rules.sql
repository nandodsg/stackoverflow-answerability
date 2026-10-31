-- Hand-written examples for the P3 bucket rules in macros/p3_features.sql: each row is a value and the bucket we
-- expect, with the edges written out (999 characters is still 500-999; 1000 is 1000-1999). Any row returned is an
-- example where a rule gives a different bucket. Reads no table, so it bills nothing.
{{ config(meta={'ac': 'AC-3.3'}) }}

with cases as (
    select * from unnest([
        struct('body_length' as feature, 499 as value, '1: <500' as expected),
        ('body_length', 500, '2: 500-999'),
        ('body_length', 999, '2: 500-999'),
        ('body_length', 1000, '3: 1000-1999'),
        ('body_length', 4000, '5: 4000+'),
        ('title_length', 39, '1: <40'),
        ('title_length', 80, '4: 80+'),
        ('code_block_count', 0, '1: 0'),
        ('code_block_count', 2, '3: 2'),
        ('code_block_count', 7, '4: 3+'),
        ('link_count', 1, '2: 1'),
        ('tag_count', 6, '5: 5+'),
        ('hour_posted_utc', 5, '1: 00-05'),
        ('hour_posted_utc', 23, '4: 18-23'),
        ('weekday_posted', 1, '7: Sun'),
        ('weekday_posted', 2, '1: Mon'),
        ('posted_on_weekend', 7, '2: yes'),
        ('posted_on_weekend', 4, '1: no'),
        ('asker_account_age', 0, '1: under 1 day'),
        ('asker_account_age', 400, '4: 1-3 years'),
        ('asker_account_age', null, '9: unknown'),
        ('asker_account_age', -5, '9: unknown'),
        ('asker_prior_questions', 0, '1: 0 (first question)'),
        ('asker_prior_questions', 20, '4: 20+')
    ])
),

flag_cases as (
    select * from unnest([
        struct(true as value, '2: yes' as expected),
        (false, '1: no'),
        (null, '9: unknown')
    ])
),

bucketed as (
    select
        feature,
        value,
        expected,
        case feature
            {%- for feature in ['body_length', 'title_length', 'code_block_count', 'link_count', 'tag_count',
                'hour_posted_utc', 'weekday_posted', 'posted_on_weekend', 'asker_account_age', 'asker_prior_questions'] %}
            when '{{ feature }}' then {{ p3_bucket(feature, 'value') }}
            {%- endfor %}
        end as actual
    from cases
    union all
    select 'has_code_block', null, expected, {{ p3_bucket('has_code_block', 'value') }}
    from flag_cases
)

select *
from bucketed
where actual is distinct from expected

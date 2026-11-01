-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag).
-- AC-3.8, does a label add anything beyond the rules? For each label level (not the reference), the difference in
-- accepted rate against the reference level, over the labeled questions of 2018-2021 (original text), measured
--   raw_effect             overall
--   rules_adjusted_effect  inside each stratum of the rule-based features that sit closest (has a code block x body
--                          length bucket, 2 x 5 = 10 strata), then averaged with each stratum weighted by the level's
--                          questions in it; strata where the level or the reference has fewer than 30 questions are
--                          skipped (adjusted_coverage = share of the level's questions kept)
-- If the adjusted effect stays near the raw one, the label carries information the rules do not (e.g. among questions
-- with equal code and length, a worked example still goes with more accepted answers). If it shrinks towards 0, the
-- rules already explained it. Correlation language only: the labels are judgments, the outcome is observational.
{{ config(tags=['needs_full_scan']) }}

{%- set min_stratum = 30 %}

with questions as (
    select
        *,
        concat({{ p3_bucket('has_code_block', 'has_code_block') }}, ' / ', {{ p3_bucket('body_length', 'body_length') }})
            as rule_stratum
    from {{ ref('int_p3_label_questions') }}
    where creation_year between 2018 and 2021
),

long as (
    select rule_stratum, has_accepted_answer, label, level
    from questions
    unpivot (level for label in ({{ p3_label_names() | join(', ') }}))
),

by_stratum as (
    select label, level, rule_stratum, count(*) as n_questions, countif(has_accepted_answer) as n_accepted
    from long
    group by label, level, rule_stratum
),

overall as (
    select label, level, sum(n_questions) as n_questions, sum(n_accepted) as n_accepted
    from by_stratum
    group by label, level
),

raw_effects as (
    select
        l.label,
        l.level,
        l.n_questions,
        r.n_questions as reference_n_questions,
        safe_divide(l.n_accepted, l.n_questions) - safe_divide(r.n_accepted, r.n_questions) as raw_effect
    from overall as l
    inner join overall as r
        on r.label = l.label
        and starts_with(r.level, '1:')
    where not starts_with(l.level, '1:')
),

adjusted as (
    select
        l.label,
        l.level,
        safe_divide(
            sum(if(l.n_questions >= {{ min_stratum }} and r.n_questions >= {{ min_stratum }},
                l.n_questions * (safe_divide(l.n_accepted, l.n_questions) - safe_divide(r.n_accepted, r.n_questions)), 0)),
            sum(if(l.n_questions >= {{ min_stratum }} and r.n_questions >= {{ min_stratum }}, l.n_questions, 0))
        ) as rules_adjusted_effect,
        safe_divide(
            sum(if(l.n_questions >= {{ min_stratum }} and r.n_questions >= {{ min_stratum }}, l.n_questions, 0)),
            sum(l.n_questions)
        ) as adjusted_coverage
    from by_stratum as l
    inner join by_stratum as r
        on r.label = l.label
        and r.rule_stratum = l.rule_stratum
        and starts_with(r.level, '1:')
    where not starts_with(l.level, '1:')
    group by l.label, l.level
)

select
    e.label,
    e.level,
    e.n_questions,
    e.reference_n_questions,
    e.raw_effect,
    a.rules_adjusted_effect,
    a.adjusted_coverage
from raw_effects as e
left join adjusted as a
    on a.label = e.label
    and a.level = e.level

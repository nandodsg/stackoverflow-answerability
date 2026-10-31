-- AC-0.10 / AC-2.6, prompt 2 impact check (severity: warn). mart_p2_python_dbt (current tags) against
-- mart_p2_python_dbt_original (original tags), per (tag, year). A row returned here has at least one of:
--   * a different number of questions being present (one version empty, the other not),
--   * a YoY change of answers per question or accepted rate that switches direction,
--   * a value that moves by more than the half-width of that year's 95% interval on the current tags.
-- Warns instead of failing; every warning is listed in the README.
{{ config(severity='warn', tags=['needs_full_scan'], meta={'ac': 'AC-0.10', 'also': 'AC-2.6'}) }}

select
    c.tag,
    c.creation_year,
    c.n_questions as current_n,
    o.n_questions as original_n,
    c.answers_per_question as current_apq,
    o.answers_per_question as original_apq,
    c.accepted_rate as current_accepted,
    o.accepted_rate as original_accepted,
    sign(c.answers_per_question_yoy_abs) != sign(o.answers_per_question_yoy_abs) as apq_yoy_switches,
    sign(c.accepted_rate_yoy_pp) != sign(o.accepted_rate_yoy_pp) as accepted_yoy_switches
from {{ ref('mart_p2_python_dbt') }} as c
inner join {{ ref('mart_p2_python_dbt_original') }} as o
    on o.tag = c.tag and o.creation_year = c.creation_year
where (c.n_questions > 0) != (o.n_questions > 0)
    or sign(c.answers_per_question_yoy_abs) != sign(o.answers_per_question_yoy_abs)
    or sign(c.accepted_rate_yoy_pp) != sign(o.accepted_rate_yoy_pp)
    or abs(c.answers_per_question - o.answers_per_question) > (c.answers_per_question_upper - c.answers_per_question_lower) / 2
    or abs(c.accepted_rate - o.accepted_rate) > (c.accepted_rate_upper - c.accepted_rate_lower) / 2

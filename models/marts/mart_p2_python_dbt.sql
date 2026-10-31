-- Materialized as a table: project default in dbt_project.yml.
-- Prompt 2 (specs/002): questions whose current tags are EXACTLY `python` or EXACTLY `dbt` (one tag, no others), one row
-- per (tag, creation year) for 2013-2022. Years with no question stay as rows of zeros (AC-2.2). Answers per question
-- is the headline ratio (D3) with its 95% interval; questions per answer (Q÷A = 1 / answers per question) is kept as
-- the inverse, shown once in the README. 2022 stops on 2022-09-25 and is flagged partial (AC-2.4).
with calendar as (
    select tag, creation_year
    from unnest(['python', 'dbt']) as tag
    cross join unnest(generate_array(2013, 2022)) as creation_year
),

questions as (
    select
        q.tags as tag,
        q.creation_year,
        q.answer_count,
        q.is_answered,
        q.has_accepted_answer,
        e.tags_exposed
    from {{ ref('int_questions') }} as q
    inner join {{ ref('int_question_exposure') }} as e
        on e.question_id = q.question_id
    where q.tags in ('python', 'dbt')
        and q.creation_year between 2013 and 2022
),

aggregated as (
    select
        c.tag,
        c.creation_year,
        count(q.tag) as n_questions,
        countif(q.is_answered) as n_answered,
        countif(q.has_accepted_answer) as n_accepted,
        coalesce(sum(q.answer_count), 0) as n_answers,
        coalesce(sum(pow(q.answer_count, 2)), 0) as sum_sq_answers,
        coalesce(sum(pow(q.answer_count, 3)), 0) as sum_cube_answers,
        countif(q.tags_exposed) as n_tags_exposed
    from calendar as c
    left join questions as q
        on q.tag = c.tag and q.creation_year = c.creation_year
    group by c.tag, c.creation_year
),

metrics as (
    select
        *,
        {{ group_metrics() }}
    from aggregated
)

select
    *,
    creation_year = 2022 as is_partial_year,
    safe_divide(n_questions, n_answers) as questions_per_answer,
    -- The interval of Q÷A is the inverted interval of answers per question.
    safe_divide(1, answers_per_question_upper) as questions_per_answer_lower,
    safe_divide(1, answers_per_question_lower) as questions_per_answer_upper,
    -- Year over year, within each tag. Absolute change is the main number, relative change sits beside it (AC-2.5).
    answers_per_question - lag(answers_per_question) over (partition by tag order by creation_year) as answers_per_question_yoy_abs,
    safe_divide(
        answers_per_question - lag(answers_per_question) over (partition by tag order by creation_year),
        lag(answers_per_question) over (partition by tag order by creation_year)
    ) as answers_per_question_yoy_rel,
    accepted_rate - lag(accepted_rate) over (partition by tag order by creation_year) as accepted_rate_yoy_pp
from metrics

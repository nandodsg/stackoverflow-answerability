-- Materialized as a table: project default in dbt_project.yml.
-- Data profile (specs/000): one row per year with the volumes and the source checks of AC-0.2–0.4, so the profile
-- rebuilds with `dbt build` instead of living in a one-off script. Question columns count by the question's
-- creation year; answer columns by the answer's own creation year.

with questions as (
    select
        creation_year as year,
        count(*) as n_questions,
        countif(is_answered) as n_answered,
        countif(has_accepted_answer) as n_accepted,
        sum(answer_count) as n_answers_counted,
        sum(n_answers_joined) as n_answers_joined,
        countif(answer_count != n_answers_joined) as n_answer_count_gap_questions
    from {{ ref('int_questions') }}
    group by year
),

accepted_exceptions as (
    select
        q.creation_year as year,
        count(*) as n_accepted_answer_exceptions
    from {{ ref('int_questions') }} as q
    left join {{ ref('stg_stackoverflow__answers') }} as a
        on a.answer_id = q.accepted_answer_id
    where q.accepted_answer_id is not null
        and (a.answer_id is null or a.question_id != q.question_id)
    group by year
),

answers as (
    select
        extract(year from a.created_at) as year,
        count(*) as n_answers_created,
        countif(q.question_id is null) as n_orphan_answers
    from {{ ref('stg_stackoverflow__answers') }} as a
    left join {{ ref('stg_stackoverflow__questions') }} as q
        on q.question_id = a.question_id
    group by year
)

select
    year,
    coalesce(q.n_questions, 0) as n_questions,
    coalesce(q.n_answered, 0) as n_answered,
    coalesce(q.n_accepted, 0) as n_accepted,
    coalesce(q.n_answers_counted, 0) as n_answers_counted,
    coalesce(q.n_answers_joined, 0) as n_answers_joined,
    coalesce(q.n_answer_count_gap_questions, 0) as n_answer_count_gap_questions,
    coalesce(x.n_accepted_answer_exceptions, 0) as n_accepted_answer_exceptions,
    coalesce(a.n_answers_created, 0) as n_answers_created,
    coalesce(a.n_orphan_answers, 0) as n_orphan_answers
from questions as q
full outer join answers as a using (year)
left join accepted_exceptions as x using (year)
order by year

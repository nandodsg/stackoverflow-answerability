-- D3 EDA: answers per question for questions tagged with exactly one tag ('python' or 'dbt'), by creation year.
--
-- Grain: one row per (tag, creation year), 2013-2022. 2022 is partial (data ends 2022-09-25).
-- Answers are attributed to their question's creation year (cohort view, specs/002).
-- Two answer counts: the question's own answer_count, and answers actually present in posts_answers (AC-0.4).
-- sum_answer_count_sq gives the per-question variance, for the standard error of answers per question.
-- Reads only id, tags, creation_date, answer_count and posts_answers.parent_id: title and body are never scanned.

with questions as (
    select
        q.id,
        q.tags as tag,
        extract(year from q.creation_date) as creation_year,
        q.answer_count
    from `bigquery-public-data.stackoverflow.posts_questions` as q
    where q.tags in ('python', 'dbt')
        and extract(year from q.creation_date) between 2013 and 2022
),

joined_answers as (
    select a.parent_id as question_id, count(*) as n_joined
    from `bigquery-public-data.stackoverflow.posts_answers` as a
    where a.parent_id in (select id from questions)
    group by a.parent_id
)

select
    q.tag,
    q.creation_year,
    count(*) as n_questions,
    countif(q.answer_count = 0) as n_unanswered,
    sum(q.answer_count) as n_answers,
    sum(q.answer_count * q.answer_count) as sum_answer_count_sq,
    max(q.answer_count) as max_answers,
    sum(coalesce(j.n_joined, 0)) as n_answers_joined
from questions as q
left join joined_answers as j on j.question_id = q.id
group by q.tag, q.creation_year
order by q.tag, q.creation_year

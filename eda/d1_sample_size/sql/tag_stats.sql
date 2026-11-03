-- D1 EDA: sample size and outcomes per tag, for questions created in @year.
--
-- Grain: one row per tag. A question with 3 tags counts once for each of its tags.
-- Reads only id, tags, creation_date, answer_count and accepted_answer_id: title and body are never scanned.
-- answer_count is the question's own counter; it matches the joined posts_answers for every question (AC-0.4, a dbt test).
-- In the BigQuery console, replace @year with a literal (e.g. 2022).

with question_tags as (
    select
        q.id as question_id,
        tag,
        q.answer_count,
        q.accepted_answer_id is not null as has_accepted_answer
    from `bigquery-public-data.stackoverflow.posts_questions` as q,
        unnest(split(q.tags, '|')) as tag
    where extract(year from q.creation_date) = @year
)

select
    tag,
    count(*) as n_questions,
    countif(answer_count > 0) as n_answered,
    countif(has_accepted_answer) as n_accepted,
    sum(answer_count) as n_answers
from question_tags
group by tag
order by n_questions desc

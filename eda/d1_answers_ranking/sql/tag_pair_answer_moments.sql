-- D1 EDA, answers-per-question ranking: per-tag-pair moments of answer_count, for questions created in @year.
--
-- Grain: one row per unordered tag pair with at least @min_questions questions. Same columns as
-- tag_answer_moments.sql.
-- Reads only id, tags, creation_date and answer_count: title and body are never scanned.
-- In the BigQuery console, replace @year and @min_questions with literals (e.g. 2022 and 30).

with question_tags as (
    select q.id as question_id, tag, q.answer_count
    from `bigquery-public-data.stackoverflow.posts_questions` as q,
        unnest(split(q.tags, '|')) as tag
    where extract(year from q.creation_date) = @year
)

select
    a.tag as tag_a,
    b.tag as tag_b,
    count(*) as n_questions,
    countif(a.answer_count > 0) as n_answered,
    sum(a.answer_count) as sum_answers,
    sum(a.answer_count * a.answer_count) as sum_answers_sq,
    sum(a.answer_count * a.answer_count * a.answer_count) as sum_answers_cube,
    max(a.answer_count) as max_answers
from question_tags as a
inner join question_tags as b
    on a.question_id = b.question_id
    and a.tag < b.tag
group by tag_a, tag_b
having count(*) >= @min_questions
order by n_questions desc

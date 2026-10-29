-- D1 EDA: sample size and outcomes per tag pair, for questions created in @year.
--
-- Grain: one row per unordered tag pair with at least @min_questions questions (the long tail of tiny pairs is
-- summarized by tag_pair_size_distribution.sql instead).
-- answer_count is the question's own counter; reconciling it with posts_answers is AC-0.4 (not done yet).
-- In the BigQuery console, replace @year and @min_questions with literals (e.g. 2022 and 30).

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
    a.tag as tag_a,
    b.tag as tag_b,
    count(*) as n_questions,
    countif(a.answer_count > 0) as n_answered,
    countif(a.has_accepted_answer) as n_accepted,
    sum(a.answer_count) as n_answers
from question_tags as a
inner join question_tags as b
    on a.question_id = b.question_id
    and a.tag < b.tag
group by tag_a, tag_b
having n_questions >= @min_questions
order by n_questions desc

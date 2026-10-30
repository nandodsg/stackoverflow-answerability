-- D1 EDA, answers-per-question ranking: per-tag moments of answer_count, for questions created in @year.
--
-- Grain: one row per tag with at least @min_questions questions. A question with 3 tags counts once for each tag.
-- The sums of answer_count, its square and its cube give the mean, standard deviation and skewness per tag, which is
-- all the mean ± 1.96 × SE interval (specs/000, D3) and the normal-approximation check need.
-- Reads only tags, creation_date and answer_count: title and body are never scanned.
-- In the BigQuery console, replace @year and @min_questions with literals (e.g. 2022 and 30).

with question_tags as (
    select tag, q.answer_count
    from `bigquery-public-data.stackoverflow.posts_questions` as q,
        unnest(split(q.tags, '|')) as tag
    where extract(year from q.creation_date) = @year
)

select
    tag,
    count(*) as n_questions,
    countif(answer_count > 0) as n_answered,
    sum(answer_count) as sum_answers,
    sum(answer_count * answer_count) as sum_answers_sq,
    sum(answer_count * answer_count * answer_count) as sum_answers_cube,
    max(answer_count) as max_answers
from question_tags
group by tag
having count(*) >= @min_questions
order by n_questions desc

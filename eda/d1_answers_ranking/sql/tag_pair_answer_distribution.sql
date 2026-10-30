-- D1 EDA, answers-per-question ranking: the full answer_count distribution of every tag pair above the ranking floor,
-- for questions created in @year.
--
-- Grain: one row per (tag pair, answer_count) for pairs with at least @min_questions questions. Same use as
-- tag_answer_distribution.sql.
-- Reads only id, tags, creation_date and answer_count: title and body are never scanned.
-- In the BigQuery console, replace @year and @min_questions with literals (e.g. 2022 and 385).

with question_tags as (
    select q.id as question_id, tag, q.answer_count
    from `bigquery-public-data.stackoverflow.posts_questions` as q,
        unnest(split(q.tags, '|')) as tag
    where extract(year from q.creation_date) = @year
),

counts as (
    select a.tag as tag_a, b.tag as tag_b, a.answer_count, count(*) as n_questions
    from question_tags as a
    inner join question_tags as b
        on a.question_id = b.question_id
        and a.tag < b.tag
    group by tag_a, tag_b, answer_count
)

select tag_a, tag_b, answer_count, n_questions
from counts
qualify sum(n_questions) over (partition by tag_a, tag_b) >= @min_questions
order by tag_a, tag_b, answer_count

-- D1 EDA, answers-per-question ranking: the full answer_count distribution of every tag above the ranking floor, for
-- questions created in @year.
--
-- Grain: one row per (tag, answer_count) for tags with at least @min_questions questions. This frequency table is all
-- a bootstrap needs (resampling questions = resampling answer_count values with these weights), so no
-- question-level rows are downloaded.
-- Reads only tags, creation_date and answer_count: title and body are never scanned.
-- In the BigQuery console, replace @year and @min_questions with literals (e.g. 2022 and 385).

with question_tags as (
    select tag, q.answer_count
    from `bigquery-public-data.stackoverflow.posts_questions` as q,
        unnest(split(q.tags, '|')) as tag
    where extract(year from q.creation_date) = @year
),

counts as (
    select tag, answer_count, count(*) as n_questions
    from question_tags
    group by tag, answer_count
)

select tag, answer_count, n_questions
from counts
qualify sum(n_questions) over (partition by tag) >= @min_questions
order by tag, answer_count

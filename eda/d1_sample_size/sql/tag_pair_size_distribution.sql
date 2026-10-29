-- D1 EDA: how many tag pairs have n questions, for questions created in @year.
--
-- Grain: one row per n_questions value (a frequency table). There are far more pairs than tags, so the pair
-- distribution is aggregated here instead of downloading one row per pair.
-- A pair is unordered: (pandas, python) and (python, pandas) are the same pair, kept once via tag_a < tag_b.
-- In the BigQuery console, replace @year with a literal (e.g. 2022).

with question_tags as (
    select
        q.id as question_id,
        tag
    from `bigquery-public-data.stackoverflow.posts_questions` as q,
        unnest(split(q.tags, '|')) as tag
    where extract(year from q.creation_date) = @year
),

pair_sizes as (
    select
        a.tag as tag_a,
        b.tag as tag_b,
        count(*) as n_questions
    from question_tags as a
    inner join question_tags as b
        on a.question_id = b.question_id
        and a.tag < b.tag
    group by tag_a, tag_b
)

select
    n_questions,
    count(*) as n_pairs
from pair_sizes
group by n_questions
order by n_questions

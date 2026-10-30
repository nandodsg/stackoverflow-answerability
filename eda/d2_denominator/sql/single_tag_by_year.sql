-- D2 EDA: outcomes per creation year for questions tagged with exactly one tag ('python' or 'dbt').
--
-- Grain: one row per (tag, creation year), 2013-2022. 2022 is partial (data ends 2022-09-25).
-- Reads only tags, creation_date, answer_count and accepted_answer_id: title and body are never scanned.

select
    q.tags as tag,
    extract(year from q.creation_date) as creation_year,
    count(*) as n_questions,
    countif(q.answer_count > 0) as n_answered,
    countif(q.accepted_answer_id is not null) as n_accepted,
    sum(q.answer_count) as n_answers
from `bigquery-public-data.stackoverflow.posts_questions` as q
where q.tags in ('python', 'dbt')
    and extract(year from q.creation_date) between 2013 and 2022
group by tag, creation_year
order by tag, creation_year

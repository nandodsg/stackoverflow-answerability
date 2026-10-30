-- D4 EDA, leakage KPI: how much the exposure to post-answer edits varies across the tags P1 ranks.
--
-- Grain: one row per tag, 2022 questions (partial year, data ends 2022-09-25), tags with >= 385 questions (D1 floor).
-- "Exposed" = the first edit of that kind came after the question's first answer, so the current version may have
-- been changed because of the answer. Tag exposure matters for P1/P2 (group membership), text exposure for P3
-- (title/body features).
-- post_history types: 4/5/6 = title/body/tags edited, 7/8/9 = title/body/tags rolled back.
-- Reads only ids, types and dates: the post_history text column (~110 GB) is never scanned.

with questions as (
    select q.id, q.tags
    from `bigquery-public-data.stackoverflow.posts_questions` as q
    where extract(year from q.creation_date) = 2022
),

edits as (
    select
        h.post_id as question_id,
        min(if(h.post_history_type_id in (6, 9), h.creation_date, null)) as first_tag_edit,
        min(if(h.post_history_type_id in (4, 5, 7, 8), h.creation_date, null)) as first_text_edit
    from `bigquery-public-data.stackoverflow.post_history` as h
    where h.post_history_type_id in (4, 5, 6, 7, 8, 9)
        and h.post_id in (select id from questions)
    group by h.post_id
),

first_answers as (
    select a.parent_id as question_id, min(a.creation_date) as first_answer
    from `bigquery-public-data.stackoverflow.posts_answers` as a
    where a.parent_id in (select id from questions)
    group by a.parent_id
),

flags as (
    select
        q.id,
        q.tags,
        coalesce(e.first_tag_edit > f.first_answer, false) as tag_exposed,
        coalesce(e.first_text_edit > f.first_answer, false) as text_exposed
    from questions as q
    left join edits as e on e.question_id = q.id
    left join first_answers as f on f.question_id = q.id
)

select
    tag,
    count(*) as n_questions,
    countif(tag_exposed) as n_tag_exposed,
    countif(text_exposed) as n_text_exposed
from flags, unnest(split(tags, '|')) as tag
group by tag
having count(*) >= 385
order by n_questions desc

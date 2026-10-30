-- D4 EDA: how often are questions edited after posting, what gets edited, by whom, and when relative to the first
-- answer; and how answer / accepted rates differ between edited and never-edited questions.
--
-- Grain: one row per (segment, creation year). Segments: 'python-only' and 'dbt-only' (tags exactly 'python' / 'dbt',
-- 2013-2022) and 'all' (every question created in 2022). 2022 is partial (data ends 2022-09-25).
-- post_history types: 4/5/6 = title/body/tags edited, 7/8/9 = title/body/tags rolled back.
-- Reads only ids, types, dates and user ids: the post_history text column (~110 GB) is never scanned.

with questions as (
    select
        q.id,
        q.owner_user_id,
        q.tags,
        extract(year from q.creation_date) as creation_year,
        q.answer_count > 0 as is_answered,
        q.accepted_answer_id is not null as has_accepted_answer,
        q.last_edit_date is not null as has_last_edit_date
    from `bigquery-public-data.stackoverflow.posts_questions` as q
    where extract(year from q.creation_date) between 2013 and 2022
        and (q.tags in ('python', 'dbt') or extract(year from q.creation_date) = 2022)
),

segments as (
    select *, 'python-only' as segment from questions where tags = 'python'
    union all
    select *, 'dbt-only' as segment from questions where tags = 'dbt'
    union all
    select *, 'all' as segment from questions where creation_year = 2022
),

edits as (
    select
        h.post_id as question_id,
        min(if(h.post_history_type_id in (6, 9), h.creation_date, null)) as first_tag_edit,
        min(if(h.post_history_type_id in (4, 5, 7, 8), h.creation_date, null)) as first_text_edit,
        logical_or(h.post_history_type_id in (6, 9) and h.user_id is distinct from q.owner_user_id) as tag_edit_by_other,
        logical_or(h.post_history_type_id in (4, 5, 7, 8) and h.user_id is distinct from q.owner_user_id)
            as text_edit_by_other
    from `bigquery-public-data.stackoverflow.post_history` as h
    inner join questions as q on q.id = h.post_id
    where h.post_history_type_id in (4, 5, 6, 7, 8, 9)
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
        s.segment,
        s.creation_year,
        s.is_answered,
        s.has_accepted_answer,
        s.has_last_edit_date,
        e.question_id is not null as is_edited,
        e.first_tag_edit is not null as has_tag_edit,
        e.first_text_edit is not null as has_text_edit,
        coalesce(e.tag_edit_by_other, false) as tag_edit_by_other,
        coalesce(e.text_edit_by_other, false) as text_edit_by_other,
        e.first_tag_edit > f.first_answer as tag_edit_after_first_answer,
        e.first_text_edit > f.first_answer as text_edit_after_first_answer
    from segments as s
    left join edits as e on e.question_id = s.id
    left join first_answers as f on f.question_id = s.id
)

select
    segment,
    creation_year,
    count(*) as n_questions,
    countif(is_answered) as n_answered,
    countif(has_accepted_answer) as n_accepted,
    countif(has_last_edit_date) as n_last_edit_date,
    countif(is_edited) as n_edited,
    countif(has_tag_edit) as n_tag_edit,
    countif(tag_edit_by_other) as n_tag_edit_by_other,
    countif(tag_edit_after_first_answer) as n_tag_edit_after_first_answer,
    countif(has_text_edit) as n_text_edit,
    countif(text_edit_by_other) as n_text_edit_by_other,
    countif(text_edit_after_first_answer) as n_text_edit_after_first_answer,
    countif(not is_edited) as n_never_edited,
    countif(not is_edited and is_answered) as n_answered_never_edited,
    countif(not is_edited and has_accepted_answer) as n_accepted_never_edited
from flags
group by segment, creation_year
order by segment, creation_year

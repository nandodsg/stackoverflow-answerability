-- AC-0.3: every accepted_answer_id points to an answer of that same question.
-- 292 legacy exceptions exist (2008–2012: 229 answers missing, 62 under another question, 1 pointing at a question
-- id), outside every prompt's years. They warn; one more fails the build.
{{ config(meta={'ac': 'AC-0.3'}, warn_if='>0', error_if='>292') }}

select
    q.question_id,
    q.creation_year,
    q.accepted_answer_id,
    a.question_id as accepted_answer_question_id
from {{ ref('int_questions') }} as q
left join {{ ref('stg_stackoverflow__answers') }} as a
    on a.answer_id = q.accepted_answer_id
where q.accepted_answer_id is not null
    and (a.answer_id is null or a.question_id != q.question_id)

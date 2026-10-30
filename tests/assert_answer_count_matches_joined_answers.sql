-- AC-0.4: a question's answer_count equals the answers present in posts_answers. The 2022-09 snapshot has no gap
-- (checked for every question), so any row here means the data changed and answer-based metrics must be rechecked.
{{ config(meta={'ac': 'AC-0.4'}) }}

select
    question_id,
    creation_year,
    answer_count,
    n_answers_joined
from {{ ref('int_questions') }}
where answer_count != n_answers_joined

-- Materialized as a view: set in the inline config() below (overrides the project default, table).
-- Everything P3 needs, one row per question created 2018-2022: outcomes, the text features of the ORIGINAL text (from
-- int_post_history_scan) and of the CURRENT text (prefixed current_, from int_question_body_scan), the features that
-- need no text, and the edit flags of the sensitivity checks (AC-3.5). Reads only the feature columns of the two scans,
-- never their stored text. A view: it stores nothing (the sandbox has 10 GB), and each P3 model reads it about once.
-- The 30 questions with no history row (no original text) are left out.
{{ config(materialized='view', tags=['needs_full_scan']) }}

{%- set text_columns = ['title_length', 'title_ends_with_question', 'title_starts_with_question_word', 'body_length',
    'has_code_block', 'code_block_count', 'has_inline_code', 'has_image', 'link_count', 'has_error_text',
    'has_effort_phrase', 'has_greeting_or_thanks'] %}

select
    q.question_id,
    q.creation_year,
    q.answer_count,
    q.is_answered,
    q.has_accepted_answer,
    -- The first tag as the asker listed it: usually the language. The topic control of P3 compares within it.
    split(o.original_tags, '|')[safe_offset(0)] as primary_tag,
    -- Sensitivity subsets (AC-3.5): title/body ever edited, and first edited after the first answer.
    e.first_text_edit_at is not null as is_text_edited,
    e.text_exposed,
    {%- for col in text_columns %}
    o.{{ col }},
    {%- endfor %}
    o.original_tag_count as tag_count,
    {%- for col in text_columns %}
    c.{{ col }} as current_{{ col }},
    {%- endfor %}
    q.tag_count as current_tag_count,
    p.hour_posted_utc,
    p.weekday_posted,
    p.asker_account_age_days,
    p.asker_prior_questions
from {{ ref('int_questions') }} as q
inner join {{ ref('int_post_history_scan') }} as o
    on o.post_id = q.question_id
    and o.post_kind = 'question'
    and o.creation_year between 2018 and 2022
inner join {{ ref('int_question_body_scan') }} as c
    on c.question_id = q.question_id
inner join {{ ref('int_question_exposure') }} as e
    on e.question_id = q.question_id
    and e.creation_year between 2018 and 2022
inner join {{ ref('int_question_posting_context') }} as p
    on p.question_id = q.question_id
where q.creation_year between 2018 and 2022

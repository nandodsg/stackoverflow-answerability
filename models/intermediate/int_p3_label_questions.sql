-- Materialized as a view: set in the inline config() below (overrides the project default, table).
-- The P3 question table (int_p3_questions) restricted to the 30,000 questions of the analysis set, with the six quality
-- labels of the seed as bucket columns ('1: reference level', '2: ...'; not_applicable is null: the rubric leaves it out)
-- and the raw rule-based neighbours the label checks need (code blocks, body length, image, error text). The labels
-- judge the ORIGINAL text, so there is no current-text version here; the edit flags give the two sensitivity subsets.
{{ config(materialized='view', tags=['needs_full_scan']) }}

select
    q.question_id,
    q.creation_year,
    q.is_answered,
    q.has_accepted_answer,
    q.primary_tag,
    q.is_text_edited,
    q.text_exposed,
    {%- for label in p3_label_names() %}
    {{ p3_label_bucket(label, 'l.' ~ label) }} as {{ label }},
    {%- endfor %}
    q.has_code_block,
    q.code_block_count,
    q.body_length,
    q.has_image,
    q.has_error_text
from {{ ref('quality_labels_analysis') }} as l
inner join {{ ref('int_p3_questions') }} as q
    on q.question_id = l.question_id

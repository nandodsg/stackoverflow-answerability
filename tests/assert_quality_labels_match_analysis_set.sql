-- The seed of quality labels must cover exactly the analysis set: every analysis question labeled once, no label for a
-- question outside it. Any row returned names a question and the rule it breaks.
{{ config(tags=['needs_full_scan']) }}

select cast(a.question_id as string) as item, 'analysis question has no label' as problem
from {{ ref('int_label_analysis_questions') }} as a
left join {{ ref('quality_labels_analysis') }} as l
    on l.question_id = a.question_id
where l.question_id is null

union all

select cast(l.question_id as string), 'label for a question outside the analysis set'
from {{ ref('quality_labels_analysis') }} as l
left join {{ ref('int_label_analysis_questions') }} as a
    on a.question_id = l.question_id
where a.question_id is null

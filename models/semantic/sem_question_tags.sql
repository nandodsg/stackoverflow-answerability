-- Materialized as a view: set for the semantic folder in dbt_project.yml.
-- Semantic layer input, one row per (question, current tag): the tag rows of int_question_tags with the question
-- columns of sem_questions. A question with 3 tags appears 3 times, so only ratios of group totals are meaningful here.
select
    t.tag,
    q.*
from {{ ref('int_question_tags') }} as t
inner join {{ ref('sem_questions') }} as q
    on q.question_id = t.question_id

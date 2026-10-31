-- Materialized as a view: set for the semantic folder in dbt_project.yml.
-- Semantic layer input, one row per (question, unordered pair of current tags), tag_a < tag_b: the pair rows of
-- int_question_tag_pairs with the question columns of sem_questions.
select
    p.tag_a,
    p.tag_b,
    q.*
from {{ ref('int_question_tag_pairs') }} as p
inner join {{ ref('sem_questions') }} as q
    on q.question_id = p.question_id

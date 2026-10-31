{#-
    p2_python_dbt(relation, tag_column, tag_list, extra_where): the whole P2 mart, so the answer and its sensitivity
    views follow the same rules (specs/002, D3). One row per (tag, creation year) for 2013-2022; a year with no question
    stays as a row of zeros (AC-2.2).

    - `relation` has question_id, creation_year, answer_count, is_answered, has_accepted_answer and the column that
      names the group: `tags` (the whole tag string, matched exactly) or `tag` (one row per question and tag).
    - `tag_column`: which column holds the group name. `tag_list`: the groups to keep.
    - `extra_where`: an optional SQL condition on q (the relation) and e (int_question_exposure), e.g. never tag-edited.
-#}
{% macro p2_python_dbt(relation, tag_column='tags', tag_list=['python', 'dbt'], extra_where='true') -%}
{%- set tag_values = "'" ~ tag_list | join("', '") ~ "'" -%}

with calendar as (
    select tag, creation_year
    from unnest([{{ tag_values }}]) as tag
    cross join unnest(generate_array(2013, 2022)) as creation_year
),

questions as (
    select
        q.{{ tag_column }} as tag,
        q.creation_year,
        q.answer_count,
        q.is_answered,
        q.has_accepted_answer,
        e.tags_exposed
    from {{ relation }} as q
    inner join {{ ref('int_question_exposure') }} as e
        on e.question_id = q.question_id
    where q.{{ tag_column }} in ({{ tag_values }})
        and q.creation_year between 2013 and 2022
        and {{ extra_where }}
),

aggregated as (
    select
        c.tag,
        c.creation_year,
        count(q.tag) as n_questions,
        countif(q.is_answered) as n_answered,
        countif(q.has_accepted_answer) as n_accepted,
        coalesce(sum(q.answer_count), 0) as n_answers,
        coalesce(sum(pow(q.answer_count, 2)), 0) as sum_sq_answers,
        coalesce(sum(pow(q.answer_count, 3)), 0) as sum_cube_answers,
        countif(q.tags_exposed) as n_tags_exposed
    from calendar as c
    left join questions as q
        on q.tag = c.tag and q.creation_year = c.creation_year
    group by c.tag, c.creation_year
),

metrics as (
    select
        *,
        {{ group_metrics() }}
    from aggregated
)

select
    *,
    creation_year = 2022 as is_partial_year,
    safe_divide(n_questions, n_answers) as questions_per_answer,
    -- The interval of Q÷A is the inverted interval of answers per question.
    safe_divide(1, answers_per_question_upper) as questions_per_answer_lower,
    safe_divide(1, answers_per_question_lower) as questions_per_answer_upper,
    -- Year over year, within each tag. Absolute change is the main number, relative change sits beside it (AC-2.5).
    answers_per_question - lag(answers_per_question) over (partition by tag order by creation_year) as answers_per_question_yoy_abs,
    safe_divide(
        answers_per_question - lag(answers_per_question) over (partition by tag order by creation_year),
        lag(answers_per_question) over (partition by tag order by creation_year)
    ) as answers_per_question_yoy_rel,
    accepted_rate - lag(accepted_rate) over (partition by tag order by creation_year) as accepted_rate_yoy_pp
from metrics
{%- endmacro %}

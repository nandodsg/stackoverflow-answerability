{#-
    p1_ranked_groups(relation, keys): the whole P1 mart for one grain (single tags or tag pairs), so both marts follow
    the same rules (specs/001, D1/D2/D3). `relation` has one row per (question, group) with question_id, creation_year,
    answer_count, is_answered, has_accepted_answer and the group key columns.

    - Years: 2022 (the answer) and 2021 (the robustness check, AC-1.4).
    - Floor: a group needs >= var('min_questions') = 385 questions in its year (AC-1.2); smaller groups are not in the
      table, which is the ranked universe.
    - Ranks, per year: "top" ranks by the lower bound (highest first), "bottom" by the upper bound (lowest first);
      `_raw` ranks use the plain rate (robustness method A, AC-1.7). Ties break on the group key so the order is stable.
-#}
{% macro p1_ranked_groups(relation, keys) -%}
{%- set key_list = keys | join(', ') -%}
{%- set min_questions = var('min_questions', 385) -%}

with questions as (
    select
        g.creation_year,
        {% for key in keys %}g.{{ key }},{% endfor %}
        g.answer_count,
        g.is_answered,
        g.has_accepted_answer,
        e.tags_exposed
    from {{ relation }} as g
    inner join {{ ref('int_question_exposure') }} as e
        on e.question_id = g.question_id
    where g.creation_year in (2021, 2022)
),

aggregated as (
    select
        creation_year,
        {{ key_list }},
        {{ group_aggregates() }}
    from questions
    group by creation_year, {{ key_list }}
    having count(*) >= {{ min_questions }}
),

metrics as (
    select
        *,
        {{ group_metrics() }}
    from aggregated
)

select
    *,
    -- Cochran's rule: the normal interval of answers per question is approximate when this is false (AC-1.10).
    coalesce(n_questions > 25 * pow(answer_count_skewness, 2), true) as answers_interval_reliable,
    -- Highest lists sort by the lower Wilson bound, lowest lists by the upper bound (AC-1.6).
    row_number() over (partition by creation_year order by accepted_rate_lower desc, {{ key_list }}) as rank_accepted_top,
    row_number() over (partition by creation_year order by accepted_rate_upper asc, {{ key_list }}) as rank_accepted_bottom,
    row_number() over (partition by creation_year order by answer_rate_lower desc, {{ key_list }}) as rank_answer_rate_top,
    row_number() over (partition by creation_year order by answer_rate_upper asc, {{ key_list }}) as rank_answer_rate_bottom,
    row_number() over (partition by creation_year order by answers_per_question_lower desc, {{ key_list }}) as rank_answers_top,
    row_number() over (partition by creation_year order by answers_per_question_upper asc, {{ key_list }}) as rank_answers_bottom,
    -- Robustness method A: the same floor, the plain rate as the sort key.
    row_number() over (partition by creation_year order by accepted_rate desc, {{ key_list }}) as rank_accepted_top_raw,
    row_number() over (partition by creation_year order by accepted_rate asc, {{ key_list }}) as rank_accepted_bottom_raw
from metrics
{%- endmacro %}

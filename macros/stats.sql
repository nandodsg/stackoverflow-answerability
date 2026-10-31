{#-
    The interval and ranking rules of specs/000 and specs/001, written once so P1 and P2 cannot drift apart.

    Wilson score interval, 95% (D1): (k + z²/2 ± z·√(k(n−k)/n + z²/4)) / (n + z²), z = 1.96. Null when n = 0.
    Reference values (AC-1.5): 9/10 → 0.596 / 0.982, 850/1000 → 0.827 / 0.871, 1/1 → 0.207 / 1, 0/1 → 0 / 0.793.
-#}

{% macro wilson_lower(k, n) -%}
    if({{ n }} = 0, null,
        ({{ k }} + 1.96 * 1.96 / 2 - 1.96 * sqrt({{ k }} * ({{ n }} - {{ k }}) / {{ n }} + 1.96 * 1.96 / 4))
        / ({{ n }} + 1.96 * 1.96))
{%- endmacro %}

{% macro wilson_upper(k, n) -%}
    if({{ n }} = 0, null,
        ({{ k }} + 1.96 * 1.96 / 2 + 1.96 * sqrt({{ k }} * ({{ n }} - {{ k }}) / {{ n }} + 1.96 * 1.96 / 4))
        / ({{ n }} + 1.96 * 1.96))
{%- endmacro %}


{#-
    group_metrics(): the derived columns of a group of questions, read from the standard aggregate columns that the
    models build: n_questions, n_answered, n_accepted, n_answers, sum_sq_answers, sum_cube_answers, n_tags_exposed.

    Rates use all questions as the denominator (D2). Answers per question is total answers / total questions (D3),
    its interval is mean ± 1.96 × SE with SE = SD / √n (sample SD from the sums: (Σx² − (Σx)²/n) / (n − 1)).
    The skewness feeds Cochran's rule (AC-1.10): the normal interval is trusted only when n > 25 × skewness².
-#}
{% macro group_metrics() -%}
    {#- Pieces written once. Every division is a safe_divide, so a group with no questions gives nulls, not an error. -#}
    {%- set mean = 'safe_divide(n_answers, n_questions)' -%}
    {%- set se = 'safe_divide(sqrt(greatest(safe_divide(sum_sq_answers - safe_divide(n_answers * n_answers, n_questions), n_questions - 1), 0)), sqrt(n_questions))' -%}
    {%- set m2 = '(safe_divide(sum_sq_answers, n_questions) - pow(' ~ mean ~ ', 2))' -%}
    {%- set m3 = '(safe_divide(sum_cube_answers, n_questions) - 3 * ' ~ mean ~ ' * safe_divide(sum_sq_answers, n_questions) + 2 * pow(' ~ mean ~ ', 3))' -%}
    safe_divide(n_answered, n_questions) as answer_rate,
    safe_divide(n_accepted, n_questions) as accepted_rate,
    safe_divide(n_accepted, n_answered) as accepted_rate_among_answered,
    {{ mean }} as answers_per_question,
    safe_divide(n_answers, n_answered) as answers_per_answered_question,
    safe_divide(n_tags_exposed, n_questions) as tag_exposure,
    {{ wilson_lower('n_answered', 'n_questions') }} as answer_rate_lower,
    {{ wilson_upper('n_answered', 'n_questions') }} as answer_rate_upper,
    {{ wilson_lower('n_accepted', 'n_questions') }} as accepted_rate_lower,
    {{ wilson_upper('n_accepted', 'n_questions') }} as accepted_rate_upper,
    {{ mean }} - 1.96 * {{ se }} as answers_per_question_lower,
    {{ mean }} + 1.96 * {{ se }} as answers_per_question_upper,
    safe_divide({{ m3 }}, pow(greatest({{ m2 }}, 0), 1.5)) as answer_count_skewness
{%- endmacro %}


{# Standard aggregate columns over a set of question rows with answer_count, is_answered, has_accepted_answer, tags_exposed. #}
{% macro group_aggregates() -%}
    count(*) as n_questions,
    countif(is_answered) as n_answered,
    countif(has_accepted_answer) as n_accepted,
    sum(answer_count) as n_answers,
    sum(pow(answer_count, 2)) as sum_sq_answers,
    sum(pow(answer_count, 3)) as sum_cube_answers,
    countif(tags_exposed) as n_tags_exposed
{%- endmacro %}

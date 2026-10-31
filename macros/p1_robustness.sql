{#-
    p1_robustness(relation, mart, keys): robustness methods A and C for the accepted rate (specs/001, AC-1.7).

    - `relation`: one row per (question, group) like the one p1_ranked_groups reads. `mart`: the P1 mart of the same grain.
    - Method C, empirical Bayes: every group's accepted rate is pulled toward the pooled rate p0 as (k + m*p0) / (n + m),
      so a small group moves more than a large one. m ("prior strength", in virtual questions at the pooled rate) comes
      from the method of moments on every group with >= 30 questions, the same formula as eda/d1_sample_size:
        p0         = total accepted / total questions
        rate_var   = sample variance of the groups' raw rates
        sampling   = average of p0 * (1 - p0) / n   (the variance chance alone would produce)
        m          = p0 * (1 - p0) / max(rate_var - sampling, 1e-6) - 1
    - The ranked universe is the mart's (>= 385 questions); only the prior is fitted on the wider >= 30 set.
    - Output: one row per mart row with the Wilson, raw (A) and EB (C) ranks side by side.
-#}
{% macro p1_robustness(relation, mart, keys) -%}
{%- set key_list = keys | join(', ') -%}

with fit_groups as (
    select
        creation_year,
        {{ key_list }},
        count(*) as n_questions,
        countif(has_accepted_answer) as n_accepted
    from {{ relation }}
    where creation_year in (2021, 2022)
    group by creation_year, {{ key_list }}
    having count(*) >= 30
),

pooled as (
    select
        creation_year,
        safe_divide(sum(n_accepted), sum(n_questions)) as pooled_rate,
        count(*) as n_groups_fitted
    from fit_groups
    group by creation_year
),

prior as (
    select
        p.creation_year,
        p.pooled_rate,
        p.n_groups_fitted,
        p.pooled_rate * (1 - p.pooled_rate)
            / greatest(var_samp(safe_divide(g.n_accepted, g.n_questions))
                       - avg(p.pooled_rate * (1 - p.pooled_rate) / g.n_questions), 1e-6)
            - 1 as prior_strength
    from fit_groups as g
    inner join pooled as p
        on p.creation_year = g.creation_year
    group by p.creation_year, p.pooled_rate, p.n_groups_fitted
),

shrunk as (
    select
        m.creation_year,
        {% for key in keys %}m.{{ key }},{% endfor %}
        m.n_questions,
        m.n_accepted,
        m.accepted_rate,
        m.accepted_rate_lower,
        m.accepted_rate_upper,
        m.rank_accepted_top,
        m.rank_accepted_bottom,
        m.rank_accepted_top_raw,
        m.rank_accepted_bottom_raw,
        p.pooled_rate,
        p.n_groups_fitted,
        p.prior_strength,
        (m.n_accepted + p.prior_strength * p.pooled_rate) / (m.n_questions + p.prior_strength) as accepted_rate_eb
    from {{ mart }} as m
    inner join prior as p
        on p.creation_year = m.creation_year
)

select
    *,
    row_number() over (partition by creation_year order by accepted_rate_eb desc, {{ key_list }}) as rank_accepted_top_eb,
    row_number() over (partition by creation_year order by accepted_rate_eb asc, {{ key_list }}) as rank_accepted_bottom_eb
from shrunk
{%- endmacro %}


{#-
    p1_rank_flips(mart, keys, grain): which groups moved in or out of a top / bottom 10 between 2021 and 2022 (AC-1.4).
    One row per (group, metric) with a change; metrics are accepted rate, answer rate and answers per question. A group
    below the 385 floor in one year has a null rank there, i.e. it is outside the list. `hard_flip` marks a group in the
    top 10 of one year and the bottom 10 of the other.
-#}
{% macro p1_rank_flips(mart, keys, grain) -%}
{%- set key_list = keys | join(', ') -%}
{%- set metrics = {'accepted_rate': 'accepted', 'answer_rate': 'answer_rate', 'answers_per_question': 'answers'} -%}
{%- set outside = 1000000 -%}

with joined as (
    select
        {{ key_list }},
        {% for metric, col in metrics.items() %}
        a.rank_{{ col }}_top as {{ metric }}_top_2022, b.rank_{{ col }}_top as {{ metric }}_top_2021,
        a.rank_{{ col }}_bottom as {{ metric }}_bottom_2022, b.rank_{{ col }}_bottom as {{ metric }}_bottom_2021
        {%- if not loop.last %},{% endif %}
        {% endfor %}
    from (select * from {{ mart }} where creation_year = 2022) as a
    full outer join (select * from {{ mart }} where creation_year = 2021) as b
        using ({{ key_list }})
)

{% for metric in metrics %}
{%- set t21 = 'coalesce(' ~ metric ~ '_top_2021, ' ~ outside ~ ')' -%}
{%- set t22 = 'coalesce(' ~ metric ~ '_top_2022, ' ~ outside ~ ')' -%}
{%- set b21 = 'coalesce(' ~ metric ~ '_bottom_2021, ' ~ outside ~ ')' -%}
{%- set b22 = 'coalesce(' ~ metric ~ '_bottom_2022, ' ~ outside ~ ')' -%}
select
    '{{ grain }}' as grain,
    {{ keys | join(" || ' + ' || ") }} as group_name,
    '{{ metric }}' as metric,
    {{ metric }}_top_2021 as rank_top_2021,
    {{ metric }}_top_2022 as rank_top_2022,
    {{ metric }}_bottom_2021 as rank_bottom_2021,
    {{ metric }}_bottom_2022 as rank_bottom_2022,
    case when {{ t22 }} <= 10 and {{ t21 }} > 10 then 'entered in 2022'
         when {{ t21 }} <= 10 and {{ t22 }} > 10 then 'left in 2022' end as top10_change,
    case when {{ b22 }} <= 10 and {{ b21 }} > 10 then 'entered in 2022'
         when {{ b21 }} <= 10 and {{ b22 }} > 10 then 'left in 2022' end as bottom10_change,
    ({{ t21 }} <= 10 and {{ b22 }} <= 10) or ({{ b21 }} <= 10 and {{ t22 }} <= 10) as hard_flip
from joined
where ({{ t22 }} <= 10) != ({{ t21 }} <= 10)
    or ({{ b22 }} <= 10) != ({{ b21 }} <= 10)
{% if not loop.last %}union all{% endif %}
{% endfor %}
{%- endmacro %}

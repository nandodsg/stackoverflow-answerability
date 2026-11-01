{#- The quality labels of the P3 analysis set (specs/003, "Quality labels"): one bucket column per label. A level becomes
    '<n>: <level>' with the label's reference level first ('1:', the same convention as the rule-based buckets, so the
    effects reuse the rules of mart_p3_feature_effects). 'not_applicable' maps to null: the rubric leaves it out of the
    level-by-level analysis, and unpivot drops nulls. The levels are the rubric's (labels/rubric.md); the seed's
    accepted_values tests and assert_p3_label_buckets fail if they drift apart. -#}
{% macro p3_label_levels() -%}
    {{ return({
        'worked_example': ['no', 'yes'],
        'ask_scope': ['narrow', 'broad', 'multiple', 'no_clear_ask'],
        'failure_description': ['concrete', 'vague'],
        'code_focus': ['focused', 'partial', 'dump'],
        'environment_dependent': ['no', 'yes'],
        'image_only_evidence': ['no', 'yes'],
    }) }}
{%- endmacro %}

{% macro p3_label_names() -%}
    {{ return(p3_label_levels().keys() | list) }}
{%- endmacro %}

{% macro p3_label_bucket(label, col) -%}
    {%- set levels = p3_label_levels()[label] -%}
    case {{ col }}
        {%- for level in levels %}
        when '{{ level }}' then '{{ loop.index }}: {{ level }}'
        {%- endfor %}
        when 'not_applicable' then null
        else '9: unmapped'
    end
{%- endmacro %}

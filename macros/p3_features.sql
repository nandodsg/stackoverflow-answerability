{#-
    The P3 feature buckets (specs/003, "Method"), written once so every P3 model groups a feature the same way.

    Each feature becomes a label such as '2: 500-999'. The number in front orders the buckets, and bucket '1:' is the
    reference every other bucket is compared with (no / zero / the smallest). A missing value is '9: unknown'.
    Cut points are fixed, not deciles, so the original and the current text of a question fall into the same buckets
    and a change of bucket means the text changed.
-#}

{# Features read from the text, in int_p3_questions as `<name>` (original text) and `current_<name>` (current text). #}
{% macro p3_text_features() -%}
    {{ return([
        'title_length', 'title_ends_with_question', 'title_starts_with_question_word',
        'body_length', 'has_code_block', 'code_block_count', 'has_inline_code', 'has_image', 'link_count',
        'has_error_text', 'has_effort_phrase', 'has_greeting_or_thanks', 'tag_count',
    ]) }}
{%- endmacro %}

{# Features known at posting time that need no text: feature name -> the column it is computed from. #}
{% macro p3_context_features() -%}
    {{ return({
        'hour_posted_utc': 'hour_posted_utc',
        'weekday_posted': 'weekday_posted',
        'posted_on_weekend': 'weekday_posted',
        'asker_account_age': 'asker_account_age_days',
        'asker_prior_questions': 'asker_prior_questions',
    }) }}
{%- endmacro %}

{# Body features that also apply to answers (the answer lens): no title, no tags. #}
{% macro p3_answer_features() -%}
    {{ return([
        'body_length', 'has_code_block', 'code_block_count', 'has_inline_code', 'has_image', 'link_count',
        'has_error_text', 'has_effort_phrase', 'has_greeting_or_thanks',
    ]) }}
{%- endmacro %}

{% macro p3_feature_names() -%}
    {{ return(p3_text_features() + (p3_context_features().keys() | list)) }}
{%- endmacro %}


{#- p3_bucket(feature, col): the bucket label of one value. Numeric features: a value below cuts[i] gets labels[i].
    No feature can be negative, so a negative value is unknown: 607 askers have an account created after their
    question (up to 1,400 days later; merged accounts, most likely). -#}
{% macro p3_bucket(feature, col) -%}
    {%- set numeric = {
        'title_length': ([40, 60, 80], ['<40', '40-59', '60-79', '80+']),
        'body_length': ([500, 1000, 2000, 4000], ['<500', '500-999', '1000-1999', '2000-3999', '4000+']),
        'code_block_count': ([1, 2, 3], ['0', '1', '2', '3+']),
        'link_count': ([1, 2], ['0', '1', '2+']),
        'tag_count': ([2, 3, 4, 5], ['1', '2', '3', '4', '5+']),
        'hour_posted_utc': ([6, 12, 18], ['00-05', '06-11', '12-17', '18-23']),
        'asker_account_age': ([1, 30, 365, 1095], ['under 1 day', '1-29 days', '1-12 months', '1-3 years', '3+ years']),
        'asker_prior_questions': ([1, 5, 20], ['0 (first question)', '1-4', '5-19', '20+']),
    } -%}
    {%- if feature in numeric -%}
        {%- set cuts, labels = numeric[feature] -%}
        case
            when {{ col }} is null or {{ col }} < 0 then '9: unknown'
            {%- for cut in cuts %}
            when {{ col }} < {{ cut }} then '{{ loop.index }}: {{ labels[loop.index0] }}'
            {%- endfor %}
            else '{{ labels | length }}: {{ labels[-1] }}'
        end
    {%- elif feature == 'weekday_posted' -%}
        {#- BigQuery numbers the days 1 = Sunday ... 7 = Saturday; the labels start the week on Monday. -#}
        case {{ col }}
            when 2 then '1: Mon' when 3 then '2: Tue' when 4 then '3: Wed' when 5 then '4: Thu'
            when 6 then '5: Fri' when 7 then '6: Sat' when 1 then '7: Sun' else '9: unknown'
        end
    {%- elif feature == 'posted_on_weekend' -%}
        case when {{ col }} is null then '9: unknown' when {{ col }} in (1, 7) then '2: yes' else '1: no' end
    {%- else -%}
        {#- Every other feature is a yes/no flag. -#}
        case when {{ col }} is null then '9: unknown' when {{ col }} then '2: yes' else '1: no' end
    {%- endif -%}
{%- endmacro %}


{#- p3_bucket_columns(prefix): one bucket column per question feature, named like the feature. The prefix picks the
    text version ('' = original, 'current_' = current); the context features are the same in every version. -#}
{% macro p3_bucket_columns(prefix) -%}
    {%- for feature in p3_text_features() %}
    {{ p3_bucket(feature, prefix ~ feature) }} as {{ feature }},
    {%- endfor %}
    {%- for feature, col in p3_context_features().items() %}
    {{ p3_bucket(feature, col) }} as {{ feature }}{% if not loop.last %},{% endif %}
    {%- endfor %}
{%- endmacro %}


{#- Wilson bounds of a rate k / n, as the two columns <name>_lower and <name>_upper. -#}
{% macro p3_rate_with_bounds(k, n, name) -%}
    safe_divide({{ k }}, {{ n }}) as {{ name }},
    {{ wilson_lower(k, n) }} as {{ name }}_lower,
    {{ wilson_upper(k, n) }} as {{ name }}_upper
{%- endmacro %}


{#- Half-width of the 95% interval of a difference of two rates: 1.96 * sqrt(p1(1-p1)/n1 + p2(1-p2)/n2). -#}
{% macro p3_difference_margin(p1, n1, p2, n2) -%}
    1.96 * sqrt(safe_divide({{ p1 }} * (1 - {{ p1 }}), {{ n1 }}) + safe_divide({{ p2 }} * (1 - {{ p2 }}), {{ n2 }}))
{%- endmacro %}

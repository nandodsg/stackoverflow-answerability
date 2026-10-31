{#-
    Two sampling helpers for the full-scan models (specs/003).

    scan_source(relation, alias): the source table, or, when `--vars '{sample_pct: 0.1}'` is passed, a block sample of
    it. BigQuery bills a TABLESAMPLE for the fraction it reads, so this is how a scan model is tried for ~0.1 GB
    before the real 109 GB run. A row filter (WHERE) does not reduce the bill of a text column, only this does.

    in_text_sample(id_col): the 5% of questions whose text is stored for the quality labels. A fixed function of the
    question id, so both scan models and the answers pick the same questions on every run.
-#}

{% macro scan_source(relation, alias) -%}
    {{ relation }} as {{ alias }}
    {%- if var('sample_pct', none) is not none %} tablesample system ({{ var('sample_pct') }} percent){% endif %}
{%- endmacro %}


{% macro in_text_sample(id_col) -%}
    mod(abs(farm_fingerprint(cast({{ id_col }} as string))), 20) = 0
{%- endmacro %}

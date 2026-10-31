-- AC-3.2 / AC-3.4: the two big text columns are read in one place each. Reads dbt's own list of models (the project
-- graph), not a table: a model returned here reads `posts_questions` or `post_history` straight from the source but is
-- neither its staging view (which leaves the text column out) nor the one-time scan model. Any other model has to go
-- through staging, which has no `body` or `text` column, so it cannot scan them by accident.
{{ config(meta={'ac': 'AC-3.2', 'also': 'AC-3.4'}) }}

{%- set allowed = {
    'posts_questions': ['stg_stackoverflow__questions', 'int_question_body_scan'],
    'post_history': ['stg_stackoverflow__post_history', 'int_post_history_scan'],
} %}
{%- set offenders = [] %}
{%- if execute %}
    {%- for node in graph.nodes.values() if node.resource_type == 'model' %}
        {%- for source_name, table_name in node.sources %}
            {%- if source_name == 'stackoverflow' and table_name in allowed and node.name not in allowed[table_name] %}
                {%- do offenders.append((node.name, table_name)) %}
            {%- endif %}
        {%- endfor %}
    {%- endfor %}
{%- endif %}

select * from unnest([
    struct('' as model_name, '' as source_table)
    {%- for model_name, table_name in offenders %}
    , ('{{ model_name }}', '{{ table_name }}')
    {%- endfor %}
])
where model_name != ''

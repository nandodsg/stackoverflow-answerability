-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag).
-- The heavy step of P3, done once: question counts per version x feature x bucket x year x topic stratum. Every P3 mart
-- reads this small table (tens of thousands of rows) instead of the 8.4M questions.
--   version       original (the headline: original text), current (current text), never_edited (title/body never
--                 edited), not_edited_after_answer (no title/body edit after the first answer): AC-3.5
--   tag_stratum   the question's primary tag if it is one of the 20 most common in 2018-2022, else '(other)': the topic
--                 control compares a feature within each stratum
{{ config(tags=['needs_full_scan']) }}

{%- set versions = [
    ('original', '', 'true'),
    ('current', 'current_', 'true'),
    ('never_edited', '', 'not is_text_edited'),
    ('not_edited_after_answer', '', 'not text_exposed'),
] %}

with questions as (
    select * from {{ ref('int_p3_questions') }}
),

top_tags as (
    select primary_tag
    from questions
    where primary_tag is not null
    group by primary_tag
    order by count(*) desc, primary_tag
    limit 20
),

labeled as (
    select
        q.*,
        coalesce(t.primary_tag, '(other)') as tag_stratum
    from questions as q
    left join top_tags as t
        on t.primary_tag = q.primary_tag
),

versions as (
    {%- for name, prefix, condition in versions %}
    select
        '{{ name }}' as version,
        creation_year,
        tag_stratum,
        is_answered,
        has_accepted_answer,
        {{ p3_bucket_columns(prefix) }}
    from labeled
    where {{ condition }}
    {% if not loop.last %}union all{% endif %}
    {%- endfor %}
)

select
    version,
    feature,
    bucket,
    creation_year,
    tag_stratum,
    count(*) as n_questions,
    countif(is_answered) as n_answered,
    countif(has_accepted_answer) as n_accepted
from versions
unpivot (bucket for feature in ({{ p3_feature_names() | join(', ') }}))
group by version, feature, bucket, creation_year, tag_stratum

-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag).
-- The counts behind the label marts, as int_p3_bucket_counts is for the rule-based features: questions, answered and
-- accepted per version x label x level x year x topic stratum. The population is the 30,000 labeled questions.
--   version       original (the headline; the labels judge the original text), never_edited (title/body never edited),
--                 not_edited_after_answer (no title/body edit after the first answer); no current-text version exists
--   tag_stratum   the question's primary tag if it is one of the 20 most common among the labeled questions, else '(other)'
-- The label is called `feature` and the level `bucket` so mart_p3_label_rates / _effects read like the rule-based marts.
{{ config(tags=['needs_full_scan']) }}

{%- set versions = [
    ('original', 'true'),
    ('never_edited', 'not is_text_edited'),
    ('not_edited_after_answer', 'not text_exposed'),
] %}

with questions as (
    select * from {{ ref('int_p3_label_questions') }}
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
    {%- for name, condition in versions %}
    select
        '{{ name }}' as version,
        creation_year,
        tag_stratum,
        is_answered,
        has_accepted_answer,
        {{ p3_label_names() | join(', ') }}
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
unpivot (bucket for feature in ({{ p3_label_names() | join(', ') }}))
group by version, feature, bucket, creation_year, tag_stratum

-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag).
-- Prompt 3, leakage KPI (specs/000, AC-3.6): how much reading the CURRENT text instead of the original would have
-- changed the features. One row per year x text feature:
--   text_exposure          share of questions whose title/body was first edited after the first answer
--   share_changed          share of questions whose bucket differs between the original and the current text
--   share_changed_never_edited  the same share among questions never edited: the two texts are the same post, so
--                          this is the format floor (Markdown vs HTML rules disagreeing), not a real change
--   share_changed_net      share_changed minus the floor: the part edits explain
-- Buckets are compared, not raw values: Markdown and HTML lengths differ by a few characters on every post, and the
-- buckets are what the analysis uses. Tag count is left out (tag edits are in the P1/P2 tag exposure).
{{ config(tags=['needs_full_scan']) }}

{%- set features = p3_text_features() | reject('equalto', 'tag_count') | list %}

with compared as (
    select
        creation_year,
        is_text_edited,
        text_exposed,
        {%- for feature in features %}
        {{ p3_bucket(feature, feature) }} != {{ p3_bucket(feature, 'current_' ~ feature) }} as {{ feature }}{% if not loop.last %},{% endif %}
        {%- endfor %}
    from {{ ref('int_p3_questions') }}
)

select
    creation_year,
    feature,
    count(*) as n_questions,
    avg(if(text_exposed, 1, 0)) as text_exposure,
    avg(if(is_text_edited, 1, 0)) as text_edited_share,
    avg(if(changed, 1, 0)) as share_changed,
    safe_divide(countif(changed and not is_text_edited), countif(not is_text_edited)) as share_changed_never_edited,
    avg(if(changed, 1, 0))
        - safe_divide(countif(changed and not is_text_edited), countif(not is_text_edited)) as share_changed_net
from compared
unpivot (changed for feature in ({{ features | join(', ') }}))
group by creation_year, feature

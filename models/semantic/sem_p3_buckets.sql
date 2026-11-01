-- Materialized as a view: project default for the semantic folder in dbt_project.yml (the inline config() below only adds the tag).
-- Semantic layer input for P3, rule-based features: the counts of int_p3_bucket_counts (questions, answered, accepted per
-- version x feature x bucket x year x topic stratum) with a row key and a date for MetricFlow. One question is counted
-- once per feature, so a query must always group by or filter `feature` (and `version`); adding up all features double
-- counts. Tagged needs_full_scan because it reads a table built from the one-time text scans.
{{ config(tags=['needs_full_scan']) }}
select
    concat(version, '|', feature, '|', bucket, '|', cast(creation_year as string), '|', tag_stratum) as bucket_key,
    date(creation_year, 1, 1) as period_start,
    version,
    feature,
    bucket,
    creation_year,
    tag_stratum,
    n_questions,
    n_answered,
    n_accepted
from {{ ref('int_p3_bucket_counts') }}

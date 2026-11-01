-- Materialized as a view: project default for the semantic folder in dbt_project.yml (the inline config() below only adds the tag).
-- Semantic layer input for P3, quality labels: the counts of int_p3_label_bucket_counts (the 30,000 labeled questions;
-- `feature` is the label and `bucket` its level) with a row key and a date for MetricFlow. A question is counted once per
-- label, so a query must always group by or filter `feature` (and `version`). Tagged needs_full_scan like the table it reads.
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
from {{ ref('int_p3_label_bucket_counts') }}

-- Materialized as a table: set in the inline config() below (overrides the semantic folder default, view).
-- MetricFlow's calendar: one row per day, 2008-01-01 to 2023-12-31 (the snapshot ends 2022-09-25). It is how MetricFlow
-- fills time gaps and aligns granularities; a few thousand rows, no source table read.
{{ config(materialized='table') }}

select day as date_day
from unnest(generate_date_array('2008-01-01', '2023-12-31')) as day

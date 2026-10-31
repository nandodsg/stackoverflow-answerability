-- AC-1.6: "highest" lists sort by the Wilson LOWER bound (best first) and "lowest" lists by the UPPER bound (lowest first).
-- A row returned here is a rank whose bound is on the wrong side of the previous rank's bound. Checked for the accepted
-- rate in both P1 marts; the other metrics come from the same macro.
{{ config(meta={'ac': 'AC-1.6'}) }}

with rows_to_check as (
    select 'tags' as mart, creation_year, rank_accepted_top, rank_accepted_bottom, accepted_rate_lower, accepted_rate_upper
    from {{ ref('mart_p1_tags') }}
    union all
    select 'pairs', creation_year, rank_accepted_top, rank_accepted_bottom, accepted_rate_lower, accepted_rate_upper
    from {{ ref('mart_p1_pairs') }}
),

previous as (
    select
        *,
        lag(accepted_rate_lower) over (partition by mart, creation_year order by rank_accepted_top) as prev_lower,
        lag(accepted_rate_upper) over (partition by mart, creation_year order by rank_accepted_bottom) as prev_upper
    from rows_to_check
)

select mart, creation_year, rank_accepted_top, rank_accepted_bottom
from previous
where accepted_rate_lower > prev_lower
    or accepted_rate_upper < prev_upper

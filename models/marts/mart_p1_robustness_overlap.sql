-- Materialized as a table: project default in dbt_project.yml.
-- AC-1.7: how many of each Wilson top / bottom 10 (accepted rate) are also in the same list under method A (raw rate)
-- and method C (empirical Bayes). 10 = identical lists. One row per (grain, year).
with ranks as (
    select 'tags' as grain, creation_year, rank_accepted_top, rank_accepted_bottom,
        rank_accepted_top_raw, rank_accepted_bottom_raw, rank_accepted_top_eb, rank_accepted_bottom_eb
    from {{ ref('mart_p1_tags_robustness') }}
    union all
    select 'pairs', creation_year, rank_accepted_top, rank_accepted_bottom,
        rank_accepted_top_raw, rank_accepted_bottom_raw, rank_accepted_top_eb, rank_accepted_bottom_eb
    from {{ ref('mart_p1_pairs_robustness') }}
)

select
    grain,
    creation_year,
    countif(rank_accepted_top <= 10 and rank_accepted_top_raw <= 10) as top10_overlap_raw,
    countif(rank_accepted_top <= 10 and rank_accepted_top_eb <= 10) as top10_overlap_eb,
    countif(rank_accepted_bottom <= 10 and rank_accepted_bottom_raw <= 10) as bottom10_overlap_raw,
    countif(rank_accepted_bottom <= 10 and rank_accepted_bottom_eb <= 10) as bottom10_overlap_eb
from ranks
group by grain, creation_year

-- AC-0.10 / AC-1.9, prompt 1 impact check (severity: warn). 2022 accepted-rate rankings on the CURRENT tags (mart_p1_tags,
-- mart_p1_pairs) against the ORIGINAL tags (the *_original marts). A row returned here is a tag or pair that
--   * enters or leaves the top 10 or the bottom 10 (null rank = below the 385 floor = outside the list), or
--   * has an accepted rate that moves by more than 2.5 points (half the +-5-point precision target behind the floor).
-- It warns instead of failing: every warning is listed in the README as the size of the edit problem.
{{ config(severity='warn', tags=['needs_full_scan'], meta={'ac': 'AC-0.10', 'also': 'AC-1.9'}) }}

with compared as (
    select
        'tags' as grain,
        coalesce(c.tag, o.tag) as group_name,
        c.rank_accepted_top as current_top, o.rank_accepted_top as original_top,
        c.rank_accepted_bottom as current_bottom, o.rank_accepted_bottom as original_bottom,
        c.accepted_rate as current_rate, o.accepted_rate as original_rate
    from (select * from {{ ref('mart_p1_tags') }} where creation_year = 2022) as c
    full outer join (select * from {{ ref('mart_p1_tags_original') }} where creation_year = 2022) as o
        on c.tag = o.tag
    union all
    select
        'pairs',
        coalesce(c.tag_a, o.tag_a) || ' + ' || coalesce(c.tag_b, o.tag_b),
        c.rank_accepted_top, o.rank_accepted_top,
        c.rank_accepted_bottom, o.rank_accepted_bottom,
        c.accepted_rate, o.accepted_rate
    from (select * from {{ ref('mart_p1_pairs') }} where creation_year = 2022) as c
    full outer join (select * from {{ ref('mart_p1_pairs_original') }} where creation_year = 2022) as o
        on c.tag_a = o.tag_a and c.tag_b = o.tag_b
)

select
    *,
    abs(current_rate - original_rate) as rate_move
from compared
where (coalesce(current_top, 1000000) <= 10) != (coalesce(original_top, 1000000) <= 10)
    or (coalesce(current_bottom, 1000000) <= 10) != (coalesce(original_bottom, 1000000) <= 10)
    or abs(current_rate - original_rate) > 0.025

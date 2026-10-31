-- Materialized as a table: project default in dbt_project.yml.
-- AC-1.4: tags and pairs that enter or leave a top / bottom 10 between 2021 (the robustness year) and 2022 (the answer),
-- for accepted rate, answer rate and answers per question. Empty lists mean no change; `hard_flip` is top in one year
-- and bottom in the other.
with tags_flips as (
    {{ p1_rank_flips(ref('mart_p1_tags'), ['tag'], 'tags') }}
),

pairs_flips as (
    {{ p1_rank_flips(ref('mart_p1_pairs'), ['tag_a', 'tag_b'], 'pairs') }}
)

select * from tags_flips
union all
select * from pairs_flips

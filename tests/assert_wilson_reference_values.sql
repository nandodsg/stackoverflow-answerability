-- AC-1.5: the Wilson bounds of macros/stats.sql match the reference values of specs/001 (to 3 decimals):
-- 9/10 -> 0.596 / 0.982, 850/1000 -> 0.827 / 0.871, 1/1 -> 0.207 / 1.000, 0/1 -> 0.000 / 0.793. Reads no table.
{{ config(meta={'ac': 'AC-1.5'}) }}

with cases as (
    select * from unnest([
        struct(9.0 as k, 10.0 as n, 0.596 as expected_lower, 0.982 as expected_upper),
        (850.0, 1000.0, 0.827, 0.871),
        (1.0, 1.0, 0.207, 1.000),
        (0.0, 1.0, 0.000, 0.793)
    ])
)

select k, n, expected_lower, expected_upper
from cases
where abs({{ wilson_lower('k', 'n') }} - expected_lower) > 0.0005
    or abs({{ wilson_upper('k', 'n') }} - expected_upper) > 0.0005

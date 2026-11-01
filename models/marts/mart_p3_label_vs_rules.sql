-- Materialized as a table: project default in dbt_project.yml (the inline config() below only adds the tag).
-- AC-3.7, label against its rule-based neighbour (specs/003): a label should mostly agree with the rule that measures
-- something close to it. One row per label level x rule value over the 30,000 labeled questions (original text, all
-- years): how many questions, the share of the level's questions with that rule value, and the share of the rule
-- value's questions with that level. Pairs: worked example ~ has a code block; code focus ~ code-block count; image-only
-- evidence ~ has an image; setup dependence ~ has error text. A level whose rule value is far from what its name
-- suggests (e.g. most "worked example: yes" questions have no code block) is a label to question.
{{ config(tags=['needs_full_scan']) }}

with questions as (
    select * from {{ ref('int_p3_label_questions') }}
),

pairs as (
    select 'worked_example' as label, worked_example as level, 'has_code_block' as rule_feature,
        {{ p3_bucket('has_code_block', 'has_code_block') }} as rule_value
    from questions
    union all
    select 'code_focus', code_focus, 'code_block_count', {{ p3_bucket('code_block_count', 'code_block_count') }}
    from questions
    union all
    select 'image_only_evidence', image_only_evidence, 'has_image', {{ p3_bucket('has_image', 'has_image') }}
    from questions
    union all
    select 'environment_dependent', environment_dependent, 'has_error_text',
        {{ p3_bucket('has_error_text', 'has_error_text') }}
    from questions
),

counts as (
    select label, level, rule_feature, rule_value, count(*) as n_questions
    from pairs
    where level is not null
    group by label, level, rule_feature, rule_value
)

select
    *,
    safe_divide(n_questions, sum(n_questions) over (partition by label, level)) as share_of_level,
    safe_divide(n_questions, sum(n_questions) over (partition by label, rule_value)) as share_of_rule_value
from counts

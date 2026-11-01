-- The label layer must account for every labeled question and every rubric level. Any row returned names a problem.
{{ config(tags=['needs_full_scan']) }}

with questions as (
    select * from {{ ref('int_p3_label_questions') }}
),

levels as (
    select 'worked_example' as label, worked_example as level from questions
    union all select 'ask_scope', ask_scope from questions
    union all select 'failure_description', failure_description from questions
    union all select 'code_focus', code_focus from questions
    union all select 'environment_dependent', environment_dependent from questions
    union all select 'image_only_evidence', image_only_evidence from questions
),

problems as (
    select concat(label, ' = ', level) as item, 'level not mapped from the seed' as problem
    from levels
    where level = '9: unmapped'
    group by label, level

    union all

    -- 30,000 labeled questions minus the few with no history row, which int_p3_questions leaves out
    select 'question count', 'fewer than 29,900 labeled questions reach the P3 table'
    from (select count(*) as n from questions)
    where n < 29900

    union all

    -- the counts model must hold, per label, exactly the questions whose label is not null
    select concat(c.feature, ' (original)'), 'counts differ from the question table'
    from (
        select feature, sum(n_questions) as n
        from {{ ref('int_p3_label_bucket_counts') }}
        where version = 'original'
        group by feature
    ) as c
    inner join (
        select label, count(level) as n
        from levels
        group by label
    ) as q
        on q.label = c.feature
    where q.n != c.n
)

select * from problems

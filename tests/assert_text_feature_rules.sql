-- Hand-written examples for the text-feature rules in macros/text_features.sql (specs/003, "Feature table"): each
-- row below is a small text with the values we expect, and any row returned here is an example where a rule gives a
-- different value. Reads no table, so it bills nothing; it is the check that the Markdown and HTML rules mean the same
-- thing before the full scans use them.
{{ config(meta={'ac': 'AC-3.4'}) }}

with markdown_cases as (
    select * from unnest([
        struct(
            'M1 indented code, greeting, thanks' as case_id,
            'Hi,\r\n\r\n    print(1)\r\n\r\nThanks in advance' as raw_text,
            36 as exp_length, 1 as exp_blocks, false as exp_inline, false as exp_image, 0 as exp_links,
            false as exp_error, false as exp_effort, true as exp_greeting
        ),
        ('M2 three backticks on one line are inline code, not a block', 'Use ```x = 1``` here',
            20, 0, true, false, 0, false, false, false),
        ('M2b a fence on its own lines is a block, not inline code', 'Run:\n```python\nx = 1\n```\nDone',
            null, 1, false, false, 0, false, false, false),
        ('M2c the first line lost its indent: a block at the top', 'x = 1\n    y = 2\n    z = 3',
            null, 1, false, false, 0, false, false, false),
        ('M3 inline code, link, image', 'See `foo` and [docs](https://a.com) and ![img](https://b.com/x.png)',
            null, 0, true, true, 1, false, false, false),
        ('M4 plain text', 'plain text no code',
            18, 0, false, false, 0, false, false, false),
        ('M5 traceback', 'Traceback (most recent call last):\n  File "a.py"',
            null, 0, false, false, 0, true, false, false),
        ('M6 effort phrase', "I've tried this",
            null, 0, false, false, 0, false, true, false),
        ('M7 the word error without a colon is not an error text', 'Error handling is hard',
            null, 0, false, false, 0, false, false, false),
        ('M8 a blank line inside one indented block is still one block', 'Try this:\n\n    a = 1\n\n    b = 2\n\nDone',
            null, 1, false, false, 0, false, false, false),
        ('M9 two indented blocks apart', 'First:\n\n    a = 1\n\nThen:\n\n    b = 2',
            null, 2, false, false, 0, false, false, false),
        ('M10 a url inside code is not a link', 'See http://a.com and:\n\n    curl http://b.com\n\nor `http://c.com`',
            null, 1, true, false, 1, false, false, false),
        ('M11 an image wrapped in a link is an image and a link', '[![enter image description here][1]][1]\n\n  [1]: https://i.stack.imgur.com/a.png',
            null, 0, false, true, 1, false, false, false)
    ])
),

html_cases as (
    select * from unnest([
        struct(
            'H1 pre block, greeting after a tag' as case_id,
            '<p>Hello</p><pre><code>x = 1</code></pre>' as raw_text,
            10 as exp_length, 1 as exp_blocks, false as exp_inline, false as exp_image, 0 as exp_links,
            false as exp_error, false as exp_effort, true as exp_greeting
        ),
        ('H2 inline code, link, image', '<p>Use <code>foo</code> and <a href="https://a.com">docs</a> <img src="x"></p>',
            null, 0, true, true, 1, false, false, false),
        ('H3 thanks', '<p>Thanks in advance</p>',
            17, 0, false, false, 0, false, false, true),
        ('H4 error text inside a block', '<pre class="lang-py prettyprint-override"><code>raise ValueError: x</code></pre>',
            19, 1, false, false, 0, true, false, false)
    ])
),

markdown_features as (
    select
        case_id,
        exp_length, exp_blocks, exp_inline, exp_image, exp_links, exp_error, exp_effort, exp_greeting,
        {{ body_features('text_norm', 'markdown') }}
    from (select *, {{ normalize_text('raw_text', 'markdown') }} as text_norm from markdown_cases)
),

html_features as (
    select
        case_id,
        exp_length, exp_blocks, exp_inline, exp_image, exp_links, exp_error, exp_effort, exp_greeting,
        {{ body_features('text_norm', 'html') }}
    from (select *, {{ normalize_text('raw_text', 'html') }} as text_norm from html_cases)
),

title_cases as (
    select
        case_id,
        exp_length, exp_words, exp_question_mark, exp_question_word,
        {{ title_features('raw_title') }}
    from unnest([
        struct('T1 a question' as case_id, 'How do I sort a list?' as raw_title,
            21 as exp_length, 6 as exp_words, true as exp_question_mark, true as exp_question_word),
        ('T2 a statement', 'Python list sort', 16, 3, false, false),
        ('T3 a question word is a whole word', 'Whatever works', 14, 2, false, false)
    ])
),

body_mismatches as (
    select case_id from (
        select * from markdown_features
        union all
        select * from html_features
    )
    where (exp_length is not null and body_length != exp_length)
        or code_block_count != exp_blocks
        or has_inline_code != exp_inline
        or has_image != exp_image
        or link_count != exp_links
        or has_error_text != exp_error
        or has_effort_phrase != exp_effort
        or has_greeting_or_thanks != exp_greeting
),

title_mismatches as (
    select case_id
    from title_cases
    where title_length != exp_length
        or title_word_count != exp_words
        or title_ends_with_question != exp_question_mark
        or title_starts_with_question_word != exp_question_word
)

select * from body_mismatches
union all
select * from title_mismatches

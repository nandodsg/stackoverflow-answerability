{#-
    Text features for P3 (specs/003, "Feature table"). Each feature is one macro with one rule per text format:

      'markdown'  post_history.text   what the asker typed (code indented 4 spaces or fenced with ```)
      'html'      posts_questions.body  the rendered page (code in <pre><code>)

    The same feature list runs on both, so original-vs-current differences are real and not a parsing artifact.
    Rules are approximations of what a reader sees (a nested list can look like indented code); the 0.1% sample
    run checks that the two formats agree on never-edited questions before the full scans.

    Every macro takes a column name (a plain string column in the model's input CTE), never a raw expression, so the
    big text column is read once per model.
-#}


{# post_history.text uses Windows line endings; the regexes below assume "\n". #}
{% macro normalize_text(col, fmt) -%}
    {%- if fmt == 'markdown' -%}replace({{ col }}, '\r\n', '\n')
    {%- elif fmt == 'html' -%}{{ col }}
    {%- else -%}{{ exceptions.raise_compiler_error("fmt must be 'markdown' or 'html', got " ~ fmt) }}
    {%- endif -%}
{%- endmacro %}


{# Characters a reader sees: markdown as typed; html with the tags stripped (entities such as &lt; stay as they are). #}
{% macro body_length(col, fmt) -%}
    {%- if fmt == 'markdown' -%}length({{ col }})
    {%- else -%}length(regexp_replace({{ col }}, r'<[^>]*>', ''))
    {%- endif -%}
{%- endmacro %}


{# Fenced blocks: a fence is a line that starts with ``` and does not close on the same line (```x``` on one line is
   inline code in the rendered page); fences come in pairs. An indented block starts at the top of the text, or at an
   indented line that follows a non-indented line and then blank lines: blank lines INSIDE a block do not start a new
   one (a first version counted them, 3.5 blocks per question against 1.4 in html, in the 2% sample). The stored text
   loses the indent of its first line, so a text whose first line is followed directly by an indented line starts
   with a block (found by comparing both formats on never-edited questions). #}
{% macro code_block_count(col, fmt) -%}
    {%- if fmt == 'markdown' -%}
        div(array_length(regexp_extract_all({{ col }}, r'(?m)^ {0,3}```[^`\n]*$')), 2)
        + array_length(regexp_extract_all({{ col }}, r'^(?: {4}|\t)[^\n]'))
        + array_length(regexp_extract_all({{ col }}, r'^[^\n]+\n(?: {4}|\t)'))
        + array_length(regexp_extract_all({{ col }}, r'(?:^|\n)[^ \t\n][^\n]*\n(?:[ \t]*\n)+(?: {4}|\t)[^\n]'))
    {%- else -%}
        array_length(regexp_extract_all({{ col }}, r'<pre[ >]'))
    {%- endif -%}
{%- endmacro %}


{# Inline code: `x` or ```x``` on one line in markdown (a fence line has no closing ``` on its line, so it is
   not matched); a <code> that is not inside a <pre> in html (more <code> tags than <pre> tags). #}
{% macro has_inline_code(col, fmt) -%}
    {%- if fmt == 'markdown' -%}
        regexp_contains({{ col }}, r'```[^`\n]+```|`[^`\n]+`')
    {%- else -%}
        array_length(regexp_extract_all({{ col }}, r'<code[ >]')) > array_length(regexp_extract_all({{ col }}, r'<pre[ >]'))
    {%- endif -%}
{%- endmacro %}


{# Markdown images: ![alt](url) or the reference style ![alt][1]. #}
{% macro has_image(col, fmt) -%}
    {%- if fmt == 'markdown' -%}regexp_contains({{ col }}, r'!\[[^\]]*\](?:\(|\[)')
    {%- else -%}regexp_contains({{ col }}, r'<img[ >]')
    {%- endif -%}
{%- endmacro %}


{# Markdown with code (fenced, indented, inline) removed, so a URL inside code is not a link, as in the rendered html. #}
{% macro markdown_without_code(col) -%}
    regexp_replace(
        regexp_replace(
            regexp_replace({{ col }}, r'(?s)```.*?```', ''),
            r'(?:^|\n)(?: {4}|\t)[^\n]*', ''
        ),
        r'`[^`\n]*`', ''
    )
{%- endmacro %}


{# Links, plain images not counted. markdown: urls outside code, minus image urls, plus images wrapped in a link
   ([![alt][1]][1], the old image-upload markup, is <a><img></a> in html); html: <a> tags. #}
{% macro link_count(col, fmt) -%}
    {%- if fmt == 'markdown' -%}
        greatest(
            array_length(regexp_extract_all({{ markdown_without_code(col) }}, r'https?://'))
            - array_length(regexp_extract_all({{ markdown_without_code(col) }}, r'!\[[^\]]*\](?:\([^)]*\)|\[\d*\])'))
            + array_length(regexp_extract_all({{ markdown_without_code(col) }}, r'\[!\[')),
            0
        )
    {%- else -%}
        array_length(regexp_extract_all({{ col }}, r'<a[ >]'))
    {%- endif -%}
{%- endmacro %}


{# The wording is the same in both formats (tags do not split these phrases). #}
{% macro has_error_text(col, fmt) -%}
    regexp_contains({{ col }}, r'(?i)traceback \(most recent call last\)|\b\w*(?:error|exception)\b\s*:|segmentation fault|stack ?trace|\bat [\w.$]+\([\w.]+:\d+\)')
{%- endmacro %}


{% macro has_effort_phrase(col, fmt) -%}
    regexp_contains({{ col }}, r"(?i)\b(?:i(?:'ve| have)? tried|i(?:'m| am| have been) trying|i attempted|what i tried|my attempt|my code|here is what i|here's what i)\b")
{%- endmacro %}


{# A greeting at the very start (skipping any leading html tags) or thanks / "in advance" anywhere. #}
{% macro has_greeting_or_thanks(col, fmt) -%}
    regexp_contains({{ col }}, r'(?i)^(?:\s|<[^>]*>)*(?:hi|hello|hey|dear|good (?:morning|afternoon|evening))\b|\b(?:thanks|thank you|thx|in advance|cheers)\b')
{%- endmacro %}


{# Title features: titles are plain text in both sources, so no format argument. #}
{% macro title_features(col) -%}
    length({{ col }}) as title_length,
    array_length(split(trim({{ col }}), ' ')) as title_word_count,
    ends_with(trim({{ col }}), '?') as title_ends_with_question,
    regexp_contains({{ col }}, r'(?i)^\s*(?:how|why|what|when|where|which|who|is|are|can|could|does|do|should|will)\b') as title_starts_with_question_word
{%- endmacro %}


{# The body feature list, one column per feature; both scan models call this with their own column and format. #}
{% macro body_features(col, fmt) -%}
    {{ body_length(col, fmt) }} as body_length,
    {{ code_block_count(col, fmt) }} as code_block_count,
    {{ code_block_count(col, fmt) }} > 0 as has_code_block,
    {{ has_inline_code(col, fmt) }} as has_inline_code,
    {{ has_image(col, fmt) }} as has_image,
    {{ link_count(col, fmt) }} as link_count,
    {{ has_error_text(col, fmt) }} as has_error_text,
    {{ has_effort_phrase(col, fmt) }} as has_effort_phrase,
    {{ has_greeting_or_thanks(col, fmt) }} as has_greeting_or_thanks
{%- endmacro %}

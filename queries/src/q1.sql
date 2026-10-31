-- Prompt 1: which tags (and tag pairs) lead to the most and the fewest answers and accepted answers in the current year?
-- Runs as-is in the BigQuery console on bigquery-public-data.stackoverflow; no dbt and no other table needed.
-- @models: int_questions, mart_p1_tags, mart_p1_pairs
--
-- Reads three result sets, in this order: (1) the headline numbers, (2) the single-tag top / bottom 10 lists,
-- (3) the tag-pair top / bottom 10 lists. Expected: 2022 accepted rate 30.5%, 1,162 ranked tags, 1,026 ranked pairs.
--
-- Assumptions (definitions and reasons: specs/000 and specs/001 in the repo):
--   * "Current year" is 2022, the latest year in the snapshot; it is partial (the data ends 2022-09-25).
--   * Tags are the CURRENT tags. Tag edits made after the first answer can leak into the ranking: the `tag_exposure`
--     column is the share of a group's questions edited that way (the dbt project also reruns the ranking on the
--     original tags, which needs a one-time scan of post_history.text and is not part of this file).
--   * A question counts once for each of its tags; a pair is an unordered pair of tags on the same question.
--   * Accepted rate = accepted questions / ALL questions (not only answered ones). `answer_rate` and
--     `accepted_rate_among_answered` sit beside it: accepted rate = answer rate x accepted among answered.
--   * Answers per question is the "most answers" metric (total answers mostly measures volume).
--   * Floor: a group needs at least 385 questions in the year (the smallest n with a +/-5 point worst-case margin).
--   * Ranking uses a 95% interval, not the raw rate: "highest" lists sort by the LOWER bound, "lowest" lists by
--     the UPPER bound. Rates use the Wilson interval; answers per question uses mean +/- 1.96 x standard error.
--   * `answers_interval_reliable` is false where the normal interval is only approximate (Cochran's rule).
--   * Cost: reads questions, answers and post_history metadata columns only (never body or text), about 9 GB.

-- 1. Headline numbers.
select
    2022 as creation_year,
    count(*) as n_questions,
    countif(has_accepted_answer) as n_accepted,
    round(safe_divide(countif(has_accepted_answer), count(*)), 3) as accepted_rate,
    (select count(*) from mart_p1_tags where creation_year = 2022) as n_ranked_tags,
    (select count(*) from mart_p1_pairs where creation_year = 2022) as n_ranked_pairs,
    max(created_at) as newest_question_at
from int_questions
where creation_year = 2022;

-- 2. Single tags, 2022: top and bottom 10 for each metric.
select list, list_rank, tag, n_questions, answer_rate, accepted_rate, accepted_rate_among_answered,
    answers_per_question, accepted_rate_lower, accepted_rate_upper, answer_rate_lower, answer_rate_upper,
    answers_per_question_lower, answers_per_question_upper, answers_interval_reliable, tag_exposure
from (
    select 'accepted rate: highest' as list, rank_accepted_top as list_rank, * from mart_p1_tags
    union all select 'accepted rate: lowest', rank_accepted_bottom, * from mart_p1_tags
    union all select 'answer rate: highest', rank_answer_rate_top, * from mart_p1_tags
    union all select 'answer rate: lowest', rank_answer_rate_bottom, * from mart_p1_tags
    union all select 'answers per question: highest', rank_answers_top, * from mart_p1_tags
    union all select 'answers per question: lowest', rank_answers_bottom, * from mart_p1_tags
)
where creation_year = 2022 and list_rank <= 10
order by list, list_rank;

-- 3. Tag pairs, 2022: top and bottom 10 for each metric.
select list, list_rank, concat(tag_a, ' + ', tag_b) as tag_pair, n_questions, answer_rate, accepted_rate,
    accepted_rate_among_answered, answers_per_question, accepted_rate_lower, accepted_rate_upper,
    answer_rate_lower, answer_rate_upper, answers_per_question_lower, answers_per_question_upper,
    answers_interval_reliable, tag_exposure
from (
    select 'accepted rate: highest' as list, rank_accepted_top as list_rank, * from mart_p1_pairs
    union all select 'accepted rate: lowest', rank_accepted_bottom, * from mart_p1_pairs
    union all select 'answer rate: highest', rank_answer_rate_top, * from mart_p1_pairs
    union all select 'answer rate: lowest', rank_answer_rate_bottom, * from mart_p1_pairs
    union all select 'answers per question: highest', rank_answers_top, * from mart_p1_pairs
    union all select 'answers per question: lowest', rank_answers_bottom, * from mart_p1_pairs
)
where creation_year = 2022 and list_rank <= 10
order by list, list_rank;

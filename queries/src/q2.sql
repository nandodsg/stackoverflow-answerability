-- Prompt 2: for questions tagged ONLY python or ONLY dbt, how do the question-to-answer ratio and the accepted-answer
-- rate change year over year, 2013-2022, and how do the two compare?
-- Runs as-is in the BigQuery console on bigquery-public-data.stackoverflow; no dbt and no other table needed.
-- @models: mart_p2_python_dbt
--
-- One row per (tag, year): 20 rows. Expected answers per question: python 2.31 / 1.52 / 1.26 for 2013 / 2021 / 2022;
-- dbt 1.39 / 1.14 / 1.06 for 2020 / 2021 / 2022.
--
-- Assumptions (definitions and reasons: specs/000 and specs/002 in the repo):
--   * "Only python" / "only dbt" means the question's current tags are exactly `python` or exactly `dbt`
--     (one tag, no others). Years are the question's creation year; answers belong to their question's year.
--   * Answers per question is the headline ratio, with a 95% interval (mean +/- 1.96 x standard error). Questions per
--     answer is its inverse: Q/A = 1 / answers per question. Show it once, never as the charted ratio.
--   * Year-over-year change: `answers_per_question_yoy_abs` is the main number, `_yoy_rel` sits beside it; accepted
--     rate changes are in percentage points (`accepted_rate_yoy_pp`).
--   * Accepted rate = accepted questions / ALL questions; `answer_rate` and `accepted_rate_among_answered` split a
--     change into "fewer questions answered" and "askers accepting less".
--   * 2022 is partial (the data ends 2022-09-25) and its newest questions had little time to collect answers
--     (censoring), so the 2022 drop is mostly not a quality signal. `is_partial_year` flags it.
--   * dbt-only questions exist only from 2020 and are few (31 / 58 / 79): read the intervals, not the point values.
--     Years with no question stay as rows of zeros / nulls. 2013-2019 dbt rows are empty by design.
--   * `tag_exposure` is the share of a row's questions whose tags were first edited after the first answer.
--   * Cost: reads questions, answers and post_history metadata columns only (never body or text), about 7 GB.

select
    tag, creation_year, is_partial_year, n_questions, n_answered, n_accepted, n_answers,
    answer_rate, accepted_rate, accepted_rate_among_answered,
    answers_per_question, answers_per_question_lower, answers_per_question_upper,
    answers_per_question_yoy_abs, answers_per_question_yoy_rel, accepted_rate_yoy_pp,
    questions_per_answer, questions_per_answer_lower, questions_per_answer_upper,
    tag_exposure
from mart_p2_python_dbt
order by tag, creation_year;

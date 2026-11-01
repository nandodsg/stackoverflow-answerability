# Agreement: human vs spacexai/grok-4.7, practice set

20 questions labeled by both; rubric version(s) 5102cea87d4f, fd79297623f7 (earlier levels mapped to the current ones).

| Label | Agree | Kappa | Hand levels | Model levels |
|---|---|---|---|---|
| `worked_example` | 14/20 | 0.06 | no 16, yes 4 | no 16, yes 4 |
| `ask_scope` | 13/20 | 0.02 | narrow 14, broad 5, multiple 1 | narrow 18, broad 1, no_clear_ask 1 |
| `failure_description` | 13/20 | 0.48 | concrete 7, vague 7, not_applicable 6 | concrete 12, vague 1, not_applicable 7 |
| `code_focus` | 16/20 | 0.65 | focused 11, partial 2, not_applicable 7 | focused 10, partial 2, not_applicable 8 |
| `environment_dependent` | 19/20 | 0.77 | no 18, yes 2 | no 17, yes 3 |
| `image_only_evidence` | 15/20 | 0.22 | no 14, yes 6 | no 19, yes 1 |

## Disagreements

- `worked_example`, question 2 (63470444): hand **yes**, model **no**. Model: Thinner result only described, no literal output
- `worked_example`, question 3 (69088554): hand **yes**, model **no**. Model: Usage snippet and error, but no input with literal expected output.
- `worked_example`, question 11 (70467797): hand **no**, model **yes**. Model: Input rows and desired result table are both written out.
- `worked_example`, question 12 (57277785): hand **no**, model **yes**. Model: States -$97.90 should become ($97.90)
- `worked_example`, question 14 (57108044): hand **yes**, model **no**. Model: Example sentence given; expected match never written
- `worked_example`, question 20 (57286212): hand **no**, model **yes**. Model: Filters and the exact if-clause to generate are both written
- `ask_scope`, question 10 (57111221): hand **broad**, model **no_clear_ask**. Model: Body is filler, pasted component, and compile error; ask only in title.
- `ask_scope`, question 11 (70467797): hand **broad**, model **narrow**. Model: One specific SQL transform from shown input to shown result.
- `ask_scope`, question 13 (71703169): hand **broad**, model **narrow**. Model: One specific overlay that must cover the app bar
- `ask_scope`, question 15 (51163418): hand **broad**, model **narrow**. Model: One conceptual why-question a paragraph could answer; article request is secondary.
- `ask_scope`, question 17 (73570903): hand **multiple**, model **narrow**. Model: One specific styling fix: remove the click outline.
- `ask_scope`, question 18 (48124321): hand **narrow**, model **broad**. Model: Asks for the best HTML-compatible real-time plotting solution.
- `ask_scope`, question 20 (57286212): hand **broad**, model **narrow**. Model: One specific dynamic filter-check request; suggestions are secondary
- `failure_description`, question 2 (63470444): hand **not_applicable**, model **concrete**. Model: Says the linear indicator is very thick
- `failure_description`, question 4 (67861346): hand **vague**, model **concrete**. Model: Attempts only replace the first or last <
- `failure_description`, question 6 (61686467): hand **vague**, model **concrete**. Model: Item 2 errors and items 3 and 4 never run
- `failure_description`, question 13 (71703169): hand **vague**, model **concrete**. Model: Stack did not cover the app bar
- `failure_description`, question 15 (51163418): hand **vague**, model **not_applicable**. Model: Conceptual question with no reported failure or failed attempt.
- `failure_description`, question 16 (68229677): hand **vague**, model **concrete**. Model: Numbers show too many decimals and are not percentages.
- `failure_description`, question 20 (57286212): hand **vague**, model **not_applicable**. Model: How-to with eval disabled as a constraint, no failed attempt
- `code_focus`, question 1 (61947450): hand **partial**, model **not_applicable**. Model: Only debug traces, which are logs not code.
- `code_focus`, question 6 (61686467): hand **partial**, model **focused**. Model: One relevant try-catch loop, problem easy to locate
- `code_focus`, question 9 (67817486): hand **focused**, model **partial**. Model: Full compose; problem is one mount, custom conf omitted.
- `code_focus`, question 17 (73570903): hand **focused**, model **partial**. Model: Short but incomplete JSX fragments of the components.
- `environment_dependent`, question 9 (67817486): hand **no**, model **yes**. Model: About container volume deployment and missing host files.
- `image_only_evidence`, question 10 (57111221): hand **yes**, model **no**. Model: No images; error and code are in text.
- `image_only_evidence`, question 15 (51163418): hand **yes**, model **no**. Model: Diagram illustrates a point the text already states.
- `image_only_evidence`, question 16 (68229677): hand **yes**, model **no**. Model: Symptom and code are in text; image only illustrates.
- `image_only_evidence`, question 18 (48124321): hand **yes**, model **no**. Model: Image is a mockup of desired charts, not essential error or data.
- `image_only_evidence`, question 20 (57286212): hand **yes**, model **no**. Model: Excel screenshots only illustrate; data and filters are in text

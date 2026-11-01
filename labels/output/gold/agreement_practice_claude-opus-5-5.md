# Agreement: human vs claude-opus-5-5, practice set

20 questions labeled by both; rubric version(s) 5102cea87d4f (earlier levels mapped to the current ones).

| Label | Agree | Kappa | Hand levels | Model levels |
|---|---|---|---|---|
| `worked_example` | 15/20 | 0.14 | no 16, yes 4 | no 17, yes 3 |
| `ask_scope` | 13/20 | 0.22 | narrow 14, broad 5, multiple 1 | narrow 15, broad 2, no_clear_ask 3 |
| `failure_description` | 12/20 | 0.40 | concrete 7, vague 7, not_applicable 6 | concrete 13, not_applicable 7 |
| `code_focus` | 17/20 | 0.75 | focused 11, partial 2, not_applicable 7 | focused 9, partial 3, not_applicable 8 |
| `environment_dependent` | 16/20 | 0.41 | no 18, yes 2 | no 14, yes 6 |
| `image_only_evidence` | 15/20 | 0.22 | no 14, yes 6 | no 19, yes 1 |

## Disagreements

- `worked_example`, question 2 (63470444): hand **yes**, model **no**. Model: No literal input/output pair; desired thinness only described in words.
- `worked_example`, question 3 (69088554): hand **yes**, model **no**. Model: Error and code shown, but no concrete input with literal desired output.
- `worked_example`, question 11 (70467797): hand **no**, model **yes**. Model: Input table and literal desired result table both written out.
- `worked_example`, question 12 (57277785): hand **no**, model **yes**. Model: Input -$97.90 and desired output ($97.90) both written literally.
- `worked_example`, question 14 (57108044): hand **yes**, model **no**. Model: Example sentence given but desired output (e.g., 'bengali') never written literally.
- `ask_scope`, question 1 (61947450): hand **narrow**, model **no_clear_ask**. Model: Only says 'Any help would be appreciated' after describing the symptom; no explicit stated ask.
- `ask_scope`, question 10 (57111221): hand **broad**, model **no_clear_ask**. Model: Body is only a filler line, pasted code and an error; no stated ask.
- `ask_scope`, question 11 (70467797): hand **broad**, model **no_clear_ask**. Model: Body only shows tables; the request lives only in the title.
- `ask_scope`, question 15 (51163418): hand **broad**, model **narrow**. Model: Single conceptual question why a function has a prototype property.
- `ask_scope`, question 17 (73570903): hand **multiple**, model **narrow**. Model: Single ask: remove the outline that appears on click.
- `ask_scope`, question 18 (48124321): hand **narrow**, model **broad**. Model: Asks for the best solution/tool for real-time web plotting.
- `ask_scope`, question 20 (57286212): hand **broad**, model **narrow**. Model: One specific ask: evaluate a dynamic filter chain without eval; the improvement request is secondary.
- `failure_description`, question 2 (63470444): hand **not_applicable**, model **concrete**. Model: Symptom 'very thick' is concrete, but no exact expected value or error.
- `failure_description`, question 4 (67861346): hand **vague**, model **concrete**. Model: Says attempts only replace first or last occurrence; no exact actual output shown.
- `failure_description`, question 5 (65997173): hand **vague**, model **concrete**. Model: Says OR in THEN 'is not supporting' without exact error text or expected behaviour detail.
- `failure_description`, question 6 (61686467): hand **vague**, model **concrete**. Model: States what happens (stops after item 2) and what should happen (run 3 and 4).
- `failure_description`, question 13 (71703169): hand **vague**, model **concrete**. Model: Past Stack attempt did not cover the app bar: a concrete symptom, no error.
- `failure_description`, question 15 (51163418): hand **vague**, model **not_applicable**. Model: No failure reported; purely conceptual question.
- `failure_description`, question 16 (68229677): hand **vague**, model **concrete**. Model: Attempt shown; symptom of too many decimals and non-percentage values, no exact error or literal expected output.
- `failure_description`, question 20 (57286212): hand **vague**, model **not_applicable**. Model: How-to question; no attempt that went wrong is reported, eval being disabled is just a constraint.
- `code_focus`, question 1 (61947450): hand **partial**, model **not_applicable**. Model: Only debug log output is posted; no source code or config.
- `code_focus`, question 9 (67817486): hand **focused**, model **partial**. Model: Full compose file with letsencrypt service; relevant volume line is buried but related.
- `code_focus`, question 10 (57111221): hand **focused**, model **partial**. Model: Single relevant component, but long repetitive carousel markup beyond the import issue.
- `environment_dependent`, question 3 (69088554): hand **no**, model **yes**. Model: Fixture availability depends on installed pytest version/plugin config, not shown.
- `environment_dependent`, question 6 (61686467): hand **no**, model **yes**. Model: Depends on the asker's game servers and SourceQuery connections, which cannot be reproduced from the post.
- `environment_dependent`, question 9 (67817486): hand **no**, model **yes**. Model: yes
- `environment_dependent`, question 19 (51651956): hand **no**, model **yes**. Model: yes
- `image_only_evidence`, question 10 (57111221): hand **yes**, model **no**. Model: No images; the error is given in text.
- `image_only_evidence`, question 15 (51163418): hand **yes**, model **no**. Model: Image illustrates article diagram; question stated in text with names.
- `image_only_evidence`, question 16 (68229677): hand **yes**, model **no**. Model: Image shows the symptom, which the text also describes (long decimals, PLF not percentage).
- `image_only_evidence`, question 18 (48124321): hand **yes**, model **no**. Model: Image only illustrates the desired chart type, a mockup of the goal.
- `image_only_evidence`, question 20 (57286212): hand **yes**, model **no**. Model: Images illustrate an Excel analogy; the essential data and intended condition are given in code.

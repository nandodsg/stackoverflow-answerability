# Agreement: google/gemini-4-argon vs spacexai/grok-4.7, practice set

20 questions labeled by both; rubric version(s) fd79297623f7 (earlier levels mapped to the current ones).

| Label | Agree | Kappa | google/gemini-4-argon levels | spacexai/grok-4.7 levels |
|---|---|---|---|---|
| `worked_example` | 19/20 | 0.83 | no 17, yes 3 | no 16, yes 4 |
| `ask_scope` | 20/20 | 1.00 | narrow 18, broad 1, no_clear_ask 1 | narrow 18, broad 1, no_clear_ask 1 |
| `failure_description` | 20/20 | 1.00 | concrete 12, vague 1, not_applicable 7 | concrete 12, vague 1, not_applicable 7 |
| `code_focus` | 17/20 | 0.75 | focused 9, partial 3, not_applicable 8 | focused 10, partial 2, not_applicable 8 |
| `environment_dependent` | 20/20 | 1.00 | no 17, yes 3 | no 17, yes 3 |
| `image_only_evidence` | 20/20 | 1.00 | no 19, yes 1 | no 19, yes 1 |

## Disagreements

- `worked_example`, question 20 (57286212): google/gemini-4-argon **no**, spacexai/grok-4.7 **yes**. google/gemini-4-argon: Provides input arrays in code, but the expected output array is only shown in an image, not written out. spacexai/grok-4.7: Filters and the exact if-clause to generate are both written
- `code_focus`, question 6 (61686467): google/gemini-4-argon **partial**, spacexai/grok-4.7 **focused**. google/gemini-4-argon: Shows the relevant loop and try-catch block, along with extra array population and file check lines. spacexai/grok-4.7: One relevant try-catch loop, problem easy to locate
- `code_focus`, question 10 (57111221): google/gemini-4-argon **partial**, spacexai/grok-4.7 **focused**. google/gemini-4-argon: Includes a whole component file when the error sits on a single import line. spacexai/grok-4.7: Short carousel component centered on the failing import.
- `code_focus`, question 17 (73570903): google/gemini-4-argon **focused**, spacexai/grok-4.7 **partial**. google/gemini-4-argon: Shows only the short, relevant JSX snippets for the Dropdown and Button components. spacexai/grok-4.7: Short but incomplete JSX fragments of the components.

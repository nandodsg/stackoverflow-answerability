# Agreement: reviewed vs spacexai/grok-4.7, scoring set

100 questions labeled by both; rubric version(s) fd79297623f7 (earlier levels mapped to the current ones).

| Label | Agree | Kappa | reviewed levels | spacexai/grok-4.7 levels |
|---|---|---|---|---|
| `worked_example` | 99/100 | 0.94 | no 91, yes 9 | no 92, yes 8 |
| `ask_scope` | 97/100 | 0.81 | narrow 91, broad 5, multiple 3, no_clear_ask 1 | narrow 92, broad 5, multiple 3 |
| `failure_description` | 99/100 | 0.98 | concrete 64, vague 6, not_applicable 30 | concrete 65, vague 5, not_applicable 30 |
| `code_focus` | 94/100 | 0.90 | focused 57, partial 13, dump 2, not_applicable 28 | focused 52, partial 18, dump 1, not_applicable 29 |
| `environment_dependent` | 96/100 | 0.84 | no 83, yes 17 | no 87, yes 13 |
| `image_only_evidence` | 97/100 | 0.65 | no 94, yes 6 | no 97, yes 3 |

## Disagreements

- `worked_example`, question 49 (57432557): reviewed **yes**, spacexai/grok-4.7 **no**. spacexai/grok-4.7: Menu shown; desired digit only described, not written as output
- `ask_scope`, question 34 (71019316): reviewed **no_clear_ask**, spacexai/grok-4.7 **narrow**. spacexai/grok-4.7: One specific question: locate the error in this function.
- `ask_scope`, question 51 (69353815): reviewed **narrow**, spacexai/grok-4.7 **broad**. spacexai/grok-4.7: Open how-to needing a multi-instance design
- `ask_scope`, question 55 (49399160): reviewed **broad**, spacexai/grok-4.7 **narrow**. spacexai/grok-4.7: One specific request: run the shown backup monthly
- `failure_description`, question 97 (59947919): reviewed **vague**, spacexai/grok-4.7 **concrete**. spacexai/grok-4.7: Reports the pasted page shows the code part as blank.
- `code_focus`, question 43 (54324062): reviewed **focused**, spacexai/grok-4.7 **partial**. spacexai/grok-4.7: Relevant chunks include unused imports, path changes, and extra loads.
- `code_focus`, question 77 (69437052): reviewed **focused**, spacexai/grok-4.7 **partial**. spacexai/grok-4.7: Short relevant snippet, but fragmentary and omits failing endAdornment.
- `code_focus`, question 81 (55283908): reviewed **dump**, spacexai/grok-4.7 **partial**. spacexai/grok-4.7: Short init commands shown; receive code missing
- `code_focus`, question 85 (64698368): reviewed **focused**, spacexai/grok-4.7 **not_applicable**. spacexai/grok-4.7: No code block or pasted source, only a URL and headers
- `code_focus`, question 89 (73675257): reviewed **focused**, spacexai/grok-4.7 **partial**. spacexai/grok-4.7: Short relevant snippet, but unclosed and slightly fragmentary.
- `code_focus`, question 93 (71675281): reviewed **focused**, spacexai/grok-4.7 **partial**. spacexai/grok-4.7: Relevant but fragmentary centroid-assignment snippet
- `environment_dependent`, question 15 (69821469): reviewed **yes**, spacexai/grok-4.7 **no**. spacexai/grok-4.7: About sample drag behavior, not the asker's setup
- `environment_dependent`, question 81 (55283908): reviewed **yes**, spacexai/grok-4.7 **no**. spacexai/grok-4.7: Split-read behavior answerable without their device setup
- `environment_dependent`, question 84 (69966579): reviewed **yes**, spacexai/grok-4.7 **no**. spacexai/grok-4.7: UI layout behavior answerable generally, not an install or config task.
- `environment_dependent`, question 87 (71390078): reviewed **yes**, spacexai/grok-4.7 **no**. spacexai/grok-4.7: Code and API behavior, not the asker's own setup.
- `image_only_evidence`, question 17 (48844194): reviewed **yes**, spacexai/grok-4.7 **no**. spacexai/grok-4.7: The request is stated in text; screenshot is only illustrative
- `image_only_evidence`, question 46 (69706877): reviewed **yes**, spacexai/grok-4.7 **no**. spacexai/grok-4.7: Inputs, merge code, and suffix symptom are all in text.
- `image_only_evidence`, question 85 (64698368): reviewed **yes**, spacexai/grok-4.7 **no**. spacexai/grok-4.7: Not-found error and URL are already written in text

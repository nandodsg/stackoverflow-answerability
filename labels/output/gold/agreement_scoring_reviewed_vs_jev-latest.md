# Agreement: reviewed vs jev-latest, scoring set

100 questions labeled by both; rubric version(s) fd79297623f7 (earlier levels mapped to the current ones).

| Label | Agree | Kappa | reviewed levels | jev-latest levels |
|---|---|---|---|---|
| `worked_example` | 97/100 | 0.81 | no 91, yes 9 | no 92, yes 8 |
| `ask_scope` | 98/100 | 0.87 | narrow 91, broad 5, multiple 3, no_clear_ask 1 | narrow 93, broad 4, multiple 3 |
| `failure_description` | 99/100 | 0.98 | concrete 64, vague 6, not_applicable 30 | concrete 65, vague 5, not_applicable 30 |
| `code_focus` | 85/100 | 0.74 | focused 57, partial 13, dump 2, not_applicable 28 | focused 55, partial 14, dump 1, not_applicable 30 |
| `environment_dependent` | 92/100 | 0.72 | no 83, yes 17 | no 83, yes 17 |
| `image_only_evidence` | 97/100 | 0.71 | no 94, yes 6 | no 95, yes 5 |

## Disagreements

- `worked_example`, question 11 (55411003): reviewed **yes**, jev-latest **no**.
- `worked_example`, question 24 (48989171): reviewed **no**, jev-latest **yes**.
- `worked_example`, question 49 (57432557): reviewed **yes**, jev-latest **no**.
- `ask_scope`, question 34 (71019316): reviewed **no_clear_ask**, jev-latest **narrow**.
- `ask_scope`, question 55 (49399160): reviewed **broad**, jev-latest **narrow**.
- `failure_description`, question 97 (59947919): reviewed **vague**, jev-latest **concrete**.
- `code_focus`, question 2 (59720878): reviewed **partial**, jev-latest **dump**.
- `code_focus`, question 3 (70911929): reviewed **partial**, jev-latest **focused**.
- `code_focus`, question 42 (59328317): reviewed **not_applicable**, jev-latest **focused**.
- `code_focus`, question 43 (54324062): reviewed **focused**, jev-latest **partial**.
- `code_focus`, question 47 (66133661): reviewed **dump**, jev-latest **partial**.
- `code_focus`, question 65 (48504766): reviewed **focused**, jev-latest **not_applicable**.
- `code_focus`, question 78 (68759793): reviewed **partial**, jev-latest **focused**.
- `code_focus`, question 80 (69925081): reviewed **focused**, jev-latest **partial**.
- `code_focus`, question 81 (55283908): reviewed **dump**, jev-latest **not_applicable**.
- `code_focus`, question 85 (64698368): reviewed **focused**, jev-latest **not_applicable**.
- `code_focus`, question 87 (71390078): reviewed **focused**, jev-latest **partial**.
- `code_focus`, question 88 (50907776): reviewed **partial**, jev-latest **focused**.
- `code_focus`, question 90 (73012994): reviewed **partial**, jev-latest **focused**.
- `code_focus`, question 92 (73623911): reviewed **focused**, jev-latest **partial**.
- `code_focus`, question 96 (69483166): reviewed **focused**, jev-latest **partial**.
- `environment_dependent`, question 8 (61074096): reviewed **no**, jev-latest **yes**.
- `environment_dependent`, question 15 (69821469): reviewed **yes**, jev-latest **no**.
- `environment_dependent`, question 17 (48844194): reviewed **no**, jev-latest **yes**.
- `environment_dependent`, question 28 (59922861): reviewed **yes**, jev-latest **no**.
- `environment_dependent`, question 66 (49802367): reviewed **no**, jev-latest **yes**.
- `environment_dependent`, question 75 (66116135): reviewed **yes**, jev-latest **no**.
- `environment_dependent`, question 87 (71390078): reviewed **yes**, jev-latest **no**.
- `environment_dependent`, question 98 (57437460): reviewed **no**, jev-latest **yes**.
- `image_only_evidence`, question 17 (48844194): reviewed **yes**, jev-latest **no**.
- `image_only_evidence`, question 46 (69706877): reviewed **yes**, jev-latest **no**.
- `image_only_evidence`, question 99 (73288048): reviewed **no**, jev-latest **yes**.

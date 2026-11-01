# Agreement: reviewed vs google/gemini-4-argon, scoring set

100 questions labeled by both; rubric version(s) fd79297623f7 (earlier levels mapped to the current ones).

| Label | Agree | Kappa | reviewed levels | google/gemini-4-argon levels |
|---|---|---|---|---|
| `worked_example` | 99/100 | 0.94 | no 91, yes 9 | no 92, yes 8 |
| `ask_scope` | 99/100 | 0.94 | narrow 91, broad 5, multiple 3, no_clear_ask 1 | narrow 90, broad 5, multiple 3, no_clear_ask 2 |
| `failure_description` | 95/100 | 0.90 | concrete 64, vague 6, not_applicable 30 | concrete 63, vague 10, not_applicable 27 |
| `code_focus` | 96/100 | 0.93 | focused 57, partial 13, dump 2, not_applicable 28 | focused 56, partial 12, dump 4, not_applicable 28 |
| `environment_dependent` | 99/100 | 0.97 | no 83, yes 17 | no 82, yes 18 |
| `image_only_evidence` | 97/100 | 0.75 | no 94, yes 6 | no 93, yes 7 |

## Disagreements

- `worked_example`, question 11 (55411003): reviewed **yes**, google/gemini-4-argon **no**. google/gemini-4-argon: Shows code and generated SQL, but no sample data input or desired data output.
- `ask_scope`, question 52 (71305015): reviewed **narrow**, google/gemini-4-argon **no_clear_ask**. google/gemini-4-argon: The body contains only filler and pasted code; the actual goal lives only in the title.
- `failure_description`, question 14 (62255052): reviewed **concrete**, google/gemini-4-argon **not_applicable**. google/gemini-4-argon: This is a how-to question with no failed code attempt reported.
- `failure_description`, question 17 (48844194): reviewed **not_applicable**, google/gemini-4-argon **vague**. google/gemini-4-argon: Implies highlighting is improper, with the actual symptom shown only in an image.
- `failure_description`, question 34 (71019316): reviewed **not_applicable**, google/gemini-4-argon **vague**. google/gemini-4-argon: Mentions a mistake and error without naming any symptom or error message.
- `failure_description`, question 52 (71305015): reviewed **not_applicable**, google/gemini-4-argon **vague**. google/gemini-4-argon: Only says 'struggling with a very simple problem' without stating any error or symptom.
- `failure_description`, question 90 (73012994): reviewed **not_applicable**, google/gemini-4-argon **vague**. google/gemini-4-argon: Includes a failed click-handler attempt and says "having trouble" without naming a concrete symptom or error.
- `code_focus`, question 9 (66295771): reviewed **focused**, google/gemini-4-argon **partial**. google/gemini-4-argon: Shows the method and click handler, but omits how GeoIPModule is defined or instantiated.
- `code_focus`, question 48 (51294665): reviewed **focused**, google/gemini-4-argon **dump**. google/gemini-4-argon: Code fragment is missing the hover handler and styling logic where the border is actually applied.
- `code_focus`, question 60 (72129652): reviewed **partial**, google/gemini-4-argon **focused**. google/gemini-4-argon: Provides a short, self-contained widget and main function focused directly on the routing setup and button call.
- `code_focus`, question 67 (51305452): reviewed **partial**, google/gemini-4-argon **dump**. google/gemini-4-argon: Includes unrelated PHP controller code and omits the HTML for the popup form fields being toggled.
- `environment_dependent`, question 8 (61074096): reviewed **no**, google/gemini-4-argon **yes**. google/gemini-4-argon: Concerns performance and resource usage on the asker's production RDS database setup.
- `image_only_evidence`, question 37 (56776190): reviewed **no**, google/gemini-4-argon **yes**. google/gemini-4-argon: Asks if jars are missing in the build path, which is only shown in image 1.
- `image_only_evidence`, question 73 (59907596): reviewed **no**, google/gemini-4-argon **yes**. google/gemini-4-argon: The actual update queries being run are shown only in a screenshot.
- `image_only_evidence`, question 74 (55208667): reviewed **yes**, google/gemini-4-argon **no**. google/gemini-4-argon: Images show example symbols to process; the task of counting lines is already clear from text.

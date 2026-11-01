# Agreement: human vs google/gemini-4-argon, practice set

20 questions labeled by both; rubric version(s) 5102cea87d4f, fd79297623f7 (earlier levels mapped to the current ones).

| Label | Agree | Kappa | Hand levels | Model levels |
|---|---|---|---|---|
| `worked_example` | 15/20 | 0.14 | no 16, yes 4 | no 17, yes 3 |
| `ask_scope` | 13/20 | 0.02 | narrow 14, broad 5, multiple 1 | narrow 18, broad 1, no_clear_ask 1 |
| `failure_description` | 13/20 | 0.48 | concrete 7, vague 7, not_applicable 6 | concrete 12, vague 1, not_applicable 7 |
| `code_focus` | 17/20 | 0.75 | focused 11, partial 2, not_applicable 7 | focused 9, partial 3, not_applicable 8 |
| `environment_dependent` | 19/20 | 0.77 | no 18, yes 2 | no 17, yes 3 |
| `image_only_evidence` | 15/20 | 0.22 | no 14, yes 6 | no 19, yes 1 |

## Disagreements

- `worked_example`, question 2 (63470444): hand **yes**, model **no**. Model: The desired outcome of making the indicator thinner is described in prose, not as literal input/output data.
- `worked_example`, question 3 (69088554): hand **yes**, model **no**. Model: Shows test code and an error, not a concrete input/output data pair.
- `worked_example`, question 11 (70467797): hand **no**, model **yes**. Model: Both the concrete input table and literal desired output table are written out.
- `worked_example`, question 12 (57277785): hand **no**, model **yes**. Model: Concrete input `-$97.90` and literal desired output `($97.90)` are both written out.
- `worked_example`, question 14 (57108044): hand **yes**, model **no**. Model: Gives an example input sentence, but the literal expected output is never written out.
- `ask_scope`, question 10 (57111221): hand **broad**, model **no_clear_ask**. Model: Body only contains a 'not working' filler line, pasted code, and an error message.
- `ask_scope`, question 11 (70467797): hand **broad**, model **narrow**. Model: Asks for a single query to produce the specified result table.
- `ask_scope`, question 13 (71703169): hand **broad**, model **narrow**. Model: How-to for one specific UI operation that mentions 'best' only in passing.
- `ask_scope`, question 15 (51163418): hand **broad**, model **narrow**. Model: Asks a specific conceptual question about why a JavaScript function has a property.
- `ask_scope`, question 17 (73570903): hand **multiple**, model **narrow**. Model: Asks for a single specific CSS/component fix to remove the outline on click.
- `ask_scope`, question 18 (48124321): hand **narrow**, model **broad**. Model: Asks for a recommendation on the best HTML-compatible solution or tool.
- `ask_scope`, question 20 (57286212): hand **broad**, model **narrow**. Model: Asks how to dynamically evaluate an array of filter conditions in PHP; the 'suggestions welcome' line is clearly secondary.
- `failure_description`, question 2 (63470444): hand **not_applicable**, model **concrete**. Model: Shows an attempt with LinearProgressIndicator and states the observable symptom that 'it is very thick'.
- `failure_description`, question 4 (67861346): hand **vague**, model **concrete**. Model: Code comment states the attempts "typically only replace the first or last occurence of <".
- `failure_description`, question 6 (61686467): hand **vague**, model **concrete**. Model: Describes a concrete symptom: when item 2 enters catch, it stops and does not run 3 and 4.
- `failure_description`, question 13 (71703169): hand **vague**, model **concrete**. Model: Describes the observable symptom of a prior attempt: 'stack was not covered my App bar'.
- `failure_description`, question 15 (51163418): hand **vague**, model **not_applicable**. Model: Purely conceptual question about JavaScript properties with no failing code or attempt.
- `failure_description`, question 16 (68229677): hand **vague**, model **concrete**. Model: Describes observable symptoms: numbers have very large decimal places and are not in percentage form.
- `failure_description`, question 20 (57286212): hand **vague**, model **not_applicable**. Model: How-to question with no failed attempt; 'eval is disabled on my PHP' is a constraint, not a failure.
- `code_focus`, question 1 (61947450): hand **partial**, model **not_applicable**. Model: The blocks are debug trace output from running a command, not source code or config.
- `code_focus`, question 9 (67817486): hand **focused**, model **partial**. Model: Shows a full docker-compose file when the issue is in one volume mount and an unshown config.
- `code_focus`, question 10 (57111221): hand **focused**, model **partial**. Model: Includes a whole component file when the error sits on a single import line.
- `environment_dependent`, question 9 (67817486): hand **no**, model **yes**. Model: About configuring Docker containers and hinges on the unshown myconf.conf file on the asker's machine.
- `image_only_evidence`, question 10 (57111221): hand **yes**, model **no**. Model: No external images; the img tags are inside the pasted JSX code.
- `image_only_evidence`, question 15 (51163418): hand **yes**, model **no**. Model: The conceptual question is fully stated in text; the image is just an illustrative diagram.
- `image_only_evidence`, question 16 (68229677): hand **yes**, model **no**. Model: The image illustrates the table, but the text already explains the decimal and percentage issues.
- `image_only_evidence`, question 18 (48124321): hand **yes**, model **no**. Model: The image is just an illustration of desired plot types, not essential evidence.
- `image_only_evidence`, question 20 (57286212): hand **yes**, model **no**. Model: The Excel screenshots only illustrate the concept; the actual PHP arrays and rules are written out in code blocks.

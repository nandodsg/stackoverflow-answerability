# Agreement: reviewed vs openai/gpt-6-luna, scoring set

100 questions labeled by both; rubric version(s) fd79297623f7 (earlier levels mapped to the current ones).

| Label | Agree | Kappa | reviewed levels | openai/gpt-6-luna levels |
|---|---|---|---|---|
| `worked_example` | 93/100 | 0.63 | no 91, yes 9 | no 88, yes 12 |
| `ask_scope` | 96/100 | 0.75 | narrow 91, broad 5, multiple 3, no_clear_ask 1 | narrow 92, broad 3, multiple 4, no_clear_ask 1 |
| `failure_description` | 91/100 | 0.83 | concrete 64, vague 6, not_applicable 30 | concrete 62, vague 11, not_applicable 27 |
| `code_focus` | 72/100 | 0.57 | focused 57, partial 13, dump 2, not_applicable 28 | focused 44, partial 18, dump 11, not_applicable 27 |
| `environment_dependent` | 93/100 | 0.79 | no 83, yes 17 | no 76, yes 24 |
| `image_only_evidence` | 98/100 | 0.79 | no 94, yes 6 | no 96, yes 4 |

## Disagreements

- `worked_example`, question 3 (70911929): reviewed **yes**, openai/gpt-6-luna **no**. openai/gpt-6-luna: The desired table is shown, but no concrete input is separately written out.
- `worked_example`, question 7 (55104952): reviewed **no**, openai/gpt-6-luna **yes**. openai/gpt-6-luna: Shows `make fileName.cpp` and the desired executable `./fileName`.
- `worked_example`, question 11 (55411003): reviewed **yes**, openai/gpt-6-luna **no**. openai/gpt-6-luna: Shows the query and desired SQL fragment, but no concrete input/output pair.
- `worked_example`, question 31 (55219369): reviewed **no**, openai/gpt-6-luna **yes**. openai/gpt-6-luna: The option is set to True, and the asker wants it to be False.
- `worked_example`, question 45 (53599655): reviewed **no**, openai/gpt-6-luna **yes**. openai/gpt-6-luna: Names the source path and the desired destination file path.
- `worked_example`, question 54 (52372892): reviewed **no**, openai/gpt-6-luna **yes**. openai/gpt-6-luna: The 45-degree turn is paired with the desired 45-degree marker rotation.
- `worked_example`, question 67 (51305452): reviewed **no**, openai/gpt-6-luna **yes**. openai/gpt-6-luna: The long-term radio option is paired with the stated desired output: only the Monthly field displayed.
- `ask_scope`, question 34 (71019316): reviewed **no_clear_ask**, openai/gpt-6-luna **narrow**. openai/gpt-6-luna: Asks where an error is in one specific function.
- `ask_scope`, question 40 (48784152): reviewed **broad**, openai/gpt-6-luna **multiple**. openai/gpt-6-luna: Asks for a package recommendation and separately how to monitor beacon proximity.
- `ask_scope`, question 52 (71305015): reviewed **narrow**, openai/gpt-6-luna **no_clear_ask**. openai/gpt-6-luna: The body says the asker is struggling but leaves the goal to the title.
- `ask_scope`, question 55 (49399160): reviewed **broad**, openai/gpt-6-luna **narrow**. openai/gpt-6-luna: The single request is to run the backup monthly.
- `failure_description`, question 17 (48844194): reviewed **not_applicable**, openai/gpt-6-luna **vague**. openai/gpt-6-luna: Says highlighting should be proper but gives no specific symptom in text.
- `failure_description`, question 26 (60344916): reviewed **not_applicable**, openai/gpt-6-luna **vague**. openai/gpt-6-luna: “I'm not getting anywhere” gives no observable failure symptom.
- `failure_description`, question 35 (66285712): reviewed **concrete**, openai/gpt-6-luna **vague**. openai/gpt-6-luna: The only symptom is that the call “doesn't do anything.”
- `failure_description`, question 65 (48504766): reviewed **concrete**, openai/gpt-6-luna **vague**. openai/gpt-6-luna: The project “doesn't seem to be finding it,” with no specific symptom or error.
- `failure_description`, question 80 (69925081): reviewed **not_applicable**, openai/gpt-6-luna **vague**. openai/gpt-6-luna: Says the controls cannot be accessed there, without a specific symptom or error.
- `failure_description`, question 91 (64044429): reviewed **concrete**, openai/gpt-6-luna **not_applicable**. openai/gpt-6-luna: Asks about execution behavior; no failed attempt or symptom is reported.
- `failure_description`, question 97 (59947919): reviewed **vague**, openai/gpt-6-luna **concrete**. openai/gpt-6-luna: Reports the webpage shows the code part as blank.
- `failure_description`, question 99 (73288048): reviewed **not_applicable**, openai/gpt-6-luna **concrete**. openai/gpt-6-luna: Describes the observable behavior: debug-off mode shows only a 500 screen.
- `failure_description`, question 100 (58762459): reviewed **concrete**, openai/gpt-6-luna **vague**. openai/gpt-6-luna: The errors are only in the screenshot; the text says only that the build fails.
- `code_focus`, question 2 (59720878): reviewed **partial**, openai/gpt-6-luna **dump**. openai/gpt-6-luna: The full page and configuration files include substantial code beyond the export issue.
- `code_focus`, question 3 (70911929): reviewed **partial**, openai/gpt-6-luna **focused**. openai/gpt-6-luna: The short employee and entry-form code includes the relevant printing loop.
- `code_focus`, question 9 (66295771): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: The relevant function and attempted call are shown, but the defining context is missing.
- `code_focus`, question 10 (73760417): reviewed **partial**, openai/gpt-6-luna **dump**. openai/gpt-6-luna: Includes the whole view page with substantial unrelated layout and styling markup.
- `code_focus`, question 11 (55411003): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: Relevant query and model snippets are short but fragmentary.
- `code_focus`, question 18 (66815431): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: Relevant module snippets are shown, but the component declaration and input are missing.
- `code_focus`, question 27 (59995557): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: The short snippet is relevant but omits where the URL is defined.
- `code_focus`, question 29 (67862183): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: The relevant creation call is shown, but the snippet is fragmentary.
- `code_focus`, question 30 (60012034): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: The snippet is relevant, but relies on undefined inputs and external types.
- `code_focus`, question 38 (54437485): reviewed **partial**, openai/gpt-6-luna **dump**. openai/gpt-6-luna: The post includes the complete HTML page and controls, not just the relevant selection code.
- `code_focus`, question 42 (59328317): reviewed **not_applicable**, openai/gpt-6-luna **focused**. openai/gpt-6-luna: A single relevant logging call shows the issue.
- `code_focus`, question 43 (54324062): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: The plotting code is included with related setup and data-loading code, plus unnecessary imports and directory changes.
- `code_focus`, question 48 (51294665): reviewed **focused**, openai/gpt-6-luna **dump**. openai/gpt-6-luna: The snippet omits the code that applies the border, which is central to the question.
- `code_focus`, question 53 (62952036): reviewed **partial**, openai/gpt-6-luna **dump**. openai/gpt-6-luna: The full view includes extensive styling and certificate content beyond the image-loading issue.
- `code_focus`, question 55 (49399160): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: The short backup snippet is relevant but omits surrounding declarations and context.
- `code_focus`, question 60 (72129652): reviewed **partial**, openai/gpt-6-luna **focused**. openai/gpt-6-luna: The relevant route table and navigation call appear in a compact app snippet.
- `code_focus`, question 61 (53494235): reviewed **focused**, openai/gpt-6-luna **dump**. openai/gpt-6-luna: Only input/output data literals are shown; the aggregation code is absent.
- `code_focus`, question 62 (49655697): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: Relevant snippets show saving and loading, but omit some surrounding context.
- `code_focus`, question 66 (49802367): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: The relevant context hints are shown, but the code is fragmentary and not runnable.
- `code_focus`, question 67 (51305452): reviewed **partial**, openai/gpt-6-luna **focused**. openai/gpt-6-luna: The short radio-button and controller snippets provide relevant context for the selection behavior.
- `code_focus`, question 69 (73414326): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: The relevant snippets are concise but incomplete.
- `code_focus`, question 72 (66404888): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: The snippets are relevant but omit the client setup and complete request code.
- `code_focus`, question 77 (69437052): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: Relevant Autocomplete and TextField code is shown, but the snippet depends on surrounding definitions.
- `code_focus`, question 80 (69925081): reviewed **focused**, openai/gpt-6-luna **partial**. openai/gpt-6-luna: Relevant class and listener snippets are fragmentary.
- `code_focus`, question 88 (50907776): reviewed **partial**, openai/gpt-6-luna **dump**. openai/gpt-6-luna: The snippet omits the chart structure needed to identify the complete bar.
- `code_focus`, question 90 (73012994): reviewed **partial**, openai/gpt-6-luna **focused**. openai/gpt-6-luna: The short HTML and JavaScript snippets are centered on the table and click behavior.
- `code_focus`, question 93 (71675281): reviewed **focused**, openai/gpt-6-luna **dump**. openai/gpt-6-luna: The code assigns polygon attributes to patches but omits the patch-fitting operation being asked about.
- `code_focus`, question 96 (69483166): reviewed **focused**, openai/gpt-6-luna **dump**. openai/gpt-6-luna: The code omits the window-flag handling central to one of the problems.
- `environment_dependent`, question 2 (59720878): reviewed **no**, openai/gpt-6-luna **yes**. openai/gpt-6-luna: The stated conflict involves the asker's gts configuration forbidding default exports.
- `environment_dependent`, question 8 (61074096): reviewed **no**, openai/gpt-6-luna **yes**. openai/gpt-6-luna: The question concerns archiving a production RDS database.
- `environment_dependent`, question 17 (48844194): reviewed **no**, openai/gpt-6-luna **yes**. openai/gpt-6-luna: The question concerns highlighting configuration in PyCharm.
- `environment_dependent`, question 43 (54324062): reviewed **no**, openai/gpt-6-luna **yes**. openai/gpt-6-luna: The problem concerns configuring Python plotting within the asker’s R Markdown-to-PDF workflow.
- `environment_dependent`, question 55 (49399160): reviewed **no**, openai/gpt-6-luna **yes**. openai/gpt-6-luna: The request concerns scheduling recurring execution in a server setup.
- `environment_dependent`, question 66 (49802367): reviewed **no**, openai/gpt-6-luna **yes**. openai/gpt-6-luna: The post identifies macOS High Sierra and includes OS-specific setup details.
- `environment_dependent`, question 98 (57437460): reviewed **no**, openai/gpt-6-luna **yes**. openai/gpt-6-luna: The post names an Orbeon version and concerns forms in the asker’s setup.
- `image_only_evidence`, question 17 (48844194): reviewed **yes**, openai/gpt-6-luna **no**. openai/gpt-6-luna: The image illustrates the highlighting issue; no essential error, data, or code is image-only.
- `image_only_evidence`, question 85 (64698368): reviewed **yes**, openai/gpt-6-luna **no**. openai/gpt-6-luna: The URL, headers, and “not found” result are stated in text.

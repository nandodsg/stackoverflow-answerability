# Agreement: reviewed vs claude-haiku-5-5, scoring set

100 questions labeled by both; rubric version(s) fd79297623f7 (earlier levels mapped to the current ones).

| Label | Agree | Kappa | reviewed levels | claude-haiku-5-5 levels |
|---|---|---|---|---|
| `worked_example` | 99/100 | 0.94 | no 91, yes 9 | no 92, yes 8 |
| `ask_scope` | 92/100 | 0.61 | narrow 91, broad 5, multiple 3, no_clear_ask 1 | narrow 87, broad 5, multiple 7, no_clear_ask 1 |
| `failure_description` | 82/100 | 0.67 | concrete 64, vague 6, not_applicable 30 | concrete 60, vague 18, not_applicable 22 |
| `code_focus` | 83/100 | 0.73 | focused 57, partial 13, dump 2, not_applicable 28 | focused 48, partial 21, dump 3, not_applicable 28 |
| `environment_dependent` | 93/100 | 0.78 | no 83, yes 17 | no 78, yes 22 |
| `image_only_evidence` | 90/100 | 0.40 | no 94, yes 6 | no 88, yes 12 |

## Disagreements

- `worked_example`, question 11 (55411003): reviewed **yes**, claude-haiku-5-5 **no**. claude-haiku-5-5: Desired SQL is given as a query shape, with no concrete input data and output values.
- `ask_scope`, question 34 (71019316): reviewed **no_clear_ask**, claude-haiku-5-5 **narrow**. claude-haiku-5-5: Single question: where an error might be in the code, answerable with a short fix or pointer.
- `ask_scope`, question 45 (53599655): reviewed **narrow**, claude-haiku-5-5 **multiple**. claude-haiku-5-5: Main ask is a safe copy to a path; the race-condition question is a separate ask needing its own answer.
- `ask_scope`, question 52 (71305015): reviewed **narrow**, claude-haiku-5-5 **no_clear_ask**. claude-haiku-5-5: Body has only code and filler ('struggling', 'If you can help!'); the goal lives only in the title.
- `ask_scope`, question 55 (49399160): reviewed **broad**, claude-haiku-5-5 **narrow**. claude-haiku-5-5: Single ask: how to run the backup code monthly in code; a short answer could resolve it.
- `ask_scope`, question 65 (48504766): reviewed **narrow**, claude-haiku-5-5 **multiple**. claude-haiku-5-5: Asks how to configure the remote repo and separately whether Artifactory must be upgraded from 4.9.0.
- `ask_scope`, question 67 (51305452): reviewed **narrow**, claude-haiku-5-5 **broad**. claude-haiku-5-5: Asks whether to create a new view or use JS for a multi-part form feature, so it seeks an approach recommendation.
- `ask_scope`, question 71 (57530530): reviewed **narrow**, claude-haiku-5-5 **multiple**. claude-haiku-5-5: Asks why props show undefined, why the page reloads on submit, and how to re-send the API call.
- `ask_scope`, question 80 (69925081): reviewed **narrow**, claude-haiku-5-5 **multiple**. claude-haiku-5-5: Asks how to wire the reset button and also how to drive start, checkbox and slider from GridView.
- `failure_description`, question 7 (55104952): reviewed **not_applicable**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Says it couldn't figure it out after trying '$@' and '$<'; no observable symptom given.
- `failure_description`, question 14 (62255052): reviewed **concrete**, claude-haiku-5-5 **not_applicable**. claude-haiku-5-5: No failure reported; it is a how-to about getting computed colours.
- `failure_description`, question 17 (48844194): reviewed **not_applicable**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Implies bad highlighting but names no symptom in text; only the image shows it.
- `failure_description`, question 25 (68297160): reviewed **vague**, claude-haiku-5-5 **concrete**. claude-haiku-5-5: Says the frame works for ax0 but not ax1, a specific observable symptom.
- `failure_description`, question 26 (60344916): reviewed **not_applicable**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Only says 'not getting anywere' with no observable symptom or output.
- `failure_description`, question 28 (59922861): reviewed **concrete**, claude-haiku-5-5 **not_applicable**. claude-haiku-5-5: Describes a setting that does not take effect, but no error or failure is reported as such; it is a how-to on configuration.
- `failure_description`, question 31 (55219369): reviewed **vague**, claude-haiku-5-5 **concrete**. claude-haiku-5-5: Says editing the hinterland.yaml file had no effect, a named attempt with observable result.
- `failure_description`, question 34 (71019316): reviewed **not_applicable**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Only says there may be an error; no symptom, wrong output or error text is given.
- `failure_description`, question 35 (66285712): reviewed **concrete**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Symptom is only 'doesn't do anything' / 'doesn't print anything', with no error text or observed wrong value.
- `failure_description`, question 52 (71305015): reviewed **not_applicable**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Only 'I am struggling' with no error text, wrong output or symptom described.
- `failure_description`, question 54 (52372892): reviewed **concrete**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Failure is only described as plugins not working and values changing, without an exact symptom or error.
- `failure_description`, question 57 (67703011): reviewed **not_applicable**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Flicker and double rendering mentioned, but no concrete error or observed output is named.
- `failure_description`, question 65 (48504766): reviewed **concrete**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Only says the project 'doesn't seem to be finding it'; no error text or observable output given.
- `failure_description`, question 68 (70191431): reviewed **not_applicable**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Says only 'tried many things', no observable symptom of the failure is named.
- `failure_description`, question 80 (69925081): reviewed **not_applicable**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Only says it cannot find a way to access the listener; no error or symptom named.
- `failure_description`, question 88 (50907776): reviewed **concrete**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Says only 'not highlighting complete bar' with no exact symptom described in text.
- `failure_description`, question 90 (73012994): reviewed **not_applicable**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Only 'having trouble getting information' with no concrete symptom or error text.
- `failure_description`, question 99 (73288048): reviewed **not_applicable**, claude-haiku-5-5 **vague**. claude-haiku-5-5: Errors are only shown in an image; text says just that a 500 screen appears, no symptom named.
- `code_focus`, question 2 (59720878): reviewed **partial**, claude-haiku-5-5 **dump**. claude-haiku-5-5: Whole page component with large unrelated antd markup, plus package.json and tsconfig pasted.
- `code_focus`, question 9 (66295771): reviewed **focused**, claude-haiku-5-5 **partial**. claude-haiku-5-5: Includes the full loadCities function plus a short click handler; relevant but longer than needed.
- `code_focus`, question 10 (73760417): reviewed **partial**, claude-haiku-5-5 **dump**. claude-haiku-5-5: Whole Razor page pasted, with large unrelated form markup alongside the controller and model.
- `code_focus`, question 35 (66285712): reviewed **focused**, claude-haiku-5-5 **partial**. claude-haiku-5-5: Whole program is pasted; the relevant function and call are there, but a duplicate commented block and setup code add bulk.
- `code_focus`, question 42 (59328317): reviewed **not_applicable**, claude-haiku-5-5 **focused**. claude-haiku-5-5: One relevant logging line, self-contained and directly on the problem.
- `code_focus`, question 43 (54324062): reviewed **focused**, claude-haiku-5-5 **partial**. claude-haiku-5-5: Relevant plotting lines plus unrelated chdir and dataset loading; long but mostly on point.
- `code_focus`, question 55 (49399160): reviewed **focused**, claude-haiku-5-5 **partial**. claude-haiku-5-5: Backup code is relevant, but the button markup and folder check are not needed for the scheduling question.
- `code_focus`, question 62 (49655697): reviewed **focused**, claude-haiku-5-5 **partial**. claude-haiku-5-5: Two short components with some unneeded parts; relevant but slightly fragmentary.
- `code_focus`, question 65 (48504766): reviewed **focused**, claude-haiku-5-5 **not_applicable**. claude-haiku-5-5: The post contains no code block or pasted code, only repository settings.
- `code_focus`, question 68 (70191431): reviewed **focused**, claude-haiku-5-5 **partial**. claude-haiku-5-5: Whole script plus a large HTML markup block; the relevant click handler is only partly the problem.
- `code_focus`, question 72 (66404888): reviewed **focused**, claude-haiku-5-5 **partial**. claude-haiku-5-5: Relevant request code and XML, but includes a working example unrelated to the failure.
- `code_focus`, question 77 (69437052): reviewed **focused**, claude-haiku-5-5 **partial**. claude-haiku-5-5: One relevant component block, but includes unrelated props and is not runnable on its own.
- `code_focus`, question 81 (55283908): reviewed **dump**, claude-haiku-5-5 **focused**. claude-haiku-5-5: Only a short list of AT init commands pasted; no app code, which is relevant but not a full dump.
- `code_focus`, question 88 (50907776): reviewed **partial**, claude-haiku-5-5 **focused**. claude-haiku-5-5: Short click handler snippet containing the relevant highlighting logic, with minimal unrelated code.
- `code_focus`, question 92 (73623911): reviewed **focused**, claude-haiku-5-5 **partial**. claude-haiku-5-5: Full small files pasted; the relevant dropEvent is one function among boilerplate.
- `code_focus`, question 93 (71675281): reviewed **focused**, claude-haiku-5-5 **partial**. claude-haiku-5-5: Moderate-length code that is relevant to attributes, but the square-patch problem lives outside it.
- `code_focus`, question 96 (69483166): reviewed **focused**, claude-haiku-5-5 **partial**. claude-haiku-5-5: Short relevant snippets, but header and menu code are unrelated and flag handling is absent.
- `environment_dependent`, question 17 (48844194): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: Asks about configuring the asker's own PyCharm IDE setup for highlighting.
- `environment_dependent`, question 43 (54324062): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: Problem hinges on the asker's R Markdown, reticulate and Windows display setup.
- `environment_dependent`, question 55 (49399160): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: Monthly scheduling depends on how the asker's server and app are deployed and run.
- `environment_dependent`, question 66 (49802367): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: Problem hinges on macOS High Sierra, OS version and an ATI driver's OpenGL version.
- `environment_dependent`, question 81 (55283908): reviewed **yes**, claude-haiku-5-5 **no**. claude-haiku-5-5: Problem is about how the app handles data received from the dongle, reproducible from the post.
- `environment_dependent`, question 97 (59947919): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: Problem hinges on how the asker integrates files into their own component and project setup.
- `environment_dependent`, question 98 (57437460): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: Mentions a specific Orbeon version and asks about database rows in their own deployment.
- `image_only_evidence`, question 14 (62255052): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: Before and after states are shown only in linked images, not described in text.
- `image_only_evidence`, question 25 (68297160): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: Says 'See picture' and the image shows the frame result, but text gives the symptom.
- `image_only_evidence`, question 36 (64429852): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: Desired and current select appearance is shown only in linked screenshots, not described in text.
- `image_only_evidence`, question 46 (69706877): reviewed **yes**, claude-haiku-5-5 **no**. claude-haiku-5-5: Text fully describes the wanted single-column result and the suffix output; images only illustrate.
- `image_only_evidence`, question 62 (49655697): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: Console output the question relies on is only shown in an image, not in text.
- `image_only_evidence`, question 73 (59907596): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: The update queries that show the problem appear only in an image, not in text.
- `image_only_evidence`, question 85 (64698368): reviewed **yes**, claude-haiku-5-5 **no**. claude-haiku-5-5: The text states the error as 'not found', so the screenshot is only illustrative.
- `image_only_evidence`, question 88 (50907776): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: Key visual of the bar highlight problem is only in the linked image, not described in text.
- `image_only_evidence`, question 94 (53406755): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: The desired two-color appearance is shown only in the linked image, not described in text.
- `image_only_evidence`, question 99 (73288048): reviewed **no**, claude-haiku-5-5 **yes**. claude-haiku-5-5: The actual error details are only in the linked screenshot, not written out in the text.

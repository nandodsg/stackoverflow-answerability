# Candidate quality labels (discovery pass, not yet curated)

Model claude-opus-5-5; guess accuracy 144 of 200 right (72%), by confidence {'high': '15 of 16 right (94%)', 'low': '55 of 89 right (62%)', 'medium': '74 of 95 right (78%)'}.

## Summary

Text alone separates the outcomes moderately. The blind reader reached 72% overall, but only 16 pairs were high-confidence (94%), and the 89 low-confidence pairs were barely above chance (62%), so most pairs are not clearly distinguishable from writing. Many of the reader's correct calls rested on topic judgments (common bug vs niche stack, environment vs pure logic) that the rubric excludes, so expect the writing labels to explain less than 72%. The most consistent writing signals are:
- a literal worked example of the desired output;
- a single narrow ask;
- avoiding vague failure reports;
- focused code;
- not depending on the asker's local environment.
The misses show the reader overrated effort, research links, polish, structure and visible-but-expert-only bugs; the analyst should not reward those. Cautions:
- The worked-example label clusters in data-manipulation tags.
- The code labels apply only to code=true pairs.
- The failure label is N/A for how-to posts.
- Environment dependence leans toward ops tags.
- Several labels rest on 6-12 pairs.
- All counts are approximate, taken from one reader's free-form notes.

## Candidates

### 1. Worked example of the desired result

The post gives concrete sample input (data, string, array, table, file lines) together with the exact output the asker wants, written out literally in text or code, not just described in words.

- Levels: yes / no
- Decision rule: Yes only if (a) at least one concrete input appears in text and (b) the literal desired output for that input is written out, such as a table, array, string or numbers. Output described only in words (for example 'grouped by user') = no. Input or output shown only in a screenshot = no. Expected-versus-actual for a bug counts only if the expected value is written literally.
- Borderline case: Input is described in prose but the target output is written literally, or vice versa. Resolve as yes only if a reader could type both the input and the expected output from the post without guessing; otherwise no.
- Support: 21 pairs showed it, 20 favoring the accepted question
- Example pairs: 2018-03, 2019-50, 2021-13, 2018-32, 2020-12
- Rule-based neighbour: has code block; body length
- Concerns: Strongest signal, but concentrated in data-manipulation tags (r, excel, python/pandas, sql, php arrays, string). The reader missed 2018-32 and 2020-12 because the bare worked example looked low-effort; the example mattered more than effort. It partly co-occurs with simple tasks, so some of its effect may be topic.

### 2. Single narrowly scoped ask

Whether the post asks one specific question that has a definite answer, rather than one broad open-ended question (design, strategy, a whole feature) or several separate questions.

- Levels: narrow: one specific question with a definite answer / broad: one question, but open-ended (design, approach, whole feature, 'any suggestions') / multiple: two or more distinct questions, or a sprawling list of concerns
- Decision rule: Count the distinct things the asker wants answered. Follow-ups that the main answer would also settle count as one. Narrow = a single ask where a short answer (a function, setting, fix or fact) could fully resolve it. Broad = a single ask that needs a design discussion or building a whole feature. Multiple = two or more independent asks.
- Borderline case: A main question plus a side question ('also, is this good practice?'). Rate narrow if the side question is minor and clearly secondary; rate multiple if it would need its own answer of similar length.
- Support: 28 pairs showed it, 22 favoring the accepted question
- Example pairs: 2018-30, 2019-27, 2020-48, 2018-48, 2020-39
- Rule-based neighbour: body length; count of question marks
- Concerns: About 5 misses where the broad or multi-question post was accepted (2018-48, 2019-08, 2020-32, 2020-39, 2021-50). Keep this separate from the recommendation label: this one is about breadth, that one about asking for opinions or tools.

### 3. Concrete failure description

For posts reporting that something does not work: whether the failure is stated concretely, through the exact error text in text form or a precise observed-versus-expected behavior, or only vaguely.

- Levels: specific: exact error text or a precise observed vs expected behavior / partial: some concrete symptom, but neither an exact error nor a clear expected behavior / vague: 'doesn't work', 'crashes', 'nothing shows', 'not a proper response', with no further detail
- Decision rule: Apply only when the post reports a malfunction; mark N/A for pure how-to or conceptual questions. Specific requires a quoted error message or a sentence naming what happens and what should happen instead, such as 'undefined on first click, works on second'. Paraphrased errors ('says something about quota') count as partial.
- Borderline case: The error is quoted, but the post never says what the code should do. Rate specific, since the error alone is concrete. Rate partial only if the error is paraphrased.
- Support: 20 pairs showed it, 15 favoring the accepted question
- Example pairs: 2018-43, 2019-29, 2020-46, 2021-41, 2018-04
- Rule-based neighbour: error keywords
- Concerns: Merely containing an error message was mixed: about 34 pairs, roughly 20 favoring accepted. The value lies in avoiding vagueness, not in having error text. Many posts will be N/A, which shrinks the usable sample.

### 4. Code focused on the problem

For posts with code: whether the code is limited to what is needed to show the problem (short, relevant, ideally runnable or with a live demo) or is a dump of whole files or pages, unrelated code, huge data literals, or disconnected fragments.

- Levels: focused: short, only relevant parts, self-contained or runnable / partial: relevant but long, or slightly fragmentary / dump: whole app, file or page, unrelated sections, giant literals, or fragments missing the pieces the question is about
- Decision rule: Judge relevance, not raw length. Ask whether most of the code bears on the stated problem. Dump if a large share is unrelated (whole CSS, full manifest, generated HTML, big data arrays) or if the explanation is buried after a large paste. Focused if a non-expert can see where the problem lives.
- Borderline case: A long but complete runnable script where everything is used. Rate partial, not dump, unless large parts are clearly unrelated to the question.
- Support: 27 pairs showed it, 19 favoring the accepted question
- Example pairs: 2018-13, 2019-49, 2021-47, 2019-01, 2020-17
- Rule-based neighbour: has code block; number of code blocks; body length
- Concerns: Applies only to code=true pairs. About 8 counter-cases where the focused snippet went unanswered (2018-04, 2018-28, 2019-20, 2020-09, 2021-19). Overlaps the code-readability label; rate relevance here and formatting there.

### 5. Depends on the asker's local environment

Whether solving the problem as written depends on the asker's own installation, deployment, network, hosting, hardware, cluster or vendor attachment, rather than being something any reader could reproduce or reason about from the post.

- Levels: yes (environment-dependent) / no
- Decision rule: Yes if the described failure involves the local machine or infrastructure state (install or package errors, deployment, firewall or network, shared hosting, cluster caches, emulator setup, attached files not shown) and the post offers no way to reproduce it elsewhere. No if a reader could paste the posted material into a fresh setup, or answer from general knowledge.
- Borderline case: A build or config error that quotes a complete minimal config file. Rate no if the config alone reproduces the error; rate yes if the error depends on what is installed on the asker's machine.
- Support: 18 pairs showed it, 14 favoring the accepted question
- Example pairs: 2021-31, 2021-34, 2020-11, 2021-15, 2021-08
- Rule-based neighbour: none directly; loosely error keywords
- Concerns: Borders on topic: environment-troubleshooting tags such as docker, linux and devops will score yes often. A broader 'self-contained' idea (all code shown) was mixed and is not this label. Yes means the unanswered outcome is more likely.

### 6. Explicit ask stated in the body

Whether the body contains a clear sentence stating what the asker wants (a question or goal), as opposed to a bare dump of a log, stack trace or error, or an ask that lives only in the title.

- Levels: yes / no
- Decision rule: Yes if the body has at least one sentence a reader can point to as the request ('how do I…', 'I want X to…', 'why does…'). No if the body is only pasted output, code or an error with at most a filler line like 'getting this error'.
- Borderline case: The body is mostly a stack trace plus 'any help?'. Rate no, because 'any help' does not specify what outcome is wanted.
- Support: 10 pairs showed it, 8 favoring the accepted question
- Example pairs: 2020-19, 2021-13, 2021-23, 2018-06, 2018-01
- Rule-based neighbour: body length; question marks; greetings/thanks
- Concerns: Small sample. Most posts will be yes, so the label mainly flags a low-quality tail. A bolded or highlighted question did not help in 2018-01.

### 7. Essential evidence only in an image

Whether information needed to answer (the error text, the data, or the code) appears only in a screenshot and not as text.

- Levels: yes / no
- Decision rule: Yes if the error, the sample data or the code that the question hinges on is visible only in an image. Mockups of desired UI, illustrative screenshots of the symptom, or images that duplicate text already in the post = no.
- Borderline case: A screenshot of a layout bug alongside the HTML/CSS in text. Rate no, because the essential code is in text and the image only illustrates.
- Support: 10 pairs showed it, 8 favoring the accepted question
- Example pairs: 2018-10, 2019-09, 2021-42, 2020-25, 2019-22
- Rule-based neighbour: has image
- Concerns: Having an image at all was neutral across many pairs. This label only adds value if the analyst checks whether the image replaces text. The sample is small.

### 8. Code readable as posted

For posts with code: whether the code is legibly presented (inside code formatting, sensibly indented, syntactically intact, no placeholder or garbage text) rather than broken or mangled.

- Levels: yes / no
- Decision rule: No if any substantial code is pasted as plain prose, code fences are broken so code and text run together, indentation is chaotic, or the code is visibly malformed (mismatched names, unclosed structures noted by the asker, leftover placeholders). Otherwise yes.
- Borderline case: Code inside a block but with inconsistent indentation only. Rate yes unless the indentation makes the structure unreadable.
- Support: 12 pairs showed it, 9 favoring the accepted question
- Example pairs: 2019-11, 2020-24, 2021-25, 2019-26, 2019-40
- Rule-based neighbour: has code block; inline code
- Concerns: This refines 'has code block', but some of it is mechanical and may be partly captured by rule features. Overlaps the focus label. Counter-cases (2018-15, 2019-26, 2019-40) show that broken formatting does not doom a question.

### 9. Recommendation or opinion framing

Whether the ask is framed as a request for the best or better way, a tool, library or tutorial recommendation, examples, or a judgment on whether a design is good, rather than a factual or how-to question.

- Levels: yes / no
- Decision rule: Yes if the core ask uses framing such as best or better way, recommend or suggest a tool or library, 'anyone have an example', 'is this good practice or design', or 'do you think it is reliable'. A how-to that merely mentions 'best' in passing while asking for a specific operation = no.
- Borderline case: 'Is there a better way to do this?' about working code. Rate yes if no concrete deficiency is named; rate no if a specific problem (slow, wrong output) is stated.
- Support: 16 pairs showed it, 10 favoring the accepted question
- Example pairs: 2018-07, 2018-30, 2019-02, 2021-06, 2020-37
- Rule-based neighbour: none (effort phrases are distinct)
- Concerns: Weakest of the kept labels, at about 60-65%. Several confident misses (2021-06, 2020-37, 2019-38, 2021-49) show the reader overrated it. Keep it only if it adds signal beyond the scope label.

### 10. Asker-imposed restriction on fixes

Whether the asker rules out the usual solutions without a technical reason, such as refusing to upgrade, refusing classes or other approaches, insisting on keeping a specific tool, or demanding their own code be fixed as-is.

- Levels: yes / no
- Decision rule: Yes if the post explicitly excludes common remedies by preference or inability ('I don't want to update', 'don't suggest classes', 'must keep using X') and that exclusion is central to the ask. Constraints explained by a requirement (data size, a must-hold invariant, an existing schema) = no.
- Borderline case: A stated business or platform constraint, such as 'cannot merge the networks'. Rate no when a reason is given and alternatives remain; rate yes only when it reads as an arbitrary refusal.
- Support: 6 pairs showed it, 5 favoring the accepted question
- Example pairs: 2020-20, 2021-22, 2019-36, 2019-16, 2018-36
- Rule-based neighbour: none
- Concerns: Very small sample, so the counts are approximate. Accepted posts often stated legitimate constraints (2018-28, 2018-36), so the arbitrary-versus-justified distinction must be applied carefully or the label will be noisy.

## Rejected ideas

- **Clarity and polish of prose (grammar, fluency, typos)**: Mixed: about 16 pairs, roughly half favoring accepted. Confident misses include 2018-35 (non-English one-liner accepted, high confidence), 2020-28, 2020-41 and 2019-46. The reader overrated polish.
- **Effort or prior attempts described**: Mixed to negative: in many pairs the post describing attempts or reasoning went unanswered (2018-01, 2018-16, 2018-26, 2018-34, 2019-13, 2019-37, 2020-03). Effort phrases are also already rule-based.
- **Research shown (docs or related questions linked)**: Favored the unanswered side more often than not (2018-14, 2018-18, 2019-38, 2020-09, 2020-37, 2020-47, 2021-06). It also overlaps the links feature.
- **Exact error message quoted (on its own)**: Only about 60% favorable across roughly 34 pairs, and close to the error-keywords rule feature. The useful part is folded into 'Concrete failure description'.
- **Complete or self-contained context (all relevant code shown)**: Mixed: several misses where the more complete post went unanswered (2018-29, 2019-21, 2019-25, 2020-35, 2018-27). Only the environment-dependence part held up, and it is kept separately.
- **Working vs failing contrast**: About 10 pairs, roughly 6 favoring accepted, with a confident miss in 2018-04. Too weak, and partly covered by the concrete failure description.
- **Headed or numbered structure**: Mixed: helped in 2018-02 and 2020-08 but misled in 2020-26, 2019-46 and 2021-06.
- **Tone (pleading, frustrated, complaining, curt)**: Mixed in the few pairs where it appeared (2018-11, 2018-15 and 2018-46 accepted despite poor tone).
- **Bug visible in the posted code**: Needs tag expertise to judge, and was the reader's most frequent source of wrong guesses (2018-06, 2018-41, 2019-25, 2019-40, 2020-10, 2021-04, 2021-12, 2020-26).
- **Niche technology vs common pattern; problem difficulty**: Topic and difficulty, not writing. Heavily used in the reader's rationales but excluded by the rubric's scope.
- **Duplicate-prone question**: Topic in disguise, and depends on knowledge of the site's existing content and on what happens after posting.
- **Request possibly impossible or unsupported**: Requires domain expertise to judge, so it is not judgeable from text by a non-expert.
- **Clear, specific title**: Only about 4 pairs, all favorable but too few. It overlaps prose clarity and the explicit-ask label.
- **Code request with no attempt ('write it for me')**: Mixed: bare code requests were accepted in 2018-16 and 2020-12 and lost in 2019-42.
- **Images, live demo links, beginner self-disclosure**: Images, live demo links and beginner self-disclosure looked neutral across pairs, and the first two are already rule-based. Only the image-only-evidence refinement is kept.

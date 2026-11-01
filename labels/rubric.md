# Quality-label rubric (P3)

Six judgments about how a Stack Overflow question is written, made from its **original title and body** (the
Markdown the asker first posted, before any edit). The same text and the same definitions are used by the hand
labeler (the gold set) and by every labeling model, so their labels can be compared. This file is the single source
of the definitions: the labeling prompt reads it as is.

Curated from the ten candidates of the discovery pass (`labels/output/discovery/candidate_labels.md`); what was kept,
merged or dropped, and why, is at the end.

## How to judge

- **Writing, not topic.** Judge how the question is written, never what it is about. Do not ask whether the
  technology is niche, the problem is hard, or the question is likely a duplicate.
- **Text only.** Judge only what the text shows. Images are not visible: a link to an image counts as "an image", and
  you do not know what it shows beyond what the text says about it.
- **No expertise needed.** Judge from what the post says, not from what you know about the tool, its versions or its
  libraries. Do not judge whether the code has a bug, whether the request is possible, or whether the approach is
  right. A reader with no knowledge of the tag should reach the same answer.
- **Each label on its own.** One label's answer never decides another's.
- **Do not reward** length, effort described, research links, polished English, headings or tone: they are not what
  these labels measure.
- **Always pick a level.** When unsure, apply the label's borderline rule; there is no "can't tell".

## The labels

Each label has a storage key, its levels (the first is the **reference level**, against which the other levels'
rates are compared in the analysis), a decision rule and the borderline cases. `not_applicable` levels are left out
of that label's comparison.

### 1. `worked_example` — input and desired output written out

Levels: `no` (reference) / `yes`

- **yes** only if both are written out in text or code: (a) at least one concrete input (data, a value, a string, an
  array, a table, file lines) and (b) the literal output the asker wants for that input (a table, an array, a string,
  a value). One value is enough: "`-$97.90` should become `($97.90)`" is **yes**.
- **no** if the desired output is only described in words ("grouped by user", "make it thinner"), if the input or
  output is only in an image, or if either is missing.
- Runnable code, an error message, a list of patterns or a description of the goal is not a worked example by
  itself. This label asks for an input/output pair, not for a reproducible example.
- A bug report's expected-versus-actual counts only if the expected value is written literally.
- *Borderline:* input written but the output left for the reader to infer (an example sentence, but the word to
  extract from it never written): **no**. **yes** only if a reader could type both the input and the expected output
  from the post without guessing.

### 2. `ask_scope` — what is being asked

Levels: `narrow` (reference) / `broad` / `multiple` / `no_clear_ask`

Decide in this order and stop at the first that fits:

1. **no_clear_ask**: the body states neither the problem nor the goal in its own words. It is only pasted code,
   output, a log or an error, with at most a filler line ("not working", "getting this error", "any help?"), and
   the request lives only in the title.
2. **multiple**: two or more independent things to answer, or a sprawling list of concerns. Follow-ups that the main
   answer would settle anyway count as one (the same fix asked for two elements is one ask).
3. **broad**: a single ask that needs a design discussion or a whole feature, app or system built ("how should I
   structure…", "how do I build a…"), **or** an ask framed as a request for an opinion or a recommendation: the best
   or a better way, a tool, library or tutorial to use, "anyone have an example", "is this good practice", "do you
   think this is reliable".
4. **narrow**: one specific question that a short answer (a function, a setting, a fix, a fact, a paragraph of
   explanation) could fully resolve.

- A problem described in prose followed by "any help?" asks for a fix of that problem: judge its scope like any other
  ask. "The result should be like this", with the result written out, is a stated ask.
- A conceptual "why does X…" or "what is X" question that a paragraph answers is **narrow**.
- A request to write one function or algorithm for a stated operation, even a non-trivial one, is **narrow**; broad
  is for designing a system or building a feature with several parts.
- *Borderline:* a main question plus a side question ("also, is this good practice?", "suggestions welcome"):
  **narrow** if the side question is minor and clearly secondary; **multiple** if it would need its own answer of
  similar length.
- *Borderline:* "is there a better way to do this?" about working code: **broad** if no concrete deficiency is
  named; **narrow** if a specific problem is stated (too slow, wrong output). A how-to that only mentions "best" in
  passing while asking for a specific operation is **narrow**.

### 3. `failure_description` — how the failure is described

Levels: `concrete` (reference) / `vague` / `not_applicable`

Decide in this order:

1. **not_applicable** if the post does not report something going wrong: a how-to, conceptual or design question
   with no attempt that failed. A constraint ("eval is disabled on my server") is not a failure. A how-to that shows
   an attempt and says what it did ("it is very thick", "it only replaces the first one") does report a failure.
2. **concrete**: the failure is named in observable terms: the exact error text, a wrong value or output, or a
   described symptom ("stops after item 2 and never runs 3 and 4", "never updates the jti", "shows too many
   decimals", "does not cover the app bar"). An expected behaviour is welcome but not required.
3. **vague**: the only description is a phrase like "doesn't work", "not working", "is not supporting", "crashes",
   "an error", "nothing shows", "not a proper response", with no symptom.

- *Borderline:* a paraphrased error that still names the problem ("says something about quota") is **concrete**. An
  error shown only in an image, with no text describing it, is **vague**.

### 4. `code_focus` — code focused on the problem

Levels: `focused` (reference) / `partial` / `dump` / `not_applicable`

- **not_applicable** if the post has no code: no code block and no pasted code of two lines or more. Code includes
  source, queries, markup, config files and data literals. Logs, debug traces and error output are not code: a post
  whose only blocks are logs is **not_applicable**.
- Judge relevance, not raw length: does most of the code bear on the stated problem?
- **focused**: short, only the relevant parts, self-contained or runnable; a non-expert can see where the problem
  lives.
- **partial**: relevant but long, or slightly fragmentary; a whole config file or component where the problem sits
  in one line or one import and the rest is related but not needed.
- **dump**: a whole app, file or page; large unrelated sections (a full stylesheet, a whole manifest, generated
  HTML, big data arrays); the question buried after a large paste; or fragments missing the very pieces the question
  is about.
- *Borderline:* a long but complete runnable script where everything is used: **partial**, not dump, unless large
  parts are clearly unrelated to the question.

### 5. `environment_dependent` — about the asker's own setup

Levels: `no` (reference) / `yes`

- **yes** if the problem, as the post describes it, is about the asker's own setup: installing, upgrading or
  versioning software; configuring or deploying (servers, containers, hosting, cloud services, build tools); networks
  and firewalls; a specific OS, machine or device; or files and attachments the post does not include and the
  problem hinges on.
- **no** if the problem is about code, a query or a behaviour that a reader could reproduce from the post or answer
  from general knowledge, even when the code happens to read a local file or talk to a server.
- Judge from what the post says: do not answer **yes** because you know a feature depends on a version, unless the
  post itself mentions installs, versions, upgrades or its setup.
- *Borderline:* a build or config error that quotes a complete, minimal config file: **no** if that config alone
  would reproduce the error; **yes** if the error depends on what is installed or deployed on the asker's side.

### 6. `image_only_evidence` — essential evidence only in an image

Levels: `no` (reference) / `yes`

- **yes** if the post points to an image for something the question hinges on and never gives it in text: the error
  ("I get this error:" followed by an image and no error text), the sample data, or the code.
- **no** if there is no image, or the images are mockups of a desired screen, illustrations of a visible symptom,
  diagrams the question is about, or repeat what the text already says.
- Test: cover the images. If you can still tell from the text what the error, the data or the code is, the answer is
  **no**.
- Image tags inside pasted code (an `<img>` element in HTML or JSX) are code, not images.
- *Borderline:* a screenshot of a layout bug next to the HTML and CSS in text: **no**; the essential code is in text
  and the image only illustrates.

## From the discovery candidates to this rubric

| Candidate (discovery pass) | Decision | Reason |
|---|---|---|
| 1 Worked example of the desired result | kept as `worked_example` | Strongest signal (20 of 21 pairs favored the accepted question). |
| 2 Single narrowly scoped ask | kept as `ask_scope` | 22 of 28; judgeable without tag knowledge. |
| 9 Recommendation or opinion framing | merged into `ask_scope` = `broad` | Weakest kept signal (10 of 16) and a kind of broad ask; merging adds no judgment per post. |
| 6 Explicit ask stated in the body | merged into `ask_scope` = `no_clear_ask` | Most posts have one, so alone it only flags a thin tail; as a level it costs nothing extra. |
| 3 Concrete failure description | kept as `failure_description` | 15 of 20; the value is in avoiding vagueness, not in quoting an error. |
| 4 Code focused on the problem | kept as `code_focus` | 19 of 27; splits the ~70% of questions with code, which the rules cannot split further. |
| 5 Depends on the asker's environment | kept as `environment_dependent` | 14 of 18 (here "yes" goes with the unanswered question). |
| 7 Essential evidence only in an image | kept as `image_only_evidence`, judged from text | 8 of 10; refines the rule-based has-image feature, which alone is neutral. Neither the hand labeler nor a model sees the images. |
| 8 Code readable as posted | dropped | Largely mechanical and close to the rule-based code features; overlaps `code_focus`. |
| 10 Asker-imposed restriction on fixes | dropped | 6 pairs only, and "arbitrary versus justified" is hard to judge consistently. |

Counts are approximate, taken from one model's free-form notes over 200 pairs; the gold set and the analysis set
measure each label properly. Labels 1 and 5 lean toward some tags (data manipulation; ops), which the analysis's
control by primary tag accounts for. Ideas the discovery pass rejected as mixed or reversed (effort shown, research
links, prose polish, structure, tone, a bare error quote) are listed in its candidates file.

**Practice round (2026-10-31).** The first wording (version 5102cea87d4f) was tried on the 20 practice questions by
the hand labeler and one model, blind to each other. Their disagreements showed where the wording left room, and it
was tightened before the scoring set: `worked_example` asks for an input/output pair, not a reproducible example;
`ask_scope` treats a problem described in prose, a written-out desired result and a conceptual question as clear,
narrow asks; `failure_description` merges "specific" and "partial" into `concrete`, since the discovery signal is
vague versus not vague; `code_focus` says logs are not code; `environment_dependent` is judged from what the post says
about its setup, not from knowledge of the tool; `image_only_evidence` gets the "cover the images" test. The outcome
hint in "Do not reward" was removed.

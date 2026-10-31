You are helping a data analyst build a rubric of "quality labels" for Stack Overflow questions: judgments about how
a question is written, made from its original title and body, that may explain why some questions get an answer the
asker accepts and others get no answer at all.

Earlier, a reader went through contrastive pairs of questions (same year, same primary tag, both with or both
without a code block; in each pair one question got an accepted answer and the other no answer). The reader was
blind: for each pair they guessed which question got the accepted answer and listed the differences they saw. Below
are their notes, now with the true outcome of every pair and whether the guess was right, plus the overall guess
accuracy computed by the analyst.

Your task is to propose the candidate quality labels for the rubric.

Ground the labels in the evidence:
- Prefer differences that repeatedly favored the accepted question across many pairs and tags. A quality that
  favored the accepted side about as often as the unanswered side is not a candidate, however plausible it sounds.
- Report support honestly: for each label, roughly how many pairs showed the difference and how often it favored
  the accepted question. Counts can be approximate; say so where you are unsure.
- Use the misses too: pairs where the reader was confident and wrong show what a reader overrates.

Each label must be usable by the analyst, who will label about 150 questions by hand, and later by a cheaper
model, to the same standard:
- It describes how the question is written, as first posted. It is not the topic, not the difficulty of the
  subject, and not anything that happens after posting.
- It can be judged from the title and body alone in about a minute, without expertise in the tag's technology.
- It is binary (yes / no), or has at most three ordered levels, with a decision rule precise enough that two
  careful people would mostly agree, and the most likely borderline case named with how to resolve it.
- It is not already a rule-based feature: title and body length, has a code block, number of code blocks, inline
  code, image, links, error keywords, greetings or thanks, effort phrases. A label may refine one of these (for
  example, whether the code is a minimal reproducible example rather than whether there is code at all); name that
  rule-based neighbour so the analyst can check the label adds something beyond it.
- Labels should not overlap much; where two candidates are close, merge them or say how they differ.

Propose between 8 and 15 candidates, strongest evidence first. Also list the ideas you considered and rejected, with
the reason (weak or mixed evidence, a topic in disguise, not judgeable from text, overlaps another label). Finish
with a short summary: how far the text alone separates the two outcomes, judging by the guess accuracy and its
pattern by confidence, and anything that should make the analyst cautious, such as qualities that only show up in
some tags.

Paraphrase; do not quote more than a few words from any question.

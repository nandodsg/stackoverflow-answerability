# Specs

One spec per prompt, written before the SQL. A spec fixes **definitions, grain, population, assumptions and acceptance
criteria**; the dbt models implement it and the tests prove it. When a number in the README changes, the spec says why.

| Spec | Prompt | Status |
|---|---|---|
| [000 — Shared definitions & data profile](000-shared-definitions.md) | all | draft |
| [001 — Tag answerability](001-q1-tag-answerability.md) | 1 | draft |
| [002 — python-only vs dbt-only, YoY](002-q2-python-vs-dbt.md) | 2 | draft |
| [003 — Non-tag post qualities](003-q3-post-qualities.md) | 3 | draft |

**Acceptance criteria** carry IDs (`AC-1.2`) so each one can be traced to the test or query that checks it.

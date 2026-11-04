# EDA — D5: the BigQuery budget

Supports the cost rules in [`specs/003`](../../specs/003-q3-post-qualities.md) (AC-3.2, AC-3.4) and the cost
guardrails in the [decisions log](../../PLAN.md#decisions-log). The project runs in BigQuery's free sandbox: 1 TB of
queries a month and 10 GB of storage. D4 needs the original text of every question, and one read of
`post_history.text` bills 106 GiB whatever the filter (BigQuery bills every column a query touches, in full, and the
table has no partition). This EDA reads BigQuery's own job log to check what the whole project actually billed.

## Run it

```bash
.venv/Scripts/python eda/d5_budget/run_eda.py              # add --refresh to requery BigQuery
```

Same setup as [`d1_sample_size`](../d1_sample_size/README.md). The query reads the job log, not the Stack Overflow
data: a metadata query, billed the 10 MB minimum, dry-run first and capped at 1 GB. It keeps the bytes billed, the time
and, for queries sent by dbt, the target and the model (dbt writes both into a comment in every query); it never keeps
the query text or the user. On a fresh clone it returns that clone's own jobs, not these.

| File | What |
|---|---|
| `sql/jobs.sql` | one row per query job since 2026-10-01: time, bytes billed, cache hit, dbt target and model, whether it read `post_history` or `posts_questions` |
| `run_eda.py` | runs the query (cached as `output/jobs.csv`), sorts each job into a kind of work, writes `output/summary.md` |

## What it found

1. **511 GiB billed in all, never more than 45% of a month.** 685 query jobs from 2026-10-29 to 2026-11-01: 460 GiB
   in October (45% of the free 1 TB, 1,024 GiB) and 50 GiB in November (5%); 114 jobs were served from cache and
   billed nothing ([per month][s-month]). The sandbox has no billing, so the bill was US$ 0; at the on-demand list
   price (US$ 6.25 per TiB) it would have been about US$ 3.
2. **Half of it is the one decision D4 made.** The full text reads are 247 GiB: `post_history.text` twice (105.96 GiB
   each) and `posts_questions.body` once (35.06 GiB) ([per kind][s-kind]).
3. **The expensive target was used three times.** Every full read ran on the `full_scan` target (120 GiB cap per
   query), 12 minutes apart on 2026-10-31; nothing else ever ran there. Before them, six 2% samples of the two models
   ran on the everyday `dev` target (20 GiB cap) for 8 GiB in all and found two rule bugs; the second
   `post_history.text` read came after a question-by-question comparison found three more ([every text read][s-text]).
4. **Everyday work is cheap.** The other 339 dbt queries billed 67 GiB together; the largest single one was 3.9 GiB
   (`int_question_exposure`). Everything not sent by dbt (the EDA scripts, the mart exports, the query checks) billed
   188 GiB over 337 jobs, none above 7.2 GiB ([largest jobs][s-largest]).
5. **The month boundary helped.** Inside a single month the same work would have used half the quota (511 of 1,024
   GiB): still under, with less room for a third full read.

**Since this read.** On 2026-11-04 the tag-pair mart was exported for the presentation (P1's combinations): one query,
0.6 MB processed, 10 MiB billed (BigQuery's minimum per query). The same day, the new unit test for AC-1.10 ran twice
(once as written, once with a wrong expected value to see it fail): four jobs, 0 bytes billed, since a unit test reads
only the rows written into it. No total above changes at the GiB they are reported in.

How the read was planned and guarded, including the rules for working with an AI coding agent:
[README, "Running on a free tier"][readme].

[s-month]: output/summary.md#per-month
[s-kind]: output/summary.md#per-month-and-kind-of-work
[s-text]: output/summary.md#every-run-of-the-two-text-read-models
[s-largest]: output/summary.md#the-15-largest-jobs
[readme]: ../../README.md#running-on-a-free-tier

# AGENTS.md

Instructions for an AI coding agent (or a person) working on this repo. What the project answers and why is in
[`README.md`](README.md); every decision and the evidence behind it is in [`PLAN.md`](PLAN.md#decisions-log).

## Setup

1. Python 3.12 and a virtual environment: `python -m venv .venv`, then
   `.venv/Scripts/pip install -r requirements.txt` (Windows) or `.venv/bin/pip install -r requirements.txt`.
2. BigQuery: `gcloud auth application-default login`. The free BigQuery sandbox is enough.
3. dbt profile: copy [`profiles.example.yml`](profiles.example.yml) to `~/.dbt/profiles.yml` and set `GCP_PROJECT` to
   your project id. Never commit a `profiles.yml`, a key file or `.env`.
4. `dbt deps`, then `dbt build`. How to test, step by step: [`TESTING.md`](TESTING.md#how-to-run).

## BigQuery cost rules

The public Stack Overflow tables are large, and two columns are expensive: `posts_questions.body` (36 GB) and
`post_history.text` (109 GB). BigQuery bills every column a query touches, in full, and these tables have no
partition, so a `WHERE` clause or a `LIMIT` does not make them cheaper. The sandbox allows 1 TB of queries a month.

- **Price a query before you run it.** Use a dry run (`bq query --dry_run`, or `dry_run=True` in the Python client):
  it is free and returns the bytes the query would bill. Every EDA script already does this and stops above 10 GB
  unless run with `--allow-gb N`; don't raise that limit without asking.
- **Never read `body` or `post_history.text` outside the two scan models**, `int_post_history_scan` and
  `int_question_body_scan`. They read the text once and store features, the original titles and tags, and a 5% text
  sample; build on those tables instead. The test `assert_text_columns_read_once` fails the build if any other model
  reads the source text tables.
- **Keep the default build.** `dbt build` skips the scan models (`selectors.yml`). Run them only when asked, on their
  own target: `dbt run --target full_scan --select tag:full_scan` (about 145 GB; each query capped at 120 GiB).
  Everything else runs on the `dev` target, capped at 20 GiB per query: BigQuery refuses a query over the cap before it
  reads anything. dbt has no dry run, so that cap is the guard; don't raise it.
- **Language-model calls have a budget too.** `labels/label_questions.py count` estimates the cost for free; a paid run
  needs `--max-usd` and stops starting calls at that amount. Ask before any paid run.

What the project billed in practice, and why the rules are shaped this way:
[README, "Running on a free tier"](README.md#running-on-a-free-tier).

## How work is done here

- **Spec first.** A change starts in [`specs/`](specs/): a definition, then acceptance criteria (AC-x.y). Each AC gets
  a test; [`TESTING.md`](TESTING.md) maps every AC to its test. A test that only flags rows for the README to discuss
  uses `severity: warn`.
- **Decisions go in the log.** A choice with more than one defensible answer gets a row in `PLAN.md`'s decisions log,
  with the evidence (usually an EDA in [`eda/`](eda/)).
- **dbt conventions.** Every model's first line says whether it is a table or a view and where that is set, e.g.
  `-- Materialized as a view: set for the staging folder in dbt_project.yml.` Folder defaults live in
  `dbt_project.yml`; only a model that differs gets an inline `config()`.
- **Generated files are not edited by hand**: `queries/*.sql` (from `queries/build_queries.py`), `eda/*/output/`
  (from each EDA script), `presentation/data/` (from `presentation/export_marts.py`) and `presentation/img/eda/` (from
  `presentation/eda_charts.py`, which reads only cached CSVs).
- **Numbers in the README come from the models.** `tests/semantic/check_semantic_layer.py` compares them with
  MetricFlow; change a number only after the model changes.

# Stack Overflow answerability

What makes a Stack Overflow question get answered, and get an accepted answer? Analysis of the
[`bigquery-public-data.stackoverflow`](https://console.cloud.google.com/marketplace/product/stack-exchange/stack-overflow)
dataset.

> Work in progress. Results land here first; method and limits follow each answer.

## Read this first

The public snapshot ends on **2022-09-25**. "Current year" in this analysis means **2022** (partial year). Details in
[`specs/000`](specs/000-shared-definitions.md).

## 1. Tags with the most and fewest answers and accepted answers

_TBD — spec: [`specs/001`](specs/001-q1-tag-answerability.md)_

## 2. python-only vs dbt-only, year over year

_TBD — spec: [`specs/002`](specs/002-q2-python-vs-dbt.md)_

## 3. Non-tag qualities that correlate with answers

_TBD — spec: [`specs/003`](specs/003-q3-post-qualities.md)_

## How this repo is organized

- `specs/` — definitions and acceptance criteria, written before the SQL
- `PLAN.md` — scope, schedule, decisions

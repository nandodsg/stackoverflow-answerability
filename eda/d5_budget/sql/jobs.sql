-- D5 EDA: what this project actually billed in BigQuery, one row per query job.
--
-- Reads BigQuery's own job log (INFORMATION_SCHEMA.JOBS_BY_PROJECT, US region), not the Stack Overflow data: a
-- metadata query that bills the 10 MB minimum. Leaves out the query text and the user, keeps what the cost story
-- needs: when, how many bytes billed, whether it came from dbt (dbt writes a JSON comment with the target and the
-- model into every query it sends), and which public tables it read.

select
    job_id,
    creation_time,
    statement_type,
    state,
    error_result.reason as error_reason,
    cache_hit,
    coalesce(total_bytes_processed, 0) as bytes_processed,
    coalesce(total_bytes_billed, 0) as bytes_billed,
    regexp_contains(query, r'"app": "dbt"') as from_dbt,
    regexp_extract(query, r'"target_name": "([^"]+)"') as dbt_target,
    regexp_extract(query, r'"node_id": "([^"]+)"') as dbt_node,
    exists (
        select 1 from unnest(referenced_tables) t
        where t.project_id = 'bigquery-public-data' and t.table_id = 'post_history'
    ) as reads_post_history,
    exists (
        select 1 from unnest(referenced_tables) t
        where t.project_id = 'bigquery-public-data' and t.table_id = 'posts_questions'
    ) as reads_posts_questions
from `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
where job_type = 'QUERY'
  and creation_time >= timestamp '2026-10-01'
order by creation_time

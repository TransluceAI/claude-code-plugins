# DQL (Docent Query Language) Reference

Docent Query Language is a read-only SQL subset that supports ad-hoc exploration in Docent.

Queries can only run over a single collection by design.

## Executing DQL

Choose the right method based on context:

* **`execute_dql` MCP tool** — Use for ad-hoc exploration and orientation (Step 1). Runs DQL directly without requiring user approval of inline scripts. Preferred for all exploratory queries.
* **`client.query()`** — Use inside reading plan scripts. Auto-registers the query as a UI-visible step. Use this for DQL that feeds data into readings, or that you want the user to see alongside reading results. Pass `name="..."` to give the step a display name.
* **`client.execute_dql()`** — Use inside Python scripts for internal logic (e.g., conditional logic between reading steps, or data that feeds into scripted readings). Results are NOT shown in the Docent UI.

```python
from docent.sdk.client import Docent

client = Docent()
collection_id = "<collection-uuid>"

# (Optional) inspect available tables/columns
schema = client.get_dql_schema(collection_id)

# In reading plan scripts: query as a UI-visible step
rows = client.query(
    collection_id,
    "SELECT agent_runs.id AS agent_run_id FROM agent_runs LIMIT 10",
    name="Recent runs",
)

# Inside scripts for internal logic: results not shown in UI
result = client.execute_dql(
    collection_id,
    "SELECT agent_runs.id AS agent_run_id FROM agent_runs LIMIT 10",
)
raw_rows = client.dql_result_to_dicts(result)
```

## Available Tables and Columns

| Table | Description |
| --- | --- |
| `agent_runs` | Information about each agent run in a collection. |
| `transcripts` | Individual transcripts tied to an agent run; stores serialized messages and per-transcript metadata. |
| `transcript_groups` | Hierarchical groupings of transcripts for runs. |
| `judge_results` | Scored rubric outputs keyed by agent run and rubric version. |
| `results` | Individual LLM analysis results from result sets. |
| `readings` | Reading definitions (template or scripted LLM analysis). |
| `reading_results` | Results from running readings. |
| `reading_result_links` | Junction table linking readings to their results. |
| `analysis_sessions` | Session containers grouping readings together. |

### `agent_runs`

| Column | Description |
| --- | --- |
| `id` | Agent run identifier (UUID). |
| `collection_id` | Collection that owns the run |
| `name` | Optional user-provided display name. |
| `description` | Optional description supplied at ingest time. |
| `metadata_json` | User supplied metadata, stored as JSON. |
| `created_at` | When the run was recorded in Docent. |

### `transcripts`

| Column | Description |
| --- | --- |
| `id` | Transcript identifier (UUID). |
| `collection_id` | Collection that owns the transcript. |
| `agent_run_id` | Parent run identifier; joins back to `agent_runs.id`. |
| `name` | Optional transcript title. |
| `description` | Optional description. |
| `transcript_group_id` | Optional grouping identifier. |
| `messages` | Binary-encoded JSON payload of message turns. |
| `metadata_json` | Binary-encoded metadata describing the transcript. |
| `created_at` | Timestamp recorded during ingest. |

### `transcript_groups`

| Column | Description |
| --- | --- |
| `id` | Transcript group identifier. |
| `collection_id` | Collection that owns the transcript. |
| `agent_run_id` | Parent run identifier; joins back to `agent_runs.id`. |
| `name` | Optional name for the group. |
| `description` | Optional descriptive text. |
| `parent_transcript_group_id` | Identifier of the parent group (for hierarchical groupings). |
| `metadata_json` | JSONB metadata payload for the group. |
| `created_at` | Timestamp recorded during ingest. |

### `judge_results`

| Column | Description |
| --- | --- |
| `id` | Judge result identifier. |
| `agent_run_id` | Run scored by the rubric. |
| `rubric_id` | Rubric identifier. |
| `rubric_version` | Version of the rubric used when scoring. |
| `output` | JSON representation of rubric outputs. |
| `result_metadata` | Optional JSON metadata attached to the result. |
| `result_type` | Enum describing the rubric output type. |

### `readings`

| Column | Description |
| --- | --- |
| `id` | Reading identifier (UUID). |
| `collection_id` | Collection that owns the reading. |
| `content_hash` | SHA-256 identity hash (unique per collection). |
| `config_hash` | Denormalized preset association hash (template readings only). |
| `is_template` | Whether this is a template or scripted reading. |
| `prompt_template_segments` | JSON template segments (template readings only). |
| `context_configs` | JSON context configs (template readings only). |
| `dql_query` | DQL query (template readings only). |
| `model_json` | Model configuration. |
| `output_schema` | JSON schema for output validation. |
| `source_reading_preset_id` | Optional associated preset. |
| `created_at` | When the reading was created. |

### `reading_results`

| Column | Description |
| --- | --- |
| `id` | Result identifier (UUID). |
| `cache_key_hash` | Hash for cross-reading cache lookups. |
| `arguments_dict` | JSON mapping of labeled context items. |
| `prompt_segments` | Per-result prompt (scripted readings only). |
| `llm_context_spec` | Structured context spec (scripted readings only). |
| `output` | JSON output (null if pending or error). |
| `error` | JSON error details if the call failed. |
| `input_tokens` | Input token count. |
| `output_tokens` | Output token count. |
| `model` | Actual model used. |

**`arguments_dict` structure**

For template readings, keys are param names (matching template slot names); values are typed context item objects:

| Type | Fields |
| --- | --- |
| `"transcript"` | `id`, `agent_run_id`, `collection_id` |
| `"transcript_slice"` | `transcript_id`, `start_idx`, `end_idx`, `agent_run_id`, `collection_id` |
| `"agent_run"` | `id`, `collection_id` |
| `"reading_result"` | `id`, `collection_id` |

Each value may also be a list of the above objects if the param accepts multiple items.

For scripted readings, `arguments_dict` holds arbitrary user-supplied metadata passed in per-request; it is included in the cache key but not used to resolve template parameters.

### `reading_result_links`

| Column | Description |
| --- | --- |
| `reading_id` | FK to readings.id. |
| `result_id` | FK to reading_results.id. |

### `analysis_sessions`

| Column | Description |
| --- | --- |
| `id` | Session identifier (UUID). |
| `collection_id` | Collection that owns the session. |
| `name` | Display name (from session_name or source script). |
| `readings_json` | Ordered list of step entries (readings, dql_only, headings). |
| `created_at` | When the session was created. |
| `updated_at` | Last modification time. |

## JSON Metadata Access Patterns

Docent stores user-supplied metadata as JSON. Access using Postgres operators:

```sql
-- Filter agent runs by a metadata attribute
SELECT id, name
FROM agent_runs
WHERE metadata_json->>'environment' = 'staging';
```

```sql
-- Retrieve nested transcript metadata
-- Dots in `get_metadata_fields` output (e.g. `metadata.conversation.speaker`) indicate nested JSON objects;
-- traverse with -> for intermediate keys and ->> for the final key.
SELECT
  id,
  metadata_json->'conversation'->>'speaker' AS speaker,
  metadata_json->'conversation'->>'topic' AS topic
FROM transcripts
WHERE metadata_json->>'status' = 'flagged';
```

```sql
-- Cast numeric metadata for aggregation
SELECT
  AVG(CAST(metadata_json->>'latency_ms' AS DOUBLE PRECISION)) AS avg_latency_ms
FROM agent_runs
WHERE metadata_json ? 'latency_ms';
```

When querying JSON fields, comparisons default to string semantics. Cast values when you need numeric ordering or aggregation.

## Allowed Syntax

| Feature |
| --- |
| `SELECT`, `DISTINCT`, `FROM`, `WHERE`, subqueries |
| `JOIN`, `LEFT JOIN`, `RIGHT JOIN`, `FULL JOIN`, `CROSS JOIN` |
| `WITH` (CTEs) |
| `UNION [ALL]`, `INTERSECT`, `EXCEPT` |
| `GROUP BY`, `HAVING` |
| Aggregations (`COUNT`, `AVG`, `MIN`, `MAX`, `SUM`, `STDDEV_POP`, `STDDEV_SAMP`, `VAR_POP`, `VAR_SAMP`, `ARRAY_AGG`, `STRING_AGG`, `JSON_AGG`, `JSONB_AGG`, `JSON_OBJECT_AGG`, `PERCENTILE_CONT`, `PERCENTILE_DISC` with `WITHIN GROUP`) |
| Window functions (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`, `LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE`, `NTH_VALUE`, `PERCENT_RANK`, `CUME_DIST`) |
| `ORDER BY`, `LIMIT`, `OFFSET` |
| Conditional & null helpers (`CASE`, `COALESCE`, `NULLIF`) |
| Boolean logic (`AND`, `OR`, `NOT`) |
| Comparison operators (`=`, `!=`, `<`, `<=`, `>`, `>=`, `IS`, `IS NOT`, `IS DISTINCT FROM`, `IN`, `BETWEEN`, `LIKE`, `ILIKE`, `EXISTS`, `SIMILAR TO`, `~`, `~*`, `!~`, `!~*`) |
| Arithmetic & math (`+`, `-`, `*`, `/`, `%`, `POWER`, `ABS`, `SIGN`, `SQRT`, `LN`, `LOG`, `EXP`, `GREATEST`, `LEAST`, `FLOOR`, `CEIL`, `ROUND`, `RANDOM`) |
| String helpers (`SUBSTRING`, `LEFT`, `RIGHT`, `LENGTH`, `UPPER`, `LOWER`, `INITCAP`, `TRIM`, `REPLACE`, `SPLIT_PART`, `POSITION`, `CONCAT`, `CONCAT_WS`, `STRING_AGG`) |
| JSON operators & functions (`->`, `->>`, `#>`, `#>>`, `@>`, `?`, `?|`, `?&`, `jsonb_build_object`, `jsonb_build_array`, `json_agg`, `jsonb_agg`, `json_object_agg`, `jsonb_set`, `jsonb_path_query`, `jsonb_path_exists`) |
| Date/time basics (`CURRENT_DATE`, `CURRENT_TIME`, `CURRENT_TIMESTAMP`, `NOW()`, `EXTRACT`, `DATE_TRUNC`, `AGE`, `AT TIME ZONE`, `timezone()`) |
| Interval arithmetic (`timestamp +/- INTERVAL`, `INTERVAL` literals, `MAKE_INTERVAL`, `JUSTIFY_DAYS`, `JUSTIFY_HOURS`, `JUSTIFY_INTERVAL`) |
| Construction & conversion (`MAKE_DATE`, `MAKE_TIME`, `MAKE_TIMESTAMP`, `MAKE_TIMESTAMPTZ`, `TO_CHAR`, `TO_DATE`, `TO_TIMESTAMP`, `DATE_PART`) |
| Array helpers (`ARRAY[...]`, `array_cat`, `array_length`, `cardinality`, `unnest`, `ARRAY(SELECT ...)`, `= ANY`, `= ALL`, `array_position`, `array_remove`) |
| Type helpers (`CAST`, `::`) |

Unsupported constructs include `*`, user-defined functions, and any DDL or DML commands.

## Example Queries

### Recent Runs

```sql
SELECT
  id,
  name,
  metadata_json->'model'->>'name' AS model_name,
  created_at
FROM agent_runs
WHERE metadata_json->>'status' = 'completed'
ORDER BY created_at DESC
LIMIT 10;
```

### Transcript Counts per Group

```sql
SELECT
  tg.id AS group_id,
  tg.name AS group_name,
  COUNT(t.id) AS transcript_count
FROM transcript_groups tg
JOIN transcripts t ON t.transcript_group_id = tg.id
GROUP BY tg.id, tg.name
HAVING COUNT(t.id) > 1
ORDER BY transcript_count DESC;
```

### Flagged Judge Results

```sql
SELECT
  jr.agent_run_id,
  jr.rubric_id,
  jr.result_metadata->>'label' AS label,
  jr.output->>'score' AS score
FROM judge_results jr
WHERE jr.result_metadata->>'severity' = 'high'
  AND EXISTS (
    SELECT 1
    FROM agent_runs ar
    WHERE ar.id = jr.agent_run_id
      AND ar.metadata_json->>'environment' = 'prod'
  )
ORDER BY CAST(jr.output->>'score' AS DOUBLE PRECISION) DESC
LIMIT 25;
```

### Completion Rate by Environment (CTE pattern)

```sql
WITH normalized_runs AS (
  SELECT
    metadata_json->>'environment' AS environment,
    metadata_json->>'status' AS status
  FROM agent_runs
  WHERE metadata_json ? 'environment'
)
SELECT
  environment,
  COUNT(environment) AS total_runs,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_runs,
  ROUND(CAST(
    CAST(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS DOUBLE PRECISION)
    / NULLIF(COUNT(environment), 0)
  AS NUMERIC), 3) AS completion_rate
FROM normalized_runs
GROUP BY environment
ORDER BY total_runs DESC;
```

### Latest Rubric Scores by Model

```sql
WITH latest_scores AS (
  SELECT
    agent_run_id,
    MAX(rubric_version) AS rubric_version
  FROM judge_results
  WHERE rubric_id = 'helpful_response_v1'
  GROUP BY agent_run_id
)
SELECT
  ar.id,
  ar.metadata_json->'model'->>'name' AS model_name,
  jr.output->>'score' AS score,
  jr.result_metadata->>'label' AS label
FROM latest_scores ls
JOIN judge_results jr
  ON jr.agent_run_id = ls.agent_run_id
  AND jr.rubric_version = ls.rubric_version
  AND jr.rubric_id = 'helpful_response_v1'
JOIN agent_runs ar ON ar.id = jr.agent_run_id
WHERE ar.metadata_json->>'environment' = 'prod'
ORDER BY CAST(jr.output->>'score' AS DOUBLE PRECISION) DESC
LIMIT 15;
```

### Reading Results for a Specific Reading

```sql
SELECT
  rr.id AS result_id,
  rrl.reading_id,
  rr.output,
  rr.error,
  rr.arguments_dict
FROM reading_results rr
JOIN reading_result_links rrl ON rrl.result_id = rr.id
WHERE rrl.reading_id = '<reading-uuid>'
ORDER BY rr.id DESC
LIMIT 50;
```

## Restrictions and Best Practices

- **Read-only**: Only `SELECT`-style queries are permitted.
- **Single statement**: Batches or multiple statements are rejected.
- **Explicit projection**: Wildcard projections (`*`) are disallowed. List the columns you need.
- **Collection scoping**: A single query can only access data within a single collection.
- **Limit enforcement**: Every query is capped at 10,000 rows. Use pagination (`OFFSET`/`LIMIT`) for larger result sets.
- **JSON performance**: Heavy JSON traversal across large collections can be slow. Prefer top-level fields when available.
- **Type awareness**: Cast values explicitly when precision matters.

## DQL quirks

### No Wildcards Allowed
- `SELECT *` is forbidden
- `COUNT(*)` is forbidden - use `COUNT(column_name)` instead

### No DISTINCT ON
`DISTINCT ON (column)` is not supported in DQL (it uses tuple expressions, which are forbidden). Use `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` with a `WHERE rn = 1` filter instead:
```sql
-- Wrong: SELECT DISTINCT ON (task) id, task FROM agent_runs ORDER BY task, id
-- Right:
SELECT id, task FROM (
    SELECT ar.id AS id, ar.metadata_json->>'task' AS task,
           ROW_NUMBER() OVER (PARTITION BY ar.metadata_json->>'task' ORDER BY ar.id) AS rn
    FROM agent_runs ar
) AS subq
WHERE rn = 1
```

### GROUP BY: Always Use the Subquery Pattern
Aliases, CASE expressions, and COALESCE don't work directly in GROUP BY when selecting from `agent_runs`. **Use the subquery pattern by default for ALL queries that GROUP BY derived columns** — it is never wrong and avoids the most common class of DQL errors:

```sql
SELECT task, model_name, COUNT(task) AS run_count
FROM (
    SELECT
        metadata_json->>'task' AS task,
        metadata_json->'agent'->>'model_name' AS model_name
    FROM agent_runs
    WHERE ...
) AS subq
GROUP BY task, model_name
```

**Common pitfall: only GROUP BY the dimensions, not the aggregated columns.** When the outer SELECT has both grouping columns and aggregations (COUNT, AVG, etc.), only the grouping columns go in GROUP BY. Putting aggregated columns in GROUP BY turns each row into its own group and defeats the aggregation:

```sql
-- Wrong: includes aggregated columns in GROUP BY
SELECT task, COUNT(task) AS run_count, ROUND(CAST(AVG(score) AS NUMERIC), 3) AS avg_score
FROM (...) AS subq
GROUP BY task, run_count, avg_score

-- Right: only the dimension column
SELECT task, COUNT(task) AS run_count, ROUND(CAST(AVG(score) AS NUMERIC), 3) AS avg_score
FROM (...) AS subq
GROUP BY task
```

### Avoid Dynamic IN Clauses with String Interpolation
Building IN clauses with f-strings is dangerous:
- Task names containing `::` can be parsed as PostgreSQL type casts
- Instead: use a subquery or CTE to derive the filter set in DQL, or as a last resort, fetch all relevant data and filter in Python

```sql
-- Dangerous: task_name::v2 gets parsed as a type cast
-- WHERE task IN ('task_name::v2', 'other_task::v3')

-- Safe: derive the filter set from a CTE or subquery
WITH target_tasks AS (
    SELECT DISTINCT task FROM (
        SELECT metadata_json->>'task' AS task FROM agent_runs
    ) AS subq
    WHERE task LIKE '%retry%'
)
SELECT ar.id FROM agent_runs ar
JOIN target_tasks tt ON ar.metadata_json->>'task' = tt.task
```

### ROUND Requires NUMERIC Cast
`ROUND(double_precision, integer)` does not exist in DQL. Cast to NUMERIC first:
```sql
-- Wrong: ROUND(AVG(...), 3)
-- Right:
ROUND(CAST(AVG(...) AS NUMERIC), 3)
```

### JSON Access Patterns
- Nested: `metadata_json->'parent'->>'child'`
- Flat key with dot: `metadata_json->>'parent.child'`
- Check key existence: `metadata_json ? 'key'`

# DQL (Docent Query Language) Reference

Docent Query Language is a read-only SQL subset that supports ad-hoc exploration in Docent.

Queries can only run over a single collection by design.

## Executing DQL

Choose the right method based on context:

* **`execute_dql` MCP tool** — Use for ad-hoc exploration and orientation (Step 1). Runs DQL directly without requiring user approval of inline scripts. Preferred for all exploratory queries.
* **`client.query()`** — Use inside analysis plan scripts. Query and results table appear in Docent UI. Use this for DQL that feeds data into readings, or that you want the user to see alongside reading results. Pass `name="..."` to give the step a display name.
* **`client.execute_dql()`** — Use inside Python scripts for internal logic (e.g., conditional logic between reading steps, or data that feeds into scripted readings). Results are NOT shown in the Docent UI.

```python
from docent.sdk.client import Docent

client = Docent()
collection_id = "<collection-uuid>"

# (Optional) inspect available tables/columns
schema = client.get_dql_schema(collection_id)

# In analysis plan scripts: query as a UI-visible step
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
| `readings` | Reading definitions (template or scripted LLM analysis). |
| `reading_results` | Results from running readings. |
| `reading_result_links` | Junction table linking readings to their results. |

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
| `messages` | UTF-8 bytes of a JSON array of message turns (Postgres `bytea`, not `jsonb`). Use `convert_from` before JSON operators or `jsonb_array_length` (see [Counting transcript messages](#counting-transcript-messages)). |
| `metadata_json` | UTF-8 bytes of JSON metadata (`bytea`). Same `convert_from` pattern as `messages` when using JSON operators. |
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
| `max_new_tokens` | Maximum number of new tokens generated per LLM call. |
| `num_rollouts` | Number of independent LLM samples generated per input row (>= 1). |
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
| `rollout_index` | 0-based position of this rollout within the reading's group for the same input row. Range `[0, readings.num_rollouts)`. |

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
-- `transcripts.metadata_json` is bytea (UTF-8 JSON), not jsonb — decode before JSON operators.
-- Dots in `get_metadata_fields` output (e.g. `metadata.conversation.speaker`) indicate nested JSON objects;
-- traverse with -> for intermediate keys and ->> for the final key.
SELECT
  id,
  meta->'conversation'->>'speaker' AS speaker,
  meta->'conversation'->>'topic' AS topic
FROM (
  SELECT
    id,
    convert_from(metadata_json, 'UTF8')::jsonb AS meta
  FROM transcripts
) AS t
WHERE meta->>'status' = 'flagged';
```

```sql
-- Cast numeric metadata for aggregation
SELECT
  AVG(CAST(metadata_json->>'latency_ms' AS DOUBLE PRECISION)) AS avg_latency_ms
FROM agent_runs
WHERE metadata_json ? 'latency_ms';
```

When querying JSON fields, comparisons default to string semantics. Cast values when you need numeric ordering or aggregation.

## Counting transcript messages

`transcripts.messages` is stored as `bytea` (UTF-8 JSON), not `jsonb`. You cannot use `messages -> 0` or `jsonb_array_length(messages)` directly — Postgres reports `operator does not exist: bytea -> integer`.

Decode to `jsonb`, then count array elements:

```sql
jsonb_array_length(convert_from(messages, 'UTF8')::jsonb)
```

Allowed helpers: `convert_from`, `convert_to`, `jsonb_array_length`.

### Agent runs with at least N messages (any transcript)

```sql
SELECT DISTINCT ar.id AS agent_run_id
FROM agent_runs ar
JOIN transcripts t ON t.agent_run_id = ar.id
WHERE jsonb_array_length(convert_from(t.messages, 'UTF8')::jsonb) >= 10;
```

### Per-transcript message counts

```sql
SELECT
  transcript_id,
  agent_run_id,
  message_count
FROM (
  SELECT
    t.id AS transcript_id,
    t.agent_run_id,
    jsonb_array_length(convert_from(t.messages, 'UTF8')::jsonb) AS message_count
  FROM transcripts t
) AS counted
WHERE message_count >= 10
ORDER BY message_count DESC;
```

Express filters like “≥10 messages” in DQL with the pattern above. Do not materialize matching run IDs elsewhere and paste them into a huge `WHERE id IN (...)` clause.

## Allowed Syntax

| Feature |
| --- |
| `SELECT`, `DISTINCT`, `FROM`, `WHERE`, subqueries |
| `JOIN`, `LEFT JOIN`, `RIGHT JOIN`, `FULL JOIN`, `CROSS JOIN` |
| `WITH` (CTEs) |
| `UNION [ALL]`, `INTERSECT`, `EXCEPT` |
| `GROUP BY`, `HAVING` |
| Aggregations (`COUNT`, `AVG`, `MIN`, `MAX`, `SUM`, `STDDEV_POP`, `STDDEV_SAMP`, `VAR_POP`, `VAR_SAMP`, `ARRAY_AGG`, `STRING_AGG`, `JSON_AGG`, `JSONB_AGG`, `JSON_OBJECT_AGG`, `MODE`, `PERCENTILE_CONT`, `PERCENTILE_DISC` with `WITHIN GROUP`) |
| Window functions (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`, `LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE`, `NTH_VALUE`, `PERCENT_RANK`, `CUME_DIST`) |
| `ORDER BY`, `LIMIT`, `OFFSET` |
| Conditional & null helpers (`CASE`, `COALESCE`, `NULLIF`) |
| Boolean logic (`AND`, `OR`, `NOT`) |
| Comparison operators (`=`, `!=`, `<`, `<=`, `>`, `>=`, `IS`, `IS NOT`, `IS DISTINCT FROM`, `IN`, `BETWEEN`, `LIKE`, `ILIKE`, `EXISTS`, `SIMILAR TO`, `~`, `~*`, `!~`, `!~*`) |
| Arithmetic & math (`+`, `-`, `*`, `/`, `%`, `POWER`, `ABS`, `SIGN`, `SQRT`, `LN`, `LOG`, `EXP`, `GREATEST`, `LEAST`, `FLOOR`, `CEIL`, `ROUND`, `RANDOM`) |
| String helpers (`SUBSTRING`, `LEFT`, `RIGHT`, `LENGTH`, `UPPER`, `LOWER`, `INITCAP`, `TRIM`, `REPLACE`, `SPLIT_PART`, `POSITION`, `CONCAT`, `CONCAT_WS`, `STRING_AGG`) |
| JSON operators & functions (`->`, `->>`, `#>`, `#>>`, `@>`, `?`, `?|`, `?&`, `jsonb_build_object`, `jsonb_build_array`, `jsonb_array_length`, `json_agg`, `jsonb_agg`, `json_object_agg`, `jsonb_set`, `jsonb_path_query`, `jsonb_path_exists`, `convert_from`, `convert_to`) |
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

### Rollouts and Self-Consistency

When a reading is configured with `num_rollouts > 1`, each input row produces multiple
independent LLM samples. Rollouts are stored as separate `reading_results` rows joined
to the reading via `reading_result_links`, with `reading_result_links.rollout_index`
recording the 0-based position within the reading. Samples are fungible: a single
result row may be linked by multiple readings (at potentially different rollout
positions) when a cached sample is reused.

**Always filter out pending and failed rollouts before aggregating outputs.** The
canonical predicate is:

```sql
rr.output IS NOT NULL AND (rr.error IS NULL OR rr.error::text = 'null')
```

`error` is JSONB, so SQL `NULL` and JSON `null` are both possible.

#### Per-row rollouts side by side

```sql
SELECT
  rr.arguments_dict->'agent_run'->>'id' AS agent_run_id,
  rrl.rollout_index,
  rr.output->>'answer' AS answer
FROM reading_results rr
JOIN reading_result_links rrl ON rrl.result_id = rr.id
WHERE rrl.reading_id = '<reading-uuid>'
  AND rr.output IS NOT NULL
ORDER BY agent_run_id, rrl.rollout_index;
```

#### Per-row self-consistency and modal vote

`COUNT(DISTINCT ...)` measures spread; `MODE() WITHIN GROUP` picks the majority answer.

```sql
SELECT
  rr.arguments_dict->'agent_run'->>'id' AS agent_run_id,
  COUNT(rr.id) AS n_completed,
  COUNT(DISTINCT rr.output->>'answer') AS n_distinct_answers,
  MODE() WITHIN GROUP (ORDER BY rr.output->>'answer') AS modal_answer
FROM reading_results rr
JOIN reading_result_links rrl ON rrl.result_id = rr.id
WHERE rrl.reading_id = '<reading-uuid>'
  AND rr.output IS NOT NULL
GROUP BY agent_run_id;
```

To compare two readings, wrap this query (selecting `agent_run_id, modal_answer`) as a
subquery per reading and join the two on `agent_run_id`.

#### Reading-level self-consistency rate

```sql
SELECT
  reading_id,
  ROUND(CAST(AVG(CASE WHEN n_distinct = 1 THEN 1.0 ELSE 0.0 END) AS NUMERIC), 3)
    AS unanimous_row_fraction,
  ROUND(CAST(AVG(n_distinct) AS NUMERIC), 3) AS avg_distinct_per_row
FROM (
  SELECT
    rrl.reading_id AS reading_id,
    rr.cache_key_hash AS row_key,
    COUNT(DISTINCT rr.output->>'answer') AS n_distinct
  FROM reading_results rr
  JOIN reading_result_links rrl ON rrl.result_id = rr.id
  WHERE rrl.reading_id IN ('<reading-A>', '<reading-B>')
    AND rr.output IS NOT NULL
  GROUP BY rrl.reading_id, rr.cache_key_hash
) AS row_stats
GROUP BY reading_id;
```

**Counting semantics.** Because cached samples are pooled across readings, a single
`reading_results` row may appear in multiple readings via different links. Choose:

- `COUNT(rr.id)` or `COUNT(rrl.result_id)` — counts links (i.e. rollouts as seen by
  this reading set). What you usually want.
- `COUNT(DISTINCT rr.id)` — counts unique LLM calls (i.e. the underlying sample pool).

**Rollout pairing caveat.** `rollout_index` is per-link, not per-result: rollout #2 of
reading A and rollout #2 of reading B are not paired draws. Avoid joining across
readings on `(input, rollout_index)` for paired tests — fungible samples have no
positional identity across readings.

## Restrictions and Best Practices

- **Read-only**: Only `SELECT`-style queries are permitted.
- **Single statement**: Batches or multiple statements are rejected.
- **Explicit projection**: Wildcard projections (`*`) are disallowed. List the columns you need.
- **Collection scoping**: A single query can only access data within a single collection.
- **Limit enforcement**: Every query is capped at 10,000 rows. Use pagination (`OFFSET`/`LIMIT`) for larger row collections.
- **JSON performance**: Heavy JSON traversal across large collections can be slow. Prefer top-level fields when available.
- **Type awareness**: Cast values explicitly when precision matters.
- **Reading results: filter by completion.** Querying `reading_results` will include pending and failed rollouts by default. Add `WHERE rr.output IS NOT NULL AND (rr.error IS NULL OR rr.error::text = 'null')` to any aggregation that should ignore them.

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

### Do not inline large lists of precomputed IDs
When a filter depends on transcript shape (message count, metadata, joins), compute it in DQL with `JOIN`/`WHERE`/`GROUP BY` — not by pasting hundreds of UUIDs into `WHERE agent_runs.id IN ('…', '…', …)`. That pattern is hard to maintain, blows query size limits, and usually means the real filter belongs in SQL (see [Counting transcript messages](#counting-transcript-messages)).

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

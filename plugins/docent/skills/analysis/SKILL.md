---
name: analysis
description: Docent is a platform for analyzing AI agent behavior using large language models. Use this skill anytime you want to use Docent to analyze AI agent behavior.
alwaysApply: true
---

# Docent Analysis Guide

You can interact with Docent by writing Python scripts that use the Docent SDK, and by calling Docent MCP tools. If Docent MCP tools are not available, alert the user that the Docent MCP server is not installed correctly.

## Data models and key concepts
* A transcript is a sequence of messages from the system, the agent (aka assistant), the user, and/or tools that the agent calls.
* An agent run represents an AI agent attempting a task or interacting with a user. An agent run may contain one or more transcripts.
* A collection contains agent runs from a certain experiment or benchmark. When we query, analyze, or compare agent runs, we do so within one collection at a time.

## SDK basics and getting oriented
The Docent SDK can be installed via `docent-python` (e.g., `uv add docent-python`).

```python
from docent.sdk.client import Docent
client = Docent()
```

The Docent SDK can be configured by a docent.env file in the working directory. The SDK will automatically discover and load a docent.env file if it exists. You do not need to explicitly source docent.env.

If you're not sure what collection the user is talking about, refer to the docent.env file in the working directory. If it does not exist, or if it does not include DOCENT_COLLECTION_ID, ask the user to paste the collection UUID.

## High-level analysis approach
The Docent SDK facilitates two main techniques:
* DQL, a read-only subset of SQL, to query and aggregate data already in the database (e.g. metadata that was logged with agent runs and transcripts, previous analysis results)
* Readings, to have LLMs read transcripts and perform qualitative analysis.

Sometimes, the user's request will clearly pertain to one of these techniques. Other times, the user may instead ask high-level questions about the behavior of their AI agents, and you will have to investigate. In the latter case, the following general process is recommended:

1. Use the `get_metadata_fields` MCP tool to understand the structure of agent run metadata for the current collection.
2. If the metadata fields might shed light on the user's question, you may use DQL to query the metadata. You may do this autonomously without consulting the user.
3. After querying the metadata, you must decide whether qualitative analysis (reading the transcripts) would provide further insight. If it seems appropriate, use readings. Feel free to ask the user clarifying questions to ensure your readings match their intent.

## Troubleshooting
If you run into any issues or unexpected behavior with the Docent platform, pause and alert the user. Do not try to work around them autonomously.

* If the user has read-only access to the collection, you cannot save new reading plans. Mention to the user that they can create their own clone of the collection in the Docent web UI.
* If the SDK does not match what's documented below, check whether the SDK is up to date.

# Readings

The reading API lets you run LLM analysis over collections of agent transcripts. You write normal code — `client.query()` to select data, `client.read()` to define analysis — and the SDK handles batching, caching, and orchestration.

A reading makes multiple calls to an LLM with different but related prompts. For example, you might want to check 50 different transcripts for environment configuration issues. There are two ways to create readings:
* Template readings: you provide a prompt template and a DQL query. Each prompt will be produced by substituting columns from that row into the prompt template. If you want to include a whole array of items in one prompt, use ARRAY_AGG() and annotate that column with `is_list=True` when you make its type explicit.
* Scripted readings: you write Python code to assemble the list of prompts.

Before you write any code to create a reading, ask yourself: can I use a template reading for this task? Prefer to use template readings. Note: if you need to put 2 agent runs in a prompt for comparison, you can often do this with a template reading by constructing a DQL query that selects 2 columns of agent run IDs.

Use scripted readings only when you need additional flexibility, e.g. varying the prompt using conditional logic, or including a variable number of items in the prompt.

Readings are executed lazily: nothing runs until `flush()` is called. You normally do not need to call `flush()` manually. `flush()` is automatically called at script exit, and also anytime you attempt to access the output of a reading which has not been run yet. The system infers the execution DAG automatically. Re-running the same script is free: readings are content-addressed, so identical analyses reuse existing results.

When readings are flushed, they will appear in a web UI for the user to approve. The script will pause execution until the user approves the readings. They may also cancel the script and ask you to make changes. (Note: the reading plan interface in the web UI is read-only.)

You should feel free to iterate on your scripts, but avoid overwriting scripts with something unrelated.

* Fix a problem in your analysis -> modify existing script and re-run
* Extend your analysis on the same topic with an additional reading -> modify existing script and re-run
* Explore a new question on the same dataset -> create a new script
* Take a different approach to the same question -> create a new script

Note: an obsolete version of the SDK provided an API called `LLMRequest`. If you encounter old code using LLMRequests, you can offer to migrate it to readings.

## Core API

### `client.query(collection_id, dql) -> QueryResult`
Returns a lazy handle.

For non-trivial queries, you may include comments within the DQL string to clarify (normal `--` SQL syntax).

Access attributes to get `ColumnRef` objects (e.g., `rows.transcript`).

When you use a ColumnRef in a prompt template, you should make its type explicit with `.as_type()`. The type can be:
* transcript
* agent_run
* reading_result
* text

For `text`, the literal text from that column will be embedded in the prompt. For other types, the column will be interpreted as the UUID of an object in the database, and that object will be formatted as a string and embedded in the prompt.

When you specify a type, you are also specifying whether the prompt slot is scalar or list-valued:
* `.as_type("transcript")` means scalar and defaults to `is_list=False`
* `.as_type("reading_result", is_list=True)` means the column resolves to a list of reading results (i.e. the column is an ARRAY_AGG)

### `client.read(...) -> Reading`
Registers a lazy reading. Two modes:

**Template path** (with ColumnRefs from a QueryResult):
```python
reading = client.read(
    prompt_template=["Summarize: ", rows.transcript.as_type("transcript")],
    model="openai/gpt-5.4-mini",
    output_schema={...},
)
```

**Scripted path** (explicit per-request prompts):
```python
from docent import AgentRunRef, TranscriptRef, ReadingResultRef

reading = client.read(
    prompts_list=[
        # Ordinarily you'd analyze similar data in each request
        # This is just demonstrating how to pass in different items
        ["Summarize this run: ", AgentRunRef(id="<uuid>", collection_id="<uuid>")],
        ["Summarize this transcript: ", TranscriptRef(id="<uuid>", agent_run_id="<uuid>", collection_id="<uuid>")],
        ["Summarize this reading result: ", ReadingResultRef(id="<uuid>", collection_id="<uuid>")],
    ],
    model="openai/gpt-5.4-mini",
    output_schema={...},
)
```

Parameters:
- `prompt_template` or `prompts_list` (mutually exclusive)
- `model`: `"provider/model_name"` string (e.g., `"openai/gpt-5.4-mini"`)
- `output_schema`: JSON schema for structured output
- `name`: Optional display name
- `reasoning_effort`: Optional `"minimal"` | `"low"` | `"medium"` | `"high"`
- `max_tokens`: Optional maximum number of tokens to generate per result
- `collection_id`: Optional collection override (useful for scripted readings that don't infer it from a QueryResult)
- `cache_mode`: Controls caching granularity. The DQL query (if any) is always executed to resolve arguments regardless of cache mode. The content hash — covering prompt template, model config, output schema, and resolved arguments — determines reading identity.
  - `"reading"` (default): reuse an existing reading with matching content hash
  - `"results"`: always create a new reading record, but reuse individual results to avoid redundant LLM calls
  - `"none"`: no caching — force full re-evaluation

### `client.show_query_result(query_result, name=None)`
Registers a DQL-only display step. Results shown in the UI but not persisted.

### `client.step_group(label) -> StepGroupContext`
Opens a labeled step group in the session UI. Use as a context manager to auto-close the group scope:
```python
with client.step_group("Section A"):
    client.read(...)
client.read(...)  # back to top-level
```
Only use a group when several readings are closely related. Do not create a step group with a single step.

### `client.preset_reading(preset_id, query_result=None, *, name=None, cache_mode="reading") -> Reading`
Registers a reading step backed by a server-side preset. The server resolves the preset's latest config at submission time.
- `preset_id`: The reading preset ID. Use the `list_reading_presets` MCP tool to discover available presets.
- `query_result`: Optional QueryResult to override the preset's DQL query.
- `name`: Optional display name.
- `cache_mode`: See cache_mode description under `client.read()`.

### `client.flush(open_in_browser=True) -> dict`
Submits all pending readings to the server. Returns `plan_id` and per-entry `entry_statuses`. You normally do not need to call this explicitly.

### `Reading` handle
- `f"{reading}"` → `$alias` (for use in DQL referencing)
- `reading.id` → forces flush, returns real reading UUID
- `reading.results` → forces flush, blocks until complete, returns `list[ReadingResult]`
- `reading.wait()` → forces flush and blocks without returning results

### Plan naming
```python
client.plan_name = "my_analysis"  # Defaults to name of script
```

Note: reading plans are grouped by name.
* If you create a new plan with the same name as an existing plan, it will be saved as a new version of the existing plan. Therefore, when you create a reading plan, give it a reasonably specific name to reduce chances of a collision.
* If you change the name of an existing reading plan, the new version will be saved as separate and unrelated. Therefore, you should avoid renaming reading plans unnecessarily.

### Default collection ID
```python
client.default_collection_id = "<collection-uuid>"
```
Used as a fallback when `flush()` resolves which collection to target. Automatically set from `DOCENT_COLLECTION_ID` in `docent.env` or the environment if present. Can also be passed to the `Docent()` constructor as `collection_id`.

### Auto-flush
On first `read()` call, an `atexit` handler is registered. Disable with `client.auto_flush = False`.

## Step dependencies and `$alias` substitution

When a DQL query references `{reading}` (using Python f-strings with a Reading handle), the `__format__` method returns `$alias`. At execution time, the server substitutes `$alias` with the real reading ID. This enables multi-stage pipelines:

```python
classify = client.read(prompt_template=[...], model="openai/gpt-5.4-mini", output_schema={...})
# Reference classify's results in a downstream query
summary_query = client.query(
    collection_id,
    f"SELECT rr.output->>'category' AS cat FROM reading_results rr "
    f"JOIN reading_result_links rrl ON rrl.result_id = rr.id "
    f"WHERE rrl.reading_id = '{classify}'",
)
```

## Model selection

Use `"provider/model_name"` format. Use `"openai/gpt-5.4-mini"` as the default.

Important: Do not use openai/gpt-4o or openai/gpt-4o-mini. Those models are obsolete.

## Output schema

If you need structured output, you may provide a JSON schema.

String fields may optionally allow the LLM to cite parts of its input.
* Fields such as "summary" or "description" or "explanation" should usually have citations.
* Do not include citations for fields such as "category", "classification" or any other field which is likely to be filtered on downstream.

```python
output_schema = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["helpful", "harmful", "neutral"]},
        "reasoning": {"type": "string", "citations": True},
    },
    "required": ["category", "reasoning"],
}
```

The default schema is a freeform string with citations. If that's all you need, do not pass a custom schema.

### Writing a good prompt

The quality of reading output depends on the quality the prompt you write. The LLM knows it is analyzing agent run transcripts, and knows how to cite items in its context. You can ask the LLM to cite items in its context and it will just work without further guidance. Otherwise, you are responsible for understanding the purpose of the analysis and writing a clear prompt articulating what you want the LLM to do.

* Include any information about the runs that is not obvious from the transcripts but important for analyzing them appropriately
* How detailed or brief should output be? A short paragraph is a good default, but it depends on the nature of the analysis.
* If you're asking for extensive (multi-paragraph) response, how should it be structured? Note: markdown is supported
* If you are looking for a particular behavior, how exactly is that behavior defined? If you're proposing a specific definition, make sure the user signs off on it.
* If you are asking the LLM to analyze other reading results, remind it to cite those reading results, NOT the original transcripts which the results may refer to.

## Analysis guidelines and reminders
* If the user asks you to "summarize the agent runs", "classify the results", or similar, they do not necessarily mean that you (the coding agent) should do so directly. In most cases, it is better to use readings for this.
* It's good to ask clarifying questions! If you're uncertain of the user's intent, ask and wait for their answer before proceeding.
* Agent runs contain metadata. Metadata varies by collection. Do not make assumptions about the structure of run metadata. Use the `get_metadata_fields` MCP tool to find out.
* You must write your code out as a script file. Unless otherwise instructed, you may place analysis scripts in the current working directory.
* If you're doing exploratory DQL queries before writing the full reading plan, put those queries in the same Python file that the reading plan will go into. Use `client.show_query_result()` so they show up in the UI. Put exploratory queries before the main reading plan, in a group titled "Explore the dataset" or similar, so the user can collapse them if desired.
* Make DQL query results self-verifying. Include extra columns that let the user confirm your query logic at a glance. The user should be able to verify correctness from the output alone, without re-reading the SQL. For example:
  * If you filter by a condition, include the filtered column in the SELECT.
  * If you join or pair rows on a key (e.g., matching runs by task), include that key for both sides.
  * If you compare values (e.g., selecting rows where model A outperformed model B), include both models' names and scores, not just the winning run.
* Unless informed otherwise, assume uv is used for python package management. Run your scripts with `uv run`.
* When writing code for readings, Don't Repeat Yourself. This is particularly important when it comes to prompts for LLMs. The user will likely want to modify prompts, and they should not have to track down multiple copies of a prompt throughout your code. If you need to create different variants of a prompt, build them from reusable pieces and/or use string interpolation, so there is a single source of truth for each part of the prompt.
* When writing code for readings, keep variable names generic. For example, if you are comparing the performance of two models, you might refer to them as "model_a" and "model_b" in your code, and then declare the identity of these models in one place only. This makes your code more reusable, so we can perform the same analysis on other data.
* When writing code for readings, be sparing with print statements.
* If you are analyzing a limited sample of many items (e.g. because you can only fit so many in the context window), be mindful of *how* you are sampling them. The most recent N items may be a biased sample. It is safe to assume that UUIDs are random.
* If you are using a reading to categorize things (e.g. types of problems, strategies, or mistakes), don't try to come up with a good list of categories without looking at the data. See the clustering example below.
* Metadata alone may provide an incomplete picture. Don't forget to consider qualitative analysis!
* You are responsible for running your reading plan scripts when appropriate. The user should not have to do so manually. After you create or update a reading plan script, don't forget to run (or re-run) it!
* Use the `get_reading_plan_results` MCP tool to inspect the results of a reading plan. Call it with just `collection_id` and `plan_name` to see an overview of all steps and their statuses. Call it with an additional `step_name` to see the actual results for a specific step (LLM outputs for reading steps, query results for DQL-only steps).
* When communicating with the user, refer to steps by name; do not number the steps.

## Example: clustering
A common workflow to cluster behaviors 3 readings.
1. Summarize each transcript or agent run, focusing on the aspect of behavior you want to cluster (e.g. failure modes, problem-solving strategies)
2. Put all the summaries into a single context window and identify patterns across all of them (or a random sample, if there are over ~100 items). This reading should output an array of clusters with names and descriptions.
3. Assign each transcript or agent run to a cluster. This reading should output an enum for each agent run. The possible enum values should be taken from the output of reading 2.

In the example below, we are clustering mistakes in a sample of transcripts. You can apply this principle to other aspects of agent behavior.

```python
from docent import Docent

client = Docent()
collection_id = "<collection_id>"
client.plan_name = "Mistake clustering"

# Step 1: Freeform summary of a sample of transcripts
sampled_transcripts = client.query(
    collection_id,
    "SELECT transcripts.id AS transcript FROM transcripts LIMIT 100",
)

summarize = client.read(
    prompt_template=[
        sampled_transcripts.transcript.as_type("transcript"),
        """
            Write a 1-2 sentence summary of any mistakes the agent made.
        """,
    ],
    model="openai/gpt-5.4-mini",
    name="Summarize runs",
)

# Step 2: Propose clusters from the summaries
summaries = client.query(
    collection_id,
    f"SELECT array_agg(rr.id) AS summaries "
    f"FROM reading_results rr "
    f"JOIN reading_result_links rrl ON rrl.result_id = rr.id "
    f"WHERE rrl.reading_id = '{summarize}' "
)

propose_clusters = client.read(
    prompt_template=[
        """
            You are reviewing mistake summaries from a sample of AI agent runs.
        """,
        summaries.summaries.as_type("reading_result"),
        """
            Based on these summaries, propose 5-10 categories that capture the
            distinct mistakes agents make. Each category should have:
            - A short snake_case name (e.g. "tool_error", "task_misunderstood")
            - A brief description of what this failure mode looks like

            The categories should be mutually exclusive and collectively exhaustive
            of the mistakes you observe.
        """,
    ],
    model="openai/gpt-5.4-mini",
    output_schema={
        "type": "object",
        "properties": {
            "categories": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["name", "description"],
                },
            },
        },
        "required": ["categories"],
    },
    name="Propose mistake clusters",
)

# Accessing output will automatically trigger flush() and user will be asked to approve the plan so far
clusters = propose_clusters.results[0].output
assert clusters is not None
categories = clusters["categories"]
categories.append({"name": "success", "description": "Agent completed the task correctly"})
category_names: list[str] = [c["name"] for c in categories]
category_descriptions = "\n".join(f"  - {c['name']}: {c['description']}" for c in categories)
print(f"Proposed {len(category_names)} clusters: {', '.join(category_names)}")

# Step 3: assign transcripts to clusters
extract = client.read(
    prompt_template=[
        sampled_transcripts.transcript.as_type("transcript"),
        f"""
            Classify this agent run using one of these categories:
            {category_descriptions}

            If the agent ultimately succeeded, classify it as "success" even if mistakes were made along the way.
            If there are multiple mistakes, focus on the one that most directly caused the agent's failure.
        """,
    ],
    model="openai/gpt-5.4-mini",
    output_schema={
        "type": "object",
        "properties": {
            "failure_category": {"type": "string", "enum": category_names},
            "description": {"type": "string", "citations": True},
        },
        "required": ["failure_category", "description"],
    },
    name="Classify each run",
)

# End of plan triggers auto-flush again
```

# DQL (Docent Query Language)

Docent Query Language is a read-only SQL subset that supports ad-hoc exploration in Docent.

Queries can only run over a single collection by design.

## Executing DQL via the Python SDK

Prefer `client.query()` — it registers the query as a UI-visible step in the analysis session. Use `client.show_query_result()` to display query results in the UI without feeding them into a reading.

`client.execute_dql()` is a lower-level escape hatch for cases where you need raw row data in Python (e.g., to drive conditional logic between reading steps). Its results are **not** shown in the Docent UI.

```python
from docent.sdk.client import Docent

client = Docent()
collection_id = "<collection-uuid>"

# (Optional) inspect available tables/columns
schema = client.get_dql_schema(collection_id)

# Preferred: query as a UI-visible step
rows = client.query(
    collection_id,
    "SELECT agent_runs.id AS agent_run_id FROM agent_runs LIMIT 10",
)
client.show_query_result(rows, name="Recent runs")

# Lower-level alternative (results not shown in UI)
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
| `context_config` | JSON context config (template readings only). |
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
ORDER BY score DESC
LIMIT 25;
```

### Completion Rate by Environment

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
  CAST(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS DOUBLE PRECISION)
    / NULLIF(COUNT(environment), 0) AS completion_rate
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

### Reading Results for a Reading

```sql
SELECT
  rr.id AS result_id,
  rrl.reading_id,
  rr.output,
  rr.error,
  rr.arguments_dict
FROM reading_results rr
JOIN reading_result_links rrl ON rrl.result_id = rr.id
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

## Reminders and tips for using DQL

### No Wildcards Allowed
- `SELECT *` is forbidden
- `COUNT(*)` is forbidden - use `COUNT(column_name)` instead

### GROUP BY Alias Workaround
Aliases don't work directly in GROUP BY when selecting from `agent_runs`. Use a subquery:

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

### Avoid Dynamic IN Clauses with String Interpolation
Building IN clauses with f-strings is dangerous:
- Task names containing `::` can be parsed as PostgreSQL type casts
- Instead: use a subquery or CTE to derive the filter set in DQL, or as a last resort, fetch all relevant data and filter in Python

### JSON Access Patterns
- Nested: `metadata_json->'parent'->>'child'`
- Flat key with dot: `metadata_json->>'parent.child'`
- Check key existence: `metadata_json ? 'key'`

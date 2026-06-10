# Readings API Reference

The reading API lets you run LLM analysis over collections of agent transcripts. You write normal code — `client.query()` to select data, `client.read()` to define analysis — and the SDK handles batching, caching, and orchestration.

A reading makes multiple calls to an LLM with different but related prompts. For example, you might want to check 50 different transcripts for environment configuration issues. There are two ways to create readings:
* Template readings: you provide a prompt template and a DQL query. Each prompt will be produced by substituting columns from that row into the prompt template. If you want to include a whole array of items in one prompt, use ARRAY_AGG() and annotate that column with `is_list=True` when you make its type explicit.
* Scripted readings: you write Python code to assemble the list of prompts.

Before you write any code to create a reading, ask yourself: can I use a template reading for this task? Prefer to use template readings. Note: if you need to put 2 agent runs in a prompt for comparison, you can often do this with a template reading by constructing a DQL query that selects 2 columns of agent run IDs.

Use scripted readings only when you need additional flexibility, e.g. varying the prompt using conditional logic, or including a variable number of items in the prompt.

Readings are executed lazily: nothing runs until `flush()` is called. You normally do not need to call `flush()` manually. `flush()` is automatically called at script exit, and also anytime you attempt to access the output of a reading which has not been run yet. The system infers the execution DAG automatically. Re-running the same script is free: readings are content-addressed, so identical analyses reuse existing results.

When readings are flushed, they will appear as an analysis plan in the web UI for the user to approve. The script will pause execution until the user approves the readings. They may also cancel the script and ask you to make changes. (Note: the analysis plan interface in the web UI is read-only.)

If you need a no-UI-approval flow for a trusted analysis, you may opt into SDK auto-approval by explicitly calling `client.flush(auto_approve=True)`. This reuses the same backend approval endpoint programmatically, including for dependent steps that are initially unresolved.

Some analysis plans require mid-script blocking, for example if one step waits for reading results (using `.results`) in order to construct a later step. In these cases:
* The script may submit an initial set of steps for approval, then block waiting for results before it can continue.
* The user may need to approve the plan more than once, unless you explicitly call `client.flush(auto_approve=True)` for each flush that should bypass manual approval.
* Warn the user upfront about multi-approval flows so they know what to expect.

Notes on what readings can see:
* When an agent run is rendered for a reading, the LLM can see the agent run metadata and all its transcripts
* When a transcript is rendered for a reading, the LLM can see the transcript metadata

You should feel free to iterate on your scripts, but avoid overwriting scripts with something unrelated.

* Fix a problem in your analysis -> modify existing script and re-run
* Extend your analysis on the same topic with an additional reading -> modify existing script and re-run
* Explore a new question on the same dataset -> create a new script
* Take a different approach to the same question -> create a new script

## Core API

### `client.query(collection_id, dql, *, name=None) -> QueryResult`
Returns a lazy handle and auto-registers a DQL-only step in the analysis session UI. Use `name` to give the step a display name. For non-trivial queries, you may include comments within the DQL string to clarify (normal `--` SQL syntax).

Access attributes to get `ColumnRef` objects (e.g., `rows.transcript`).

When you use a ColumnRef in a prompt template, you should make its type explicit with `.as_type()`. The type can be:
* transcript
* transcript_slice
* agent_run
* reading_result
* text

For `text`, the literal text from that column will be embedded in the prompt. For most other types, the column will be interpreted as the UUID of an object in the database, and that object will be formatted as a string and embedded in the prompt. The exception is `transcript_slice`, whose column value is a JSON object produced by the DQL `transcript_slice(transcript_id, start_idx, end_idx)` function (see the **Transcript slices** section below).

When you specify a type, you are also specifying whether the prompt slot is scalar or list-valued:
* `.as_type("transcript")` means scalar and defaults to `is_list=False`
* `.as_type("reading_result", is_list=True)` means the column resolves to a list of reading results (i.e. the column is an ARRAY_AGG)

### `client.read(...) -> Reading`
Registers a lazy reading. Two modes:

**Template path** (with ColumnRefs from a QueryResult):
```python
# rows = client.query(collection_id, "SELECT transcripts.id AS transcript FROM transcripts LIMIT 50")
reading = client.read(
    prompt_template=["Summarize: ", rows.transcript.as_type("transcript")],
    model="openai/gpt-5.4-mini",
    output_schema={...},
)
```

For `ARRAY_AGG` columns, pass `is_list=True`:
```python
# agg = client.query(collection_id, f"SELECT array_agg(rr.id ORDER BY rr.id) AS results FROM reading_results rr ...")
reading = client.read(
    prompt_template=["Synthesize these results: ", agg.results.as_type("reading_result", is_list=True)],
    model="openai/gpt-5.4-mini",
)
```
(Note: the ORDER BY is important. Without an ORDER BY, Postgres may later return results in a different order, invalidating the cache and triggering an expensive LLM call. If there's no natural order, you can order by ID.)

**Scripted path** (explicit per-request prompts):
```python
from docent import TranscriptRef

reading = client.read(
    prompts_list=[
        ["Summarize this transcript: ", TranscriptRef(id="<uuid-1>", agent_run_id="<uuid>", collection_id="<uuid>")],
        ["Summarize this transcript: ", TranscriptRef(id="<uuid-2>", agent_run_id="<uuid>", collection_id="<uuid>")],
    ],
    model="openai/gpt-5.4-mini",
    output_schema={...},
)
```

Other ref types for scripted readings: `AgentRunRef(id, collection_id)`, `TranscriptSliceRef(transcript_id, start_idx, end_idx, agent_run_id, collection_id)`, `ReadingResultRef(id, collection_id)`.

Parameters:
- `prompt_template` or `prompts_list` (mutually exclusive)
- `model`: `"provider/model_name"` string (e.g., `"openai/gpt-5.4-mini"`)
- `output_schema`: JSON schema for structured output
- `name`: Optional display name
- `reasoning_effort`: Optional `"minimal"` | `"low"` | `"medium"` | `"high"`
- `max_new_tokens`: Optional maximum number of new tokens to generate per result
- `collection_id`: Optional collection override (useful for scripted readings that don't infer it from a QueryResult)
- `cache_mode`: Controls caching granularity. See below

### Cache modes
The DQL query (if any) is always executed to resolve arguments regardless of cache mode. The content hash — covering prompt template, context config, model config, output schema, token limit, and resolved arguments — determines reading identity.
- `"reading"` (default): reuse an existing reading with matching content hash
- `"results"`: always create a new reading record, but reuse individual results to avoid redundant LLM calls
- `"none"`: no caching — force full re-evaluation

Note: if some results for a reading succeeded and some errored, rerunning with cache_mode="reading" will not retry the errored results. This avoids wasting time retrying problematic prompts (e.g. too long, or blocked by LLM API safety filters). If you need to force retry all errored results, run with cache_mode="results".

### Transcript slices

A `transcript_slice` parameter renders a contiguous message range on a specific transcript instead of the whole transcript. The range is inclusive on both ends (`start_idx`, `end_idx`), and rendered block labels preserve the original transcript message indices so the LLM can still cite by absolute position. Negative indices are valid and interpreted like in Python, e.g. to get the last 5 transcript blocks you could set start_idx=-5 end_idx=-1.

Transcript slices are a specialized feature, and should only be used if the user's request strongly implies that they're the right tool (e.g. "look at the last 5 messages of each transcript").

**Template reading.** Produce slice references directly in DQL with the `transcript_slice(transcript_id, start_idx, end_idx)` function, then annotate the column with `.as_type("transcript_slice")`:

```python
slices = client.query(
    collection_id,
    """
    WITH windows AS (
      SELECT
        t.id AS transcript_id,
        GREATEST(0, CAST(t.metadata_json->>'first_error_idx' AS INTEGER) - 3) AS start_idx,
        CAST(t.metadata_json->>'first_error_idx' AS INTEGER) + 3 AS end_idx
      FROM transcripts t
      WHERE t.metadata_json ? 'first_error_idx'
    )
    SELECT transcript_slice(transcript_id, start_idx, end_idx) AS window
    FROM windows
    """,
    name="Error context windows",
)

reading = client.read(
    prompt_template=[
        "Explain what went wrong in this excerpt: ",
        slices.window.as_type("transcript_slice"),
    ],
    model="openai/gpt-5.4-mini",
    name="Explain error contexts",
)
```

Notes on the DQL function:
* `transcript_slice()` must be called with exactly three arguments and emits a JSON object value. It is allowed anywhere a scalar expression is valid (including inside `CASE`, `DISTINCT`, `ORDER BY`, or `ARRAY_AGG(...)` for list-valued slots).
* Access control and collection scoping come from the underlying transcript; indices outside the transcript simply render fewer messages rather than erroring.
* `start_idx` and `end_idx` may be equal to render a single message.

**Scripted reading.** Construct a `TranscriptSliceRef` per prompt. Use this when the slice indices come from Python logic rather than SQL (e.g., derived from earlier reading results):

```python
from docent import TranscriptSliceRef

reading = client.read(
    prompts_list=[
        [
            "Summarize this excerpt: ",
            TranscriptSliceRef(
                transcript_id="<transcript-uuid>",
                start_idx=10,
                end_idx=25,
                agent_run_id="<run-uuid>",
                collection_id=collection_id,
            ),
        ],
    ],
    model="openai/gpt-5.4-mini",
    name="Slice summaries",
)
```

**Context config for slices.** `TranscriptSliceContextConfig` exposes the same filters as `TranscriptContextConfig` (`transcript_metadata`, `message_metadata`); defaults are listed under **Context configs** above. Attach it the same way as other context configs — via `context_configs={param_name: TranscriptSliceContextConfig(...)}` for template readings, or `TranscriptSliceRef(..., context_config=TranscriptSliceContextConfig(...))` for scripted readings. As with other context configs, changing it changes the reading's content hash and therefore its cache identity.


### Context configs
Use context configs to control which metadata and transcript subtrees are rendered when a reading prompt includes an `agent_run`, `transcript`, or `transcript_slice` parameter. Context configs do not change which rows DQL selects; they only change how selected context items are formatted for the LLM. They are part of the reading config/cache identity, so changing them creates a different reading.

Metadata is excluded by default, while transcript and transcript group names are included by default. Add a context config only when metadata or narrower transcript selection is needed.

Default context config settings:
* `AgentRunContextConfig`
  * `agent_run_metadata`: `EXCLUDE_ALL_GLOB_FILTER`
  * `transcript_group_names`: `INCLUDE_ALL_GLOB_FILTER`
  * `transcript_group_metadata`: `EXCLUDE_ALL_GLOB_FILTER`
  * `transcript_names`: `INCLUDE_ALL_GLOB_FILTER`
  * `transcript_metadata`: `EXCLUDE_ALL_GLOB_FILTER`
  * `message_metadata`: `EXCLUDE_ALL_GLOB_FILTER`
* `TranscriptContextConfig`
  * `transcript_metadata`: `EXCLUDE_ALL_GLOB_FILTER`
  * `message_metadata`: `EXCLUDE_ALL_GLOB_FILTER`
* `TranscriptSliceContextConfig`
  * `transcript_metadata`: `EXCLUDE_ALL_GLOB_FILTER`
  * `message_metadata`: `EXCLUDE_ALL_GLOB_FILTER`

Import the config classes directly:
```python
from docent.data_models.context_config import (
    AgentRunContextConfig,
    TranscriptContextConfig,
    TranscriptSliceContextConfig,
)
from docent.data_models.metadata_util import (
    INCLUDE_ALL_GLOB_FILTER,
    EXCLUDE_ALL_GLOB_FILTER,
    GlobFilter,
)
```
`INCLUDE_ALL_GLOB_FILTER` is a shorthand for `GlobFilter(include=("*",))`; use it only when you intentionally want the full metadata subtree for a scope.
`EXCLUDE_ALL_GLOB_FILTER` is a shorthand for `GlobFilter(exclude=("*",))`.

For a template reading, `client.read(..., context_configs=...)` takes a dict keyed by prompt parameter name. Each value should use the config type that matches the corresponding `ColumnRef` parameter type:
```python
rows = client.query(
    collection_id,
    "SELECT agent_runs.id AS run FROM agent_runs LIMIT 50",
    name="Sample runs",
)

reading = client.read(
    prompt_template=[
        "Evaluate this run, using the included metadata when relevant: ",
        rows.run.as_type("agent_run"),
    ],
    context_configs={
        "run": AgentRunContextConfig(
            agent_run_metadata=GlobFilter(include=("task.*", "score")),
            transcript_group_names=GlobFilter(exclude=("scratch-*",)),
            transcript_names=GlobFilter(include=("main", "solver-*")),
        ),
    },
    model="openai/gpt-5.4-mini",
    name="Evaluate runs with metadata",
)
```

For `transcript` and `transcript_slice` parameters, only transcript-level and message-level metadata filters are available:
```python
transcript_rows = client.query(
    collection_id,
    "SELECT transcripts.id AS transcript FROM transcripts LIMIT 50",
    name="Sample transcripts",
)

reading = client.read(
    prompt_template=[
        transcript_rows.transcript.as_type("transcript"),
        "Summarize what happened and cite any relevant metadata.",
    ],
    context_configs={
        "transcript": TranscriptContextConfig(
            transcript_metadata=GlobFilter(include=("source.*", "scenario_id")),
            message_metadata=GlobFilter(include=("tool.name", "status.code")),
        ),
    },
    model="openai/gpt-5.4-mini",
    name="Summarize transcripts with metadata",
)
```

For scripted readings, do not pass `context_configs` to `client.read()`. Put the config on each ref:
```python
from docent import AgentRunRef, TranscriptRef

reading = client.read(
    prompts_list=[
        [
            "Compare these two items: ",
            AgentRunRef(
                id="<run-id>",
                collection_id=collection_id,
                context_config=...,
            ).label("run"),
            TranscriptRef(
                id="<transcript-id>",
                agent_run_id="<run-id>",
                collection_id=collection_id,
                context_config=...,
            ).label("transcript"),
        ],
    ],
    model="openai/gpt-5.4-mini",
    name="Scripted comparison with metadata",
)
```


Glob filter rules:
* Metadata filters match dot paths inside metadata dictionaries, for example `config.model` or `usage.prompt_tokens`.
* `*`, `?`, and character ranges match within one path segment.
* Including a parent path includes the full subtree; excluding a parent drops the full subtree.
* For example, `GlobFilter(include=("usage.*",), exclude=("usage.raw_payload",))` includes `usage.prompt_tokens` and nested values under matched `usage` children, while removing `usage.raw_payload`.
* More specific patterns win. If include and exclude patterns tie, exclude wins.
* `transcript_group_names` and `transcript_names` match object names, not metadata paths or IDs. Unnamed objects do not match name filters.
* Common pitfall: do not set `transcript_group_names=GlobFilter(include=("*",))` when the user asks to render only a specific transcript name. Including all transcript groups makes all visible descendants render, so it can override the intended narrow transcript selection. In that case, make `transcript_group_names` exclude-all and set only `transcript_names=GlobFilter(include=("<requested transcript name>",))`.
* Transcript group filtering is path-scoped. Including a nested group makes that group and its visible descendants render, and any ancestors needed to reach it may render as wrappers. It does not make sibling branches visible. For example, if `G1` contains both `G2 -> G3` and `G2-prime`, including `G3` can render wrapper groups `G1` and `G2`, but `G2-prime` remains hidden unless it or one of its descendants is independently included.

### Multiple rollouts

If the user asks for multiple rollouts, you can use the `num_rollouts` parameter. Leave it unset (defaults to 1) unless the user explicitly asks.
```python
reading = client.read(
    prompt_template=["Summarize: ", rows.transcript.as_type("transcript")],
    model="openai/gpt-5.4-mini",
    num_rollouts=3
)
```

### `client.step_group(label) -> StepGroupContext`
Opens a labeled step group in the session UI. Use as a context manager to auto-close the group scope:
```python
with client.step_group("Section A"):
    client.read(...)
client.read(...)  # back to top-level
```
Only use a group when several readings are closely related. Do not create a step group with a single step.

### `client.list_reading_presets(collection_id, *, owned_only=True) -> list[dict]`
Lists reading presets in a collection.
- `owned_only=True`: returns only presets created by the current user.
- `owned_only=False`: returns all presets discoverable in the collection.

### `client.create_reading_preset(collection_id, name, reading_config) -> dict`
Creates a new reading preset lineage with version `1`.
- `name`: Exact preset name as stored on the server.
- `reading_config`: `PartialReadingConfig` or an equivalent JSON-serializable dict.
- Returns a dict containing at least `id` and `version_index`.
- Creating a preset with a duplicate name in the same collection returns `409`.

### `client.save_reading_preset_version(collection_id, preset_id, reading_config) -> dict`
Creates a new version for an existing preset.
- `preset_id`: The preset lineage ID to extend.
- `reading_config`: `PartialReadingConfig` or an equivalent JSON-serializable dict.
- Returns a dict containing the new `version_index`.
- If the config matches the latest version exactly, the server returns `409`.

### `client.update_reading_preset_name(collection_id, preset_id, name) -> dict`
Renames an existing preset lineage.
- `preset_id`: The preset lineage ID to rename.
- `name`: New exact preset name.
- Returns a status dict.
- Renaming to a name already used by another preset in the same collection returns `409`.

### `client.read_with_preset(preset_id=None, query_result=None, *, preset_name=None, name=None, prompt_template=None, model=None, output_schema=None, context_configs=None, reasoning_effort=None, max_new_tokens=None, source_reading_preset_version=None, cache_mode="reading") -> Reading`
Registers a reading step backed by a server-side preset. The server resolves the preset's latest config at submission time and combines it with any runtime fields you supply here.
- `preset_id`: The reading preset ID.
- `preset_name`: Exact preset name within the collection. Set exactly one of `preset_id` / `preset_name`.
- `query_result`: QueryResult supplying the rows for the preset-backed reading.
- `name`: Optional display name.
- `prompt_template`, `model`, `output_schema`, `context_configs`, `reasoning_effort`: Optional runtime fields used only when the preset left those fields unset. Pinned preset fields cannot be overridden.
- `max_new_tokens`: Runtime maximum number of new tokens per result. Defaults to `None`, so preset-backed reads leave this unset unless you explicitly pass an override-compatible value.
- `source_reading_preset_version`: Optional preset version to pin. When omitted, the server resolves the latest version.
- `cache_mode`: See cache_mode description under `client.read()`.

### `client.flush(open_in_browser=True, auto_approve=False) -> dict`
Submits all pending readings to the server. Returns `plan_id` and per-entry `entry_statuses`. You normally do not need to call this explicitly. If `auto_approve=True`, the SDK will immediately approve newly submitted reading steps before waiting for results. Implicit flushes triggered by `reading.id`, `reading.results`, or `atexit` do not enable auto-approval unless you call `flush(auto_approve=True)` yourself first.

### `Reading` handle
- `f"{reading}"` → `$alias` (for use in DQL referencing)
- `reading.id` → forces flush, returns real reading UUID
- `reading.results` → forces flush, blocks until complete, returns `list[ReadingResult]`

### Plan naming
```python
client.plan_name = "safety_failure_clustering"  # Defaults to name of script
```

Note: analysis plans are grouped by name.
* If you create a new plan with the same name as an existing plan, it will be saved as a new version of the existing plan. Therefore, when you create an analysis plan, give it a reasonably specific name to reduce chances of a collision.
* If you change the name of an existing analysis plan, the new version will be saved as separate and unrelated. Therefore, you should avoid renaming analysis plans unnecessarily.

### Default collection ID
```python
client.default_collection_id = "<collection-uuid>"
```
Used as a fallback when `flush()` resolves which collection to target. Automatically set from `DOCENT_COLLECTION_ID` in the SDK-discovered `docent.env` or the environment if present. Can also be passed to the `Docent()` constructor as `collection_id`.

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

Use `"provider/model_name"` format. For simple questions about transcript content, use openai/gpt-5.4-mini. For more complex interpretation, reasoning, or judgement, use openai/gpt-5.5.

Important: Do not use openai/gpt-4o or openai/gpt-4o-mini. Those models are obsolete.

## Output schema

If you need structured output, you may provide a JSON schema.

String fields may optionally allow the LLM to cite parts of its input.
* Fields such as "summary" or "description" or "explanation" should usually have citations.
* Enum fields must not have citations.
* "Reasoning" fields should come before "decision" fields. That way, the LLM is generating the decision based on the reasoning, instead of justifying its decision post-hoc.

```python
output_schema = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string", "citations": True},
        "category": {"type": "string", "enum": ["helpful", "harmful", "neutral"]},
    },
    "required": ["reasoning", "category"],
}
```

The default schema is a freeform string with citations. If that's all you need, do not pass a custom schema.

## Writing a good prompt

The quality of reading output depends on the quality the prompt you write. The LLM knows it is analyzing agent run transcripts, and knows how to cite items in its context. You can ask the LLM to cite items in its context and it will just work without further guidance. Otherwise, you are responsible for understanding the purpose of the analysis and writing a clear prompt articulating what you want the LLM to do.

* Include any information about the runs that is not obvious from the transcripts but important for analyzing them appropriately
* How detailed or brief should output be? A short paragraph is a good default, but it depends on the nature of the analysis.
* If you're asking for extensive (multi-paragraph) response, how should it be structured? Note: markdown is supported
* If you are looking for a particular behavior, how exactly is that behavior defined? If you're proposing a specific definition, make sure the user signs off on it.

## Chosing clear names
The name of each step (client.query and client.read) should fit on one line. Subject to that constraint, make step names descriptive. Ideally, the names make sense to a user without much context on your analysis. A descriptive name does not have to be wordy.

Bad step name: "Sample transcript slices"
Missing information: What kind of sample? How many? How are you slicing the transcripts?
Better name: "Get first 5 messages of 100 random transcripts"

Bad step name: "A: category only (medium reasoning)"
Missing information: What is A? Category of what? Is the reasoning from the analysis or the original transcript?
Better name: "Classify failure modes with medium reasoning"

Bad step name: "Explain A-vs-B disagreements"
Missing information: What is A and B? What are the disagreements about?
Better name: "Explain why medium-reasoning judge and high-reasoning judge assigned different failure categories"

A similar principle applies to the column names in user-facing DQL tables (i.e. tables created with client.query). Name output columns clearly with the `AS` keyword.

Bad column name: "cat"
Better name: "judge_classification"

## Coding tips for reading scripts

* You must write your code out as a script file. Place analysis scripts in a per-session subdirectory under `docent_analyses/`, using the format `docent_analyses/<date>_<short-label>/` (e.g., `docent_analyses/2026-04-20_safety-eval/`). Create the directory at the start of the session. The short label should be a 2-3 word slug describing the analysis topic. This keeps scripts organized across sessions and out of the project's working directory.
* Unless informed otherwise, assume uv is used for python package management. Run your scripts with `uv run`.
* Make DQL query results self-verifying. Include extra columns that let the user confirm your query logic at a glance. The user should be able to verify correctness from the output alone, without re-reading the SQL. For example:
  * If you filter by a condition, include the filtered column in the SELECT.
  * If you join or pair rows on a key (e.g., matching runs by task), include that key for both sides.
  * If you compare values (e.g., selecting rows where model A outperformed model B), include both models' names and scores, not just the winning run.
* Don't Repeat Yourself. This is particularly important when it comes to prompts for LLMs. The user will likely want to modify prompts, and they should not have to track down multiple copies of a prompt throughout your code. If you need to create different variants of a prompt, build them from reusable pieces and/or use string interpolation, so there is a single source of truth for each part of the prompt.
* Be sparing with print statements.
* If you are analyzing a limited sample of many items (e.g. because you can only fit so many in the context window), be mindful of *how* you are sampling them. The most recent N items may be a biased sample. It is safe to assume that UUIDs are random.
* If you are using a reading to categorize things (e.g. types of problems, strategies, or mistakes), don't try to come up with a good list of categories without looking at the data. See the clustering example below.
* **Test DQL incrementally.** When writing scripts with multiple DQL queries, test one simple query first to validate syntax patterns (casting, GROUP BY, etc.) before writing a large batch. DQL has quirks that are easier to catch one at a time than to debug across a 200-line script.

## Example: clustering

A common workflow to cluster behaviors uses 3 readings. This pattern is referenced from Step 2.5 in the main workflow — use it whenever the analysis requires categorization, grouping, or thematic clustering.

1. Summarize each transcript or agent run, focusing on the aspect of behavior you want to cluster (e.g. failure modes, problem-solving strategies)
2. Put all the summaries into a single context window and identify patterns across all of them (or a random sample, if there are over ~100 items). This reading should output an array of clusters with names and descriptions.
3. Assign each transcript or agent run to a cluster. This reading should output an enum for each agent run. The possible enum values should be taken from the output of reading 2.

**Build this incrementally.** Write Phase 1, run it, verify the clusters look right, then extend the script with Phase 2. Do not write the whole thing at once — Step 3 depends on Step 2's output, so you need to see the results before you can write the classification step correctly.

### Phase 1: Summarize and propose clusters

Write this as your script (e.g., `docent_analyses/2026-04-20_safety-eval/mistake_clustering.py`) and run it:

```python
from docent import Docent

client = Docent()
collection_id = "<collection_id>"
client.plan_name = "Mistake clustering"

# Step 1: Freeform summary of a sample of transcripts
sampled_transcripts = client.query(
    collection_id,
    "SELECT transcripts.id AS transcript FROM transcripts ORDER BY transcripts.id LIMIT 100",
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
    f"SELECT array_agg(rr.id ORDER BY rr.id) AS summaries "
    f"FROM reading_results rr "
    f"JOIN reading_result_links rrl ON rrl.result_id = rr.id "
    f"WHERE rrl.reading_id = '{summarize}' ",
)

propose_clusters = client.read(
    prompt_template=[
        """
            You are reviewing mistake summaries from a sample of AI agent runs.
        """,
        summaries.summaries.as_type("reading_result", is_list=True),
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

# .results triggers flush — user approves steps 1-2 in the Docent UI, then results come back
# [0] because the array_agg query returns a single row with all summaries
clusters = propose_clusters.results[0].output
assert clusters is not None
categories = clusters["categories"]
categories.append({"name": "success", "description": "Agent completed the task correctly"})
category_names: list[str] = [c["name"] for c in categories]
category_descriptions = "\n".join(f"  - {c['name']}: {c['description']}" for c in categories)
print(f"Proposed {len(category_names)} clusters: {', '.join(category_names)}")
```

**Stop here.** Run this script, review the proposed clusters, and report them to the user. If the clusters look right, proceed to Phase 2. If not, adjust the summarization prompt or sample and re-run. Re-running is free for unchanged steps (results are cached).

**If something goes wrong:** Check DQL query syntax first (see `dql-reference.md` quirks). Common issues: missing `is_list=True` on aggregated columns, or no rows returned by the sample query. If the clusters are too broad or too narrow, adjust the number of requested categories in the Step 2 prompt or focus the summarization prompt on a more specific aspect of behavior.

### Phase 2: Classify using the proposed clusters

Add this to the end of the same script file, below the `print` statement:

```python
# Step 3: Assign each transcript to a cluster
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
```

Run the extended script. Steps 1-2 are cached and won't re-run — only Step 3 executes. The user approves the classification step, and results come back.

## Example: hierarchical synthesis

When synthesizing more than ~30 reading results into a single analysis, do NOT put all results into one prompt. Instead:

1. **Batch**: Split results into groups of 15-20 using DQL (e.g., `LIMIT 20 OFFSET 0`, `LIMIT 20 OFFSET 20`, etc.)
2. **Summarize each batch**: Run a synthesis reading per batch that produces a structured intermediate summary
3. **Final synthesis**: Aggregate the batch summaries (which are now ~5-10 items) into a single final reading

Alternatively, if the per-item readings produce structured output (e.g., categories/enums), use DQL aggregation over `reading_results.output` to produce counts and distributions — this avoids context limits entirely and gives exact numbers.

---
name: report
description: Docent is a platform for analyzing AI agent behavior. Use this skill anytime you want to create a report from a Docent analysis.
alwaysApply: true
---

# Docent Report Guide

**The goal of a Docent report is to make every claim verifiable.** The reader should be able to trace any number, pattern, or conclusion back to the exact DQL query, reading result, or transcript that produced it. A report is not a summary of what the agent found — it is a structured document where data-backed components do the talking, and narrative prose interprets them.

## When to use reports

This skill is the default next step after a completed analysis workflow unless the user explicitly opts out of report generation.

Use the report feature when:
* The analysis session is complete (readings have run, results are available)
* The user wants a shareable artifact beyond CLI output
* The findings need to be reviewed by someone who wasn't present for the analysis

Do NOT use reports as a substitute for the analysis itself. First run the analysis using the Docent analysis skill, then generate the report from the results.

**Preconditions:**
- Reports are created from reading plans. If there is no reading plan ID, tell the user they need to provide one.
- The user should be fairly clear about what they want the report to cover. If the scope, question, or audience is not clear enough to operationalize, ask before drafting.
- Unless the user specifies another location, write the report markdown file in the current working directory.

## Principles

These should shape every decision about what to include and how to structure the report.

### Quality bar

The point of a report is to surface highly verifiable, traceable, actionable, and important insights for readers who are trying to make consequential decisions about agent behavior.

- **Verifiable**: every meaningful claim should be backed by adjacent evidence, such as a DQL table, a reading result embed, or a citation to the exact underlying object.
- **Traceable**: a reader should be able to follow a claim back to the exact reading plan, step, result, DQL query, or transcript that supports it.
- **Important**: focus on findings that are consequential for the user's terminal goal, such as improving performance, reducing unsafe behavior, or making some other important behavior change. Findings that happen only a tiny fraction of the time are usually not report-worthy unless the user explicitly says they matter.
- **Actionable**: recommendations must be specific enough to imply an intervention the user can make to the agent. Only include them when there is a strong, coherent, and sound argument that the intervention should improve the observed behavior.

Avoid generic summaries, isolated anecdotes, and speculative recommendations. The report should help a reader decide what matters and what to change.

### Claim → evidence

Every interpretive claim in the report must be **immediately followed** by the data component that supports it. Never make a quantitative claim in narrative prose without an adjacent table or reading sample that the reader can verify.

**Wrong** — claim with no adjacent evidence:
```md
Strategy differences account for 78% of head-to-head divergences, while
timeout-related issues account for 20%.
```

**Right** — claim immediately followed by its evidence:
```md
Strategy differences dominate over capability gaps in the head-to-head
comparisons, as shown in the following breakdown:

::dql-table{title="Failure type distribution" query="SELECT failure_type, COUNT(failure_type) AS count FROM (SELECT rr.output->>'failure_type' AS failure_type FROM reading_results rr JOIN reading_result_links rrl ON rrl.result_id = rr.id WHERE rrl.reading_id = 'READING_ID' AND rr.output IS NOT NULL) AS subq GROUP BY failure_type ORDER BY count DESC"}
::
```

The reader can now verify the "strategy differences dominate" claim by inspecting the table and its underlying DQL query.

### No platform jargon

Do not use platform jargon ("reading plan," "DQL," "reading result") in report prose visible to the reader. Use plain descriptions ("analysis," "query," "result"). Platform terminology is fine in shortcode attributes and developer-facing code.

---

# Report format

Reports are plain Markdown files with YAML frontmatter. The renderer supports normal GitHub-flavored markdown plus a small shortcode language for embedded widgets and inline citations.

## Frontmatter

```md
---
docent_collection_id: your-collection-id
docent_source_reading_plan_id: reading-plan-id
title: Your Report Title
---

# Your Report Title
...
```

- `docent_collection_id`, `docent_source_reading_plan_id`, and `title` are required for saving to Docent.
- `update_report_file(...)` rejects the update if the file's `docent_collection_id` or `docent_source_reading_plan_id` does not match the persisted report.
- Pass `report_id` and `expected_revision` explicitly to `update_report_file(...)`. They are not read from frontmatter.

## Shortcode syntax

Block shortcodes embed widgets. Inline shortcodes (citations) go inside prose.

### Block syntax

```md
::shortcode-name{key="value" other_key="value"}
Body content
can span multiple lines
::
```

Rules:
- Start every block shortcode at column 1. Do not indent it.
- Close every block shortcode with a line that is exactly `::`.
- Use only `key="value"` attributes with double quotes. Single quotes and unquoted values are not parsed.
- Do not nest block shortcodes inside other shortcode bodies.
- Do not invent IDs. If a reading result ID, transcript ID, or agent run ID is unknown, ask for it or leave a clearly labeled placeholder.
- Unsupported block shortcode names are left as normal markdown text.

### Standard markdown behavior

- Normal markdown is rendered with `react-markdown` and `remark-gfm`.
- Headings `#` through `####` appear in the table of contents.
- Links to `#anchors` stay in-page; other links open in a new tab.
- Inline citations work inside paragraphs, lists, blockquotes, and table cells.
- Inline citations are stripped from links, headings, and table headers.
- Inline citations do not render inside code blocks or inline code.
- HTML shortcode bodies are rendered as raw `iframe srcDoc`, not markdown.

---

# Shortcode reference

Available block shortcodes: `callout`, `reading-result`, `reading-results-table`, `dql-table`, `html`. Available inline shortcode: `citation`.

## `::callout`

Use for highlighted narrative content — warnings, caveats, summaries, or recommendations.

```md
::callout{color="orange" title="Heads Up"}
This is a **callout** with normal markdown inside it.
::
```

Attributes:
- `color`: optional. Allowed: `blue`, `green`, `orange`, `red`, `indigo`, `purple`. Defaults to `blue`.
- `title`: optional. Defaults to `Note`.

Body: interpreted as normal markdown. Keep callouts short and opinionated.

## `::reading-result`

Use for embedding a single reading result as qualitative evidence.

```md
::reading-result{id="reading-result-uuid" title="Example Result"}
Optional markdown note above the embedded result.
::
```

Attributes:
- `id` (or `result_id`): reading result UUID.
- `title`: optional. Defaults to `Reading Result`.

Behavior: Uses the page's `collection_id` automatically. The block exposes a `View details` action that opens the reading result panel.

Authoring guidance: Add 1-3 sentences of context above the embed. Use for qualitative evidence, not large batches.

## `::reading-results-table`

Use for embedding the full results table for a specific reading.

```md
::reading-results-table{reading_id="reading-uuid" title="Example Results"}
Optional markdown note above the embedded results table.
::
```

Attributes:
- `reading_id` (or `id`): reading UUID.
- `title`: optional. Defaults to `Reading Results Table`.

Behavior: Uses the page's `collection_id` automatically. Shows paginated results; clicking a row opens the reading result panel.

Authoring guidance: Use when the full batch is the evidence. Prefer `::reading-result` when one result suffices.

## `::dql-table`

Use for executing DQL and embedding a result table.

```md
::dql-table{title="Recent Runs" query="SELECT id, model_name FROM (SELECT id, metadata_json->>'model_name' AS model_name FROM agent_runs) AS subq LIMIT 10"}
Optional markdown note above the table.
::
```

Attributes:
- `query` (or `dql`): DQL string.
- `title`: optional. Defaults to `DQL Table`.

Behavior: Uses the page's `collection_id` automatically. Shows row count, execution time, truncation info, and a toggle to show/hide the raw DQL.

Authoring guidance:
- Keep queries short, explicit, and cheap. Add `LIMIT` unless the full result set is needed.
- Use the body to explain why this table matters, not to restate column names.
- **Key pattern**: aggregate reading results via DQL rather than stating numbers in prose. A `::dql-table` computing a distribution is always preferable to "52% are X" in text, because the reader can inspect the query.

## `::html`

Use for self-contained HTML embeds when markdown plus existing widgets are not enough.

```md
::html{title="Chart Preview" height="320"}
<div id="chart"></div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  const ctx = document.createElement('canvas');
  document.getElementById('chart')?.appendChild(ctx);
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['A', 'B', 'C'],
      datasets: [{ data: [4, 7, 5] }],
    },
  });
</script>
::
```

Attributes:
- `title`: optional. If omitted, no visible label.
- `height` (or `minHeight`, `min_height`, `min-height`): initial height in pixels. Default `360`, clamped to `0..2400`.

Body: raw HTML passed to `iframe srcDoc` (not markdown). The iframe uses `sandbox="allow-scripts"`. Parent page styles and React state are not available.

## Inline `::citation`

Use inline citations inside markdown sentences to link claims to specific evidence.

```md
This claim is grounded in ::citation{type="reading_result" collection_id="collection-uuid" reading_result_id="reading-result-uuid"}.
```

Use `short="true"` for a compact icon-only citation:

```md
See ::citation{type="analysis_result" collection_id="collection-uuid" result_set_id="result-set-uuid" result_id="result-uuid" short="true"} for details.
```

Rules:
- This is inline text, not a block shortcode.
- `short="true"` renders a quote icon instead of full citation text.
- Invalid citations render an `Invalid citation` badge.
- **Inline citations require an explicit `collection_id` attribute.** Block shortcodes use the page's collection automatically — do not add `collection_id` to them.

### Citation targeting modes

**Shortcut** — pass a full citation ID:
```md
::citation{id="full-citation-id"}
```

**Explicit** — pass `type`, `collection_id`, and type-specific fields:

| Type | Required fields | Optional fields |
|---|---|---|
| `analysis_result` | `result_set_id`, `result_id` | |
| `reading_result` | `reading_result_id` | |
| `block_content` | `agent_run_id`, `transcript_id` | `block_idx` (default `0`), `content_idx` |
| `agent_run_metadata` | `agent_run_id`, `metadata_key` | |
| `transcript_metadata` | `agent_run_id`, `transcript_id`, `metadata_key` | |
| `block_metadata` | `agent_run_id`, `transcript_id`, `metadata_key` | `block_idx` (default `0`) |

Optional text-range fields (for highlighting a quoted span): `start_pattern`, `end_pattern`, `target_start_idx`, `target_end_idx`.

Use inline citations sparingly — they are most valuable for anchoring specific qualitative claims to specific transcripts. For quantitative claims, prefer `::dql-table`.

---

# Authoring patterns

A strong report usually follows this shape:

1. Start with a single-`#` H1 at the very top, then a short intro. The UI renders pill-style links to the collection and reading plan beneath the H1 using the frontmatter IDs — you do not need to author those links.
2. Follow the intro with headings and short narrative that states a question or claim.
3. Put the supporting `::dql-table`, `::reading-result`, `::reading-results-table`, and/or inline citations immediately next to that claim.
4. Use `::callout` for a key takeaway, caveat, or recommendation only when adjacent evidence already supports it.
5. Use `::dql-table` for quantitative evidence, `::reading-result` for a single qualitative example, and `::reading-results-table` when the batch itself is the evidence.
6. Use inline `::citation` for claims that depend on a specific transcript, result, or metadata target.
7. Use `::html` only when markdown plus existing widgets are not enough.
8. Prefer a few consequential sections over a long dump of weak or low-prevalence observations.

## Report structure template

```md
---
docent_collection_id: <collection-id>
docent_source_reading_plan_id: <reading-plan-id>
title: <Report Title>
---

# Report Title

Brief overview of the analysis question and approach.

## Section Title
Interpretive claim about the data...

::dql-table{title="Evidence for claim" query="SELECT ..."}
::

Another claim supported by qualitative evidence...

::reading-result{id="reading-result-uuid" title="Representative example"}
Brief framing of what this result shows.
::

## Another Section
...

## Recommendations
Each recommendation references a specific table or reading above.

::callout{color="green" title="Recommendation"}
Specific, actionable recommendation grounded in the evidence above.
::
```

---

# Data gathering and persistence

Reference material for getting data into the report and saving it to Docent.

## MCP endpoints

- `get_reading_plan_results(collection_id, plan_name)` — reading plan overview with step statuses and result counts.
- `get_reading_plan_results(collection_id, plan_name, step_name)` — concrete outputs for a specific step.
- `get_metadata_fields(collection_id)` — helps when you need tables grouped or filtered by run metadata.
- `list_reading_presets(collection_id, owned_only=True)` — useful when a report needs to contextualize preset-backed readings. Set `owned_only=False` to inspect all collection presets.

`get_reading_plan_results` is keyed by `plan_name`, not `plan_id`. If the user gives only a plan ID, use the SDK to fetch the plan first and recover the name.

## SDK methods

- `client.list_reading_plans(collection_id, name=..., owned_only=True)` — find matching reading plans. Pass `owned_only=False` to search all visible plans.
- `client.get_reading_plan(collection_id, plan_id)` — full plan with step metadata, reading IDs, DQL step definitions.
- `client.get_reading_results(collection_id, reading_id)` — raw reading results for qualitative inspection.
- `client.execute_dql(collection_id, dql, reading_plan_id=plan_id)` plus `client.dql_result_to_dicts(...)` — materialize DQL-backed evidence tied to the plan.
- `client.query(...)` — supplemental quantitative support. Keep the report anchored to the cited reading plan.

## Persisting reports

The recommended workflow: draft the report as a local Markdown file with YAML frontmatter, save it to Docent, then recover the persisted report ID via lookup when you need an update.

**SDK methods:**
- `client.save_report_file(path)` — create a persisted report from a local Markdown file.
- `client.update_report_file(path, report_id=..., expected_revision=...)` — update a persisted report.
- `client.get_report(collection_id, report_id)` — fetch a persisted report.
- `client.list_reports(collection_id, source_reading_plan_id=..., prefix=..., owned_only=True)` — list reports. Pass `owned_only=False` to search all visible reports.
- `client.open_report(collection_id, report_id)` — open the persisted report UI.

**MCP endpoints:**
- `save_report_file(path)` — create a persisted report.
- `update_report_file(path, report_id, expected_revision)` — update a persisted report.
- `get_report(collection_id, report_id)` — fetch a persisted report.
- `list_reports(collection_id, source_reading_plan_id=None, prefix=None, owned_only=True)` — list reports.

**After creating or updating**, open the report in the browser. If you have the report ID, call `client.open_report(collection_id, report_id)` directly. Otherwise, recover it via report lookup first.

### Recovering report IDs for updates

Report markdown files do not persist `report_id` or `revision` in frontmatter.

1. Read `docent_collection_id`, `docent_source_reading_plan_id`, and `title` from frontmatter.
2. Use `list_reports(collection_id, source_reading_plan_id=..., prefix=title, owned_only=True)`.
3. If exactly one match: use its `id` and `revision` with `update_report_file(...)`.
4. If multiple matches: inspect returned IDs, revisions, owners, `updated_at` — ask the user to disambiguate unless the target is obvious.
5. If no matches: use `save_report_file(path)` instead.

## Looking up reading IDs

Many DQL queries over reading results require the `reading_id`. To find it:

```python
plans = client.list_reading_plans(collection_id)
plan = [p for p in plans if p["name"] == "My Plan"][0]
detail = client.get_reading_plan(collection_id, plan["plan_id"])
for step in detail["steps"]:
    print(f'{step["alias"]}: {step["name"]} -> {step.get("reading_id")}')
```

Store reading IDs as constants at the top of the report script so they're easy to find and update.

## Querying reading result fields

Reading results have two important JSON columns:
* `output` — the LLM's structured output (matches `output_schema` from the reading)
* `arguments_dict` — the input arguments (agent run refs, text values, etc.)

Access patterns:
```sql
-- Structured output field
rr.output->>'failure_category'

-- Nested output field
rr.output->'scores'->>'accuracy'

-- Input argument (plain string)
rr.arguments_dict->>'task_name'

-- Input argument (context ref)
rr.arguments_dict->'agent_run'->>'id'
```

Always verify the actual structure of `arguments_dict` before writing DQL — arguments can be plain strings or nested objects depending on the reading definition. Inspect with:

```python
results = client.get_reading_results(collection_id, reading_id)
print(results[0]["arguments_dict"])
print(results[0]["output"])
```

For more background on Docent analysis workflows, see `./analysis.md`.

---

# Common mistakes

### Hardcoding numbers in prose

**Wrong**: `"78% of failures are strategy differences"`
**Right**: A `::dql-table` that computes the percentage, with prose saying "strategy differences are the dominant failure type, as shown below"

The moment you type a number in a markdown section, ask yourself: is there a DQL query that produces this number? If yes, use a `::dql-table` instead.

### Orphaned evidence

**Wrong**: A `::dql-table` sitting alone with no narrative explaining what the reader should take from it.
**Right**: A brief interpretive sentence before the table explaining what claim it supports, and optionally a sentence after explaining what the data shows.

### Shortcode syntax errors

- Do not indent block shortcodes under list items or blockquotes — they will not parse.
- Do not use single-quoted attributes like `title='foo'`.
- Do not omit the closing `::`.
- Do not put block shortcodes inside another shortcode body.
- Do not expect block shortcodes to work inside HTML embeds.
- Do not rely on inline citations inside code fences or inline code.
- Do not add `collection_id` to block shortcodes — they use the page's collection automatically. Do include `collection_id` on inline `::citation` shortcodes.
- Do not omit `LIMIT` in `::dql-table` queries unless the full result set is genuinely needed.

### Other mistakes

- Do not start a report without a reading plan ID.
- Do not guess the report scope when the user's request is not clear enough.
- Do not elevate a vanishingly rare edge case into a headline finding unless the user explicitly cares about it.
- Do not recommend interventions unless you can explain why that intervention should improve the observed behavior.

## Showing literal shortcode syntax

The block parser is line-based. Raw block shortcode lines can be interpreted even inside a fenced code example. To show literal shortcode syntax in a report:

- Indent the shortcode lines inside the code fence so they do not start at column 1.
- Replace the leading `::` with escaped or entity text.

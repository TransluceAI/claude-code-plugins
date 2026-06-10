---
name: ingestion
description: Structured workflow for ingesting agent run data into Docent. Use when the user wants to upload evaluation logs or agent transcripts to Docent. Triggers on phrases like "ingest into Docent", "upload to Docent", "import runs to Docent", or when working with agent evaluation data that needs to be loaded into Docent for analysis.
---

# Docent Ingestion Skill

Use this workflow to convert local transcripts, agent logs, or evaluation traces into Docent `AgentRun` data and upload them to a Docent collection.

Keep the main workflow lightweight. Load `./ingestion-reference.md` only when you need concrete SDK examples, conversion snippets, source-inspection helpers, or examples for Inspect AI, tool calls, pass@k, branching, or multi-agent data.

## Core Rules

- Work in four stages: context, planning, ingestion, verification.
- Create and maintain `ingestion-plan.md` in the working directory.
- Do not upload until the user confirms the proposed collection name, Docent hierarchy, field mappings, and omitted data.
- Never silently skip source data. Any file or field not ingested must be documented with a reason and expected impact.
- Save ingestion code to a file such as `ingest.py` or `ingest_<collection_name>.py`; do not rely on one-off inline Python for the final upload path.
- Use `parse_chat_message` from the Docent SDK for transcript messages, and make deliberate role mappings when the source roles differ from Docent's supported roles.
- Run deterministic `AgentRun` sanity checks before upload and resolve obvious conversion problems.

## When Triggered

If the user asks to "ingest", "upload", "import", or "move" traces, transcripts, or eval logs into Docent, briefly offer this structured workflow:

1. Gather context and credentials.
2. Inspect the data and propose a Docent organization.
3. Write and run an ingestion script.
4. Verify uploaded counts and warnings.

If the user accepts or directly asks you to proceed, start Stage 1. If they decline, work freeform.

## Stage 1: Context

Before Python work, use an existing virtual environment if present. If no environment is active and `docent-python` is unavailable, ask before installing it.

Collect only what is needed to plan:

- API key: prefer `$DOCENT_API_KEY` or an SDK-discovered config file. The default global file is `~/.docent/docent.env`; project-level `docent.env` files are supported as local overrides.
- Data path: the file or directory to ingest.
- Optional context: what produced the data and what analysis the user wants to do in Docent.

Create `ingestion-plan.md` with this compact structure and append findings as the workflow proceeds:

```markdown
# Docent Ingestion Plan

## Configuration
- Data path:
- API key source:

## Source Analysis
- File structure:
- Detected formats:
- Expected source record count:

## Docent Model Orientation
- Documentation reviewed:
- Important SDK/model assumptions:

## Proposed Docent Structure
- Collection:
- AgentRun unit:
- TranscriptGroup usage:
- Transcript usage:

## Field Mapping
| Source | Docent target | Notes |
| --- | --- | --- |

## Omitted Data
| Field/File | Reason | Impact |
| --- | --- | --- |

## Confirmation
- Collection name:
- Data context:
- Analysis goals:
- User confirmed:

## Execution Log

## Verification
- Source records:
- Converted:
- Failed conversions:
- Uploaded:
- Sanity warnings:
- Collection URL:
```

## Stage 2: Planning

### Orient on Docent Models

Before designing the ingestion shape, review the ingestion-side SDK models and docs:

- Online SDK documentation: https://docs.transluce.org/llms.txt
- Local examples and snippets, as needed: `./ingestion-reference.md`

At minimum, understand:

- `Collection`, `AgentRun`, `TranscriptGroup`, and `Transcript`
- Message classes, `parse_chat_message`, supported roles, tool calls, and tool responses
- How the source represents reasoning, such as visible reasoning text, structured
  summaries, opaque blobs, or split assistant fragments
- Where structured values belong: usually `AgentRun.metadata`, `Transcript.metadata`, scores, identifiers, and grouping fields
- ID behavior: the SDK assigns `AgentRun` IDs automatically

### Analyze Source Data

Inspect the data path enough to identify the repeatable unit that should become an `AgentRun`.

Look for:

- Directory organization: experiment, model, checkpoint, date, task, sample, attempt, phase
- File formats: JSON, JSONL, Inspect `.eval`, logs, configs, metadata files
- Repeated templates: the same set of files or folders repeated across samples or experiments
- Transcript fields: `messages`, `conversation`, `dialogue`, `turns`, `traj`, `trajectory`
- Score and result fields: `score`, `reward`, `accuracy`, `correct`, `success`, `metric`, `result`
- Identifiers and grouping keys: `task_id`, `sample_id`, `episode`, `run_id`, `uuid`
- Special structures: pass@k attempts, tree/branching traces, multi-agent episodes, tool call sequences

If Inspect `.eval` files are present, prefer the built-in Inspect loader. For mixed or unclear data, summarize your best interpretation and ask the user to confirm before coding.

### Propose Docent Structure

Most Docent analysis features, including rubrics, search, and clustering, operate at the `AgentRun` level. Structure data so each `AgentRun` is a meaningful analysis unit.

| Level | Use |
| --- | --- |
| `Collection` | One experiment, benchmark run, dataset, or cohesive ingestion batch |
| `AgentRun` | The primary item to analyze, compare, search, label, or score |
| `TranscriptGroup` | Attempts or phases within one `AgentRun`, such as pass@k |
| `Transcript` | One conversation history; use multiple transcripts for multi-agent runs |

Default: if unsure, make each independent task, episode, sample, or branch its own `AgentRun` with one `Transcript`.

For tree or branching data, usually ingest each branch as its own `AgentRun` and use metadata such as `root_task_id`, `branch_id`, `parent_branch_id`, and `branch_depth` to preserve relationships.

### Confirmation Gate

Before writing the final upload script, present the plan and wait for user confirmation. Include:

- Source structure and detected data type
- Proposed collection name
- Proposed `Collection` / `AgentRun` / `TranscriptGroup` / `Transcript` structure
- Key field mappings for messages, scores, identifiers, and metadata
- Any omitted files or fields, with reason and impact
- Expected source record count, if available
- Your understanding of the data context and analysis goals

## Stage 3: Ingestion

For Inspect `.eval` files, use the built-in loader and proceed directly to sanity checks. See `./ingestion-reference.md` for the import pattern.

For custom data:

1. Write an ingestion script to the filesystem.
2. Load raw source records according to the confirmed file structure.
3. Convert a small sample into `AgentRun` objects.
4. Manually inspect sample turns with reasoning and tool calls to verify reasoning
   was represented, merged, or intentionally omitted according to the plan.
5. Fix sample conversion issues.
6. Convert the full dataset and record conversion failures.
7. Run `check_agent_runs(agent_runs)` and inspect the formatted report.
8. Upload only after the conversion output and warnings match the confirmed plan.

If a failure is not easily recoverable, such as unexpected data shape, authentication failure, API error, or ambiguous SDK error, stop and ask the user how they want to proceed. Include the exact error and the affected file or record when possible.

### Sanity Checks

`check_agent_runs` warnings are not necessarily schema errors, but they often reveal conversion mistakes. Fix warnings caused by data shaping. For warnings that may be legitimate, summarize categories, counts, and representative examples, then ask whether they are expected.

Deterministic checks do not fully validate reasoning handling. Inspect source
reasoning during sample conversion, especially when the source stores reasoning
outside normal assistant text or splits reasoning from the answer/tool-call turn.

Document any accepted warnings in `ingestion-plan.md` with counts and justification.

## Stage 4: Verification

After upload, verify and log:

- Source records discovered
- Records converted successfully
- Conversion failures and representative errors
- Agent runs uploaded to Docent
- Whether source, converted, and uploaded counts match expectations
- Any accepted sanity warnings
- Collection URL

If the SDK cannot verify the uploaded count, provide the collection URL and record that manual verification is needed.

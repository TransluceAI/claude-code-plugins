# Docent Ingestion Reference

Load this file only when you need concrete code or detailed patterns while following `./ingestion.md`.

## Source Discovery Helpers

Use these snippets as starting points. Adapt them to the source layout instead of treating them as required framework code.

```python
from collections import Counter
from pathlib import Path


def build_folder_tree(path: str, max_depth: int = 5) -> dict | None:
    path_obj = Path(path)

    def recurse(current: Path, depth: int) -> dict | None:
        if depth > max_depth or not current.is_dir():
            return None

        children = {}
        file_extensions = Counter()

        for item in sorted(current.iterdir()):
            if item.is_dir():
                children[item.name] = recurse(item, depth + 1)
            else:
                file_extensions[item.suffix.lower() or "no_ext"] += 1

        return {
            "children": children,
            "file_counts": dict(file_extensions),
            "total_files": sum(file_extensions.values()),
        }

    return recurse(path_obj, 0)


def find_repeatable_template(tree: dict) -> dict:
    def signature(node: dict | None) -> tuple:
        if node is None:
            return ()
        child_names = tuple(sorted(node.get("children", {}).keys()))
        file_exts = tuple(sorted(node.get("file_counts", {}).keys()))
        return (child_names, file_exts)

    signatures = {}

    def collect(node: dict | None, path: str = "") -> None:
        if node is None:
            return
        sig = signature(node)
        signatures.setdefault(sig, []).append(path)
        for name, child in node.get("children", {}).items():
            collect(child, f"{path}/{name}")

    collect(tree)
    repeated = [(sig, paths) for sig, paths in signatures.items() if len(paths) > 1 and sig[0]]
    if not repeated:
        return {"template_structure": None, "note": "No repeating pattern found"}

    repeated.sort(key=lambda item: len(item[1]), reverse=True)
    return {
        "template_structure": repeated[0][0],
        "instance_count": len(repeated[0][1]),
        "example_paths": repeated[0][1][:3],
    }


def detect_inspect_files(path: Path) -> list[str]:
    return [str(file) for file in path.rglob("*.eval")]
```

```python
from pathlib import Path


def sample_files_strategically(path: Path, template_info: dict) -> list[Path]:
    samples = []

    for instance_path in template_info.get("example_paths", [])[:2]:
        instance = path / instance_path.lstrip("/")
        for subdir in ["trajs", "trajectories", "logs", "results", ""]:
            candidate = instance / subdir if subdir else instance
            if candidate.exists():
                samples.extend(list(candidate.glob("*.json"))[:1])
                samples.extend(list(candidate.glob("*.jsonl"))[:1])
                if samples:
                    break

    if not samples:
        samples = list(path.rglob("*.json"))[:3] + list(path.rglob("*.jsonl"))[:2]

    return samples[:5]
```

```python
def infer_json_schema(data: dict | list, max_depth: int = 5) -> dict:
    if max_depth == 0:
        return {"type": "any", "note": "truncated"}

    if isinstance(data, dict):
        return {
            "type": "object",
            "fields": {
                key: infer_json_schema(value, max_depth - 1)
                for key, value in data.items()
            },
        }

    if isinstance(data, list):
        if not data:
            return {"type": "array", "items": "unknown"}
        item_schemas = [infer_json_schema(item, max_depth - 1) for item in data[:3]]
        return {"type": "array", "items": item_schemas[0], "sample_count": len(data)}

    return {"type": type(data).__name__, "example": repr(data)[:100]}
```

## Inspect AI Logs

When `.eval` files are detected, prefer the built-in loader:

```python
from inspect_ai.log import read_eval_log
from docent.loaders.load_inspect import load_inspect_log

eval_log = read_eval_log("path/to/file.eval")
agent_runs = load_inspect_log(eval_log)
print(f"Loaded {len(agent_runs)} runs from Inspect log")
```

## Transcript Sanity Check Warnings

`check_agent_runs`, `check_agent_run`, `check_transcript`, and `check_messages`
return warning-level `TranscriptCheck` objects. They do not reject data by
themselves, but ingestion scripts should treat them as conversion errors unless
the warning category is explicitly understood, documented in the ingestion plan,
and accepted by the user.

All possible warning codes from `docent.data_models.chat.checks`:

| Code | When it appears | Fix or acceptance guidance |
| --- | --- | --- |
| `empty_message` | A message has no visible text, structured reasoning, assistant tool calls, or tool error. | Drop source noise, or preserve omitted source data in metadata if it is important. |
| `system_message_after_conversation_start` | A system message appears after a user, assistant, or tool turn. | Move setup text into the initial system prompt, or document that the source intentionally changes instructions mid-run. |
| `conversation_starts_with_tool_message` | The first non-system message is a tool response. | Check whether the assistant tool call was omitted or split into another transcript. |
| `consecutive_assistant_messages` | Two assistant messages are adjacent. | Usually merge adjacent assistant text, reasoning blocks, and tool calls into one assistant message unless the split is intentional. |
| `consecutive_user_messages` | Two user messages are adjacent. | Check whether they are separate conversations, or merge them if the source represents one user turn in fragments. |
| `assistant_tool_calls_interrupted` | A non-tool message appears before all previous assistant tool calls receive tool responses. | Place tool responses immediately after the assistant message that requested them, before the next user or assistant turn. |
| `missing_tool_response` | An assistant tool call never receives a matching tool response by the end of the transcript. | Add a tool message with the same `tool_call_id`, or document why the source lacks the response. |
| `reasoning_embedded_as_text` | Assistant text contains reasoning markers such as `<reasoning>`, `<thinking>`, `reasoning:`, or `thinking:` but has no structured reasoning content block. | Move reasoning into `{"type": "reasoning", "reasoning": ...}` and keep user-visible answer text in `{"type": "text", "text": ...}`. |
| `tool_call_missing_id` | An assistant tool call has a blank `id`. | Populate a stable id so the corresponding tool message can refer to it via `tool_call_id`. |
| `tool_call_missing_function` | An assistant tool call has an id but a blank function name. | Populate the tool function name if it exists in the source data. |
| `duplicate_tool_call_id_in_assistant_message` | One assistant message contains the same tool call id more than once. | Use unique tool call ids within each assistant turn. |
| `duplicate_tool_call_id` | A tool call id was already emitted by an earlier assistant message in the same transcript. | Preserve source ids only when they are globally unique per transcript; otherwise generate stable unique ids during conversion. |
| `tool_response_missing_id` | A tool message has a blank `tool_call_id`. | Set `tool_call_id` to the id of the assistant tool call that produced the response. |
| `orphan_tool_response` | A tool message references a `tool_call_id` that no previous assistant tool call emitted. | Check whether the assistant tool call was omitted, assigned a different id, or split into another transcript. |
| `duplicate_tool_response` | Multiple tool messages respond to the same `tool_call_id`. | Keep one tool response per tool call unless the source intentionally streams partial tool outputs. |
| `tool_response_function_mismatch` | A tool message function name does not match the function name on the referenced assistant tool call. | Use the function name from the assistant tool call, or document a source-specific reason for the mismatch. |

## Base Ingestion Script Shape

Use this shape for custom data. Fill in `load_data` and `convert_to_agent_run` based on the confirmed plan.

```python
import os
from pathlib import Path
from typing import Any

from docent import Docent
from docent.data_models import AgentRun, Transcript
from docent.data_models.chat import (
    check_agent_runs,
    format_check_report,
    parse_chat_message,
)


DATA_PATH = Path("path/to/data")
COLLECTION_NAME = "collection-name"
DOCENT_API_KEY = os.environ["DOCENT_API_KEY"]


def load_data(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    # Implement according to the confirmed source structure.
    return records


def convert_to_agent_run(record: dict[str, Any]) -> AgentRun:
    raw_messages = record.get("messages") or record.get("traj") or []
    messages = [parse_chat_message(message) for message in raw_messages]

    transcript = Transcript(
        messages=messages,
        metadata={},  # transcript-level fields from the mapping
    )

    return AgentRun(
        transcripts=[transcript],
        metadata={
            # scores, identifiers, grouping fields, and other mapped metadata
        },
    )


raw_data = load_data(DATA_PATH)
print(f"Loaded {len(raw_data)} source records")

sample_errors = []
for index, record in enumerate(raw_data[:10]):
    try:
        convert_to_agent_run(record)
    except Exception as exc:
        sample_errors.append({"index": index, "error": str(exc)})

if sample_errors:
    raise RuntimeError(f"Sample conversion failed: {sample_errors[:5]}")

agent_runs = []
conversion_errors = []
for index, record in enumerate(raw_data):
    try:
        agent_runs.append(convert_to_agent_run(record))
    except Exception as exc:
        conversion_errors.append({"index": index, "error": str(exc)})

print(f"Converted {len(agent_runs)}/{len(raw_data)} source records")
if conversion_errors:
    raise RuntimeError(
        "Full conversion had failures. Fix or explicitly document every skipped "
        f"source record before upload. Examples: {conversion_errors[:5]}"
    )

sanity_report = check_agent_runs(agent_runs)
print(format_check_report(sanity_report))
if sanity_report.has_warnings:
    raise RuntimeError(
        "AgentRun sanity checks produced warnings. Fix conversion problems, or "
        "document accepted warning categories in ingestion-plan.md and confirm "
        "with the user before upload."
    )

client = Docent(api_key=DOCENT_API_KEY)
collection_id = client.create_collection(name=COLLECTION_NAME, description="")
upload_result = client.add_agent_runs(collection_id, agent_runs)
print(upload_result)
print(f"https://docent.transluce.org/collection/{collection_id}")
```

## Message Parsing

Prefer `parse_chat_message` for dictionaries:

```python
from docent.data_models.chat import parse_chat_message

user_msg = parse_chat_message({"role": "user", "content": "What is 2+2?"})
assistant_msg = parse_chat_message({"role": "assistant", "content": "The answer is 4."})
system_msg = parse_chat_message({"role": "system", "content": "You are helpful."})
```

Direct construction is also available when you need precise control:

```python
from docent.data_models.chat import AssistantMessage, SystemMessage, UserMessage

user_msg = UserMessage(content="Hello")
assistant_msg = AssistantMessage(content="Hi", model="gpt-4")
system_msg = SystemMessage(content="You are helpful.")
```

## Reasoning Handling

Pay attention to reasoning during source analysis and sample conversion.
Deterministic sanity checks catch obvious structural issues such as adjacent
assistant messages and embedded reasoning markers, but they cannot decide
whether a source's reasoning stream was represented correctly.

- Use `ContentReasoning` for visible reasoning summaries when the source exposes
  them, and place those blocks on the same `AssistantMessage` as the answer text
  and tool calls they belong to.
- If the source splits reasoning into separate assistant fragments, merge those
  fragments into the following assistant message unless the split is semantically
  intentional.
- Do not dump opaque or encrypted reasoning into user-visible text. Omit it or
  preserve source-level counts/metadata, then document the omission in
  `ingestion-plan.md`.
- During the sample conversion pass, inspect reasoning and tool-call turns
  manually and record any accepted omissions or source-specific handling.

```python
from docent.data_models.chat import AssistantMessage, ContentReasoning, ContentText

assistant_msg = AssistantMessage(
    content=[
        ContentReasoning(reasoning="The model's visible reasoning summary."),
        ContentText(text="The answer shown to the user."),
    ],
)
```

## Tool Calls

Normalize raw tool calls before parsing messages if the source format differs from Docent's expected shape.

```python
from docent.data_models.chat import AssistantMessage, ToolCall, ToolMessage

assistant_msg = AssistantMessage(
    content="Let me search for that.",
    tool_calls=[
        ToolCall(
            id="call_123",
            function="web_search",
            arguments={"query": "weather today"},
            type="function",
        )
    ],
)

tool_msg = ToolMessage(
    content="Sunny, 72F",
    tool_call_id="call_123",
    function="web_search",
)
```

```python
from typing import Any

from docent.data_models.chat import ToolCall


def parse_tool_calls(raw_calls: list[dict[str, Any]]) -> list[ToolCall]:
    calls = []
    for index, raw_call in enumerate(raw_calls):
        function_payload = raw_call.get("function", {})
        calls.append(
            ToolCall(
                id=raw_call.get("id", f"call_{index}"),
                function=function_payload.get("name", raw_call.get("name", "")),
                arguments=function_payload.get(
                    "arguments",
                    raw_call.get("arguments", {}),
                ),
                type="function",
            )
        )
    return calls
```

## Simple Flat Records

```python
from typing import Any

from docent.data_models import AgentRun, Transcript
from docent.data_models.chat import parse_chat_message


def convert_simple(record: dict[str, Any]) -> AgentRun:
    messages = [parse_chat_message(message) for message in record["messages"]]
    metadata = {key: value for key, value in record.items() if key != "messages"}
    metadata["scores"] = {"reward": record.get("reward", 0)}

    return AgentRun(
        transcripts=[Transcript(messages=messages)],
        metadata=metadata,
    )
```

## Pass@k Evaluation

Use `TranscriptGroup` for attempts that belong to the same task-level `AgentRun`.

```python
from typing import Any

from docent.data_models import AgentRun, Transcript, TranscriptGroup
from docent.data_models.chat import parse_chat_message


def convert_pass_at_k(task_data: dict[str, Any]) -> AgentRun:
    agent_run = AgentRun(
        transcripts=[Transcript(messages=[])],
        metadata={"task_id": task_data["task_id"]},
    )

    groups = []
    transcripts = []

    for index, attempt in enumerate(task_data["attempts"]):
        group = TranscriptGroup(
            name=f"Attempt {index + 1}",
            agent_run_id=agent_run.id,
            metadata={"k": index},
        )
        groups.append(group)

        transcript = Transcript(
            messages=[parse_chat_message(message) for message in attempt["messages"]],
            transcript_group_id=group.id,
            metadata={"attempt": index},
        )
        transcripts.append(transcript)

    agent_run.transcripts = transcripts
    agent_run.transcript_groups = groups
    return agent_run
```

## Tree Or Branching Data

Usually ingest each branch as its own `AgentRun`. Preserve tree structure in metadata.

```python
from docent.data_models import AgentRun

agent_run = AgentRun(
    transcripts=[transcript],
    metadata={
        "root_task_id": "task_123",
        "branch_id": "branch_a_1",
        "parent_branch_id": "branch_a",
        "branch_depth": 2,
    },
)
```

## Multi-Agent Data

Use one `Transcript` per agent in the same `AgentRun` when the agents share one episode-level outcome.

```python
from docent.data_models import AgentRun, Transcript

agent_run = AgentRun(
    transcripts=[
        Transcript(messages=agent_1_messages, metadata={"agent_id": "agent_1"}),
        Transcript(messages=agent_2_messages, metadata={"agent_id": "agent_2"}),
    ],
    metadata={
        "episode_id": "episode_42",
        "scores": {"joint_reward": 0.85},
    },
)
```

## Verification Snippet

Prefer an SDK or API count when available. If count keys differ across SDK versions, log the raw collection details and manually verify the collection page.

```python
collection_info = client.get_collection(collection_id)
print(collection_info)

uploaded_count = None
if collection_info:
    for key in ["agent_run_count", "num_agent_runs", "n_agent_runs", "total_runs"]:
        if key in collection_info:
            uploaded_count = collection_info[key]
            break

print("VERIFICATION REPORT")
print(f"Source records: {len(raw_data)}")
print(f"Converted: {len(agent_runs)}")
print(f"Failed conversions: {len(conversion_errors)}")
print(f"Uploaded count: {uploaded_count if uploaded_count is not None else 'unknown'}")
print(f"Collection URL: https://docent.transluce.org/dashboard/{collection_id}")
```

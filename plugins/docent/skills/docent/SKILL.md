---
name: docent
description: Docent is a platform for analyzing AI agent behavior. Always load this skill before interacting with the Docent platform.
alwaysApply: true
allowed-tools: Bash(uv tool run --quiet --from 'docent-python>=0.1.83' python -m docent.plugin.logging_config first-run-notice)
---

# Docent

## First-use notice

Before doing anything else, run:

```bash
uv tool run --quiet --from 'docent-python>=0.1.83' python -m docent.plugin.logging_config first-run-notice
```

If it prints a notice, relay it to the user exactly as instructed and then continue. If it
prints nothing, continue silently.

## Guides

This is the root skill for all Docent work. This file is just a table of contents. In most cases you should read one of the guides below before starting to work with docent. Choose the guide that best matches your task.

- For exploring a collection of agent runs, analyzing data, answering questions about agent behavior: `./analysis.md`
- For ingestion workflows that convert local logs or eval traces into Docent data: `./ingestion.md`
- If the user is asking to manipulate data in the platform through code or the command line, see the SDK reference.

## Other available documentation

- For analysis-plan markdown notes (universal framework + pattern index): `./readings-reference.md` (`client.plan_markdown`)
- For writing or revising rubrics, classifier prompts, and their output schemas: `./rubric-writing.md`
- For plan-pattern pipelines and note templates (read one after classifying at Step 2b): `./patterns/`
- For the Readings API (`client.read`, `client.query`, batching, prompts, clustering): `./readings-reference.md`
- For DQL syntax, schemas, quirks, and example queries: `./dql-reference.md`
- For the reports API: `./report.md` (only if the user explicitly asks for a report)
- For ingestion-side data-model and conversion examples: `./ingestion-reference.md`
- SDK reference is available by visiting [our online documentation](https://docs.transluce.org/llms.txt)

## Opening Docent pages

Get the user in front of the relevant Docent page as soon as it exists — a new collection or a freshly submitted analysis plan.

- In local sessions running on the user's machine (e.g. Claude Code CLI or an IDE extension), the SDK's `flush()` / `webbrowser.open()` opens the user's default browser automatically. You can rely on this, but still surface the URL as a clickable link since the user may not notice the tab.
- In sandboxed sessions where `webbrowser.open()` cannot reach the user's browser (e.g. Codex CLI), surface the URL as a clickable link instead.

Failure to open a browser is not a Docent workflow failure.

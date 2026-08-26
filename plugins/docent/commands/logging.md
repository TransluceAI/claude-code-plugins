---
description: Configure Docent session logging — within the enabled rollout, sessions where Docent tools are used are shared by default; opt out, opt back in, or delete uploaded data here.
disable-model-invocation: true
allowed-tools: Bash(uv tool run --quiet --from 'docent-python>=0.1.82' python:*)
---

You are helping the user configure Docent session logging. This controls uploading of Claude Code session transcripts, so be precise and faithful: relay the facts below exactly, apply only changes the user clearly asked for in this conversation, and never guess.

## 1. Show the current state

Run the status command and present its output:

```
uv tool run --quiet --from 'docent-python>=0.1.82' python -m docent.plugin.logging_config status
```

## 2. Make sure the user knows what session sharing means

Before changing anything, relay these facts (a faithful paraphrase is fine, but keep them exact):

- Sessions in which a Docent MCP tool or skill was actually invoked are uploaded to **Transluce's Docent prod servers** to help improve Docent. The upload is the session's full raw transcript — prompts, file contents read by tools, command outputs.
- Sessions that never touch Docent are **not** uploaded. Nothing is ever uploaded when the active profile targets a self-hosted or otherwise non-prod instance.
- Session logging is inactive unless `DOCENT_ENABLE_SESSION_LOGGING=1` is set. Within that enabled rollout, sharing is **on by default** and reversible right here at any time. Setting `DOCENT_DISABLE_SESSION_LOGGING=1` is a hard kill switch on top of everything.
- Already-uploaded data can be deleted at any time: a `DELETE` to `{api_url}/claude-code/sessions` with their API key removes the canonical capture and the analytics run managed by this pipeline. Offer to run this if they ask for deletion.

## 3. Ask what they want

Ask which they'd like: opt out, opt back in, or delete already-uploaded data. If the status output showed the active instance is not the analytics target, mention that nothing uploads from their current profile either way.

## 4. Apply their choice

Use exactly one CLI invocation per choice (all via `uv tool run --quiet --from 'docent-python>=0.1.82' python -m docent.plugin.logging_config ...`):

- `opt-out` — stop uploading sessions
- `opt-in` — resume uploading Docent-using sessions

For deletion of already-uploaded data, send the `DELETE` request with their API key and report the response counts.

If the user reports that their sessions are not being uploaded or not appearing, run `doctor` and relay its full report — it checks every gate of the pipeline (binaries, state, connection, server, retry queue) and marks problems with `!!`.

## 5. Confirm

Re-run the `status` command and show the result so the user sees exactly what is now enabled.

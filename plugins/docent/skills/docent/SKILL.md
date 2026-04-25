---
name: docent
description: Unified skill for the Docent AI platform. Includes instructions on how to analyze, report on, and ingest AI agent runs, as well as API references.
alwaysApply: true
---

# Docent

This is the root skill for all Docent work. Use it whenever the user wants to analyze runs, ingest data, create or update reports, or look up how the Docent SDK works.

## Choose the right guide

- For analyzing or answering questions about agent runs, exploring collections, creating new reports on a topic: `./analysis.md`
- For ingestion workflows that convert local logs or eval traces into Docent data: `./ingestion.md`
- If the user is asking to manipulate data in the platform through code or the command line, see the SDK reference.

## API references

- For the Readings API (`client.read`, `client.query`, batching, prompts, clustering): `./readings-reference.md`
- For DQL syntax, schemas, quirks, and example queries: `./dql-reference.md`
- For the reports API: `./report.md`
- For ingestion-side data-model and conversion examples: the reference and pattern sections in `./ingestion.md`
- SDK reference is available by visiting [our online documentation](https://docs.transluce.org/llms.txt)

Open only the sibling docs that match the user's task; do not load everything by default.

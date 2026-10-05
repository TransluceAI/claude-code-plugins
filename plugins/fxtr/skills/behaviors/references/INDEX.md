# The behaviors documentation

The pages of https://docs.transluce.ai/behaviors, copied with this skill: `provenance.json`,
beside its `SKILL.md`, says from which version. Each is listed with what it covers,
in the order of the site's navigation.

## Get started

- [Introduction](index.mdx): Primitives for evaluating AI model behavior.

## Other pages

- [Choosing models](guides/choosing-models.mdx): Find the exact model IDs a provider offers your account, pick the adapter for its endpoint, and check a model before a sweep.
- [Conversation records and checkpoints](guides/conversation-records.mdx): What a rollout records, how conversations are stored as fxtr entities and flattened into transcripts, and how to checkpoint a session.
- [Docent readings](guides/docent-readings.mdx): Convert conversations to Docent's data models, and run a Docent reading against a transcript or agent run with a model you choose.
- [Calling language models](guides/language-models.mdx): Use the behaviors library to hold conversations and judge outputs in fxtr steps.
- [Policies and tools](guides/policies-and-tools.mdx): Decide what the model sees each turn: scripted users, tool policies, their combinations, and custom conversation flows.
- [Rollout outcomes and retries](guides/rollout-outcomes.mdx): How a rollout ends, how model call failures are retried, recorded, or raised, and how to watch a rollout as it runs.
- [API overview](reference/api.mdx): The layers of behaviors, where each is imported from, the provider adapters, and the request, response, and sampling types.

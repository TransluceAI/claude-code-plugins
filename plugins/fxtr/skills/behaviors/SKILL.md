---
name: behaviors
description: Call language models from fxtr experiments with the behaviors Python library, covering one-shot requests and judge steps, multi-turn chat rollouts, scripted or custom user and tool policies, retries and failures, streaming, checkpoints, and storing conversations. Use whenever a fxtr experiment calls a model or holds a conversation, or when extending behaviors' model adapters or policies.
---

# behaviors

behaviors is a Python library for calling language models from fxtr experiments: provider
adapters, conversation sessions, context policies that play users and tools, retries and failure
recording, and conversation records stored as fxtr entities. Use these pieces when they fit the
experiment, rather than building another chat loop or transcript format.

The pages below are its documentation. Read the ones a task needs before writing code.

## Where to read

| Task                                                                                                                           | Read                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| Add behaviors to a project; hold a conversation, judge outputs, and summarize verdicts in fxtr steps; test without credentials | [Calling language models](references/guides/language-models.mdx)                   |
| Pick a provider, an adapter, and an exact model ID                                                                             | [Choosing models](references/guides/choosing-models.mdx)                           |
| Script users, offer tools, or write a custom conversation flow                                                                 | [Policies and tools](references/guides/policies-and-tools.mdx)                     |
| Rollout statuses and `max_turns`, failures, retries, streaming                                                                 | [Rollout outcomes and retries](references/guides/rollout-outcomes.mdx)             |
| Messages and content, stored records, transcripts, conversations in the viewer, checkpoints                                    | [Conversation records and checkpoints](references/guides/conversation-records.mdx) |
| Run Docent readings, or convert records for Docent                                                                             | [Docent readings](references/guides/docent-readings.mdx)                           |
| Choose a layer; imports, adapters, sampling settings, requests and responses                                                   | [API overview](references/reference/api.mdx)                                       |
| Steps, workflows, arrays, launching jobs, and the step cache                                                                   | the adjacent [fxtr skill](../fxtr/SKILL.md)                                        |

## Best practices

* **Judge with `gpt-6-luna` by default.** For an LLM judge, use `gpt-6-luna` through the
  `OpenAIResponsesAPI` adapter, unless the user asks for another model.
* **Keep the model the user names.** Verify its exact ID from the provider's listing, as Choosing
  models shows, rather than substituting another. Without credentials to check, take candidate
  IDs from the provider's published catalog, and tell the user that account access has not been
  verified.
* **Shape model experiments as the guide does**: one step per conversation, with every setting
  that affects the request in a configuration entity; fxtr replicas for repeated samples; and
  separate steps for judging and for aggregating verdicts.

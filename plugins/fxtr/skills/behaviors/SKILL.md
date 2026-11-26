---
name: behaviors
description: Call language models from fxtr experiments with the behaviors Python library, covering one-shot requests and judge steps, multi-turn chat rollouts, scripted, model-simulated, or custom users and tool policies, retries and failures, streaming, checkpoints, and storing conversations, and running code in containers on Docker, Modal, or AWS. Use whenever a fxtr experiment calls a model, holds a conversation, or needs a container or sandbox to run code in, or when extending behaviors' model adapters or policies.
---

# behaviors

behaviors is a Python library for calling language models from fxtr experiments: provider
adapters, conversation sessions, context policies that play users and tools, retries and failure
recording, and conversation records stored as fxtr entities. It also starts containers to run
code in, on the user's Docker daemon, on Modal, or on AWS. Use these pieces when they fit the
experiment, rather than building another chat loop, transcript format, or container wrapper.

The pages below are its documentation. Read the ones a task needs before writing code.

## Where to read

| Task                                                                                                                                                                                     | Read                                                                                    |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Add behaviors to a project; hold a conversation, judge outputs, and summarize verdicts in fxtr steps; test without credentials                                                           | [Calling language models](references/guides/language-models.mdx)                        |
| Pick a provider, an adapter, and an exact model ID                                                                                                                                       | [Choosing models](references/guides/choosing-models.mdx)                                |
| Script users or simulate them with models (a base model, steered by a pilot), offer tools, or write a custom conversation flow                                                           | [Policies and tools](references/guides/policies-and-tools.mdx)                          |
| What each provider's dialect carries, adaptation losses and refusing them, structured output (`response_format`, strict tools, tool output schemas), refusals and other stops, codecs    | [Dialects and adaptation](references/guides/dialects-and-adaptation.mdx)                |
| Rollout statuses and `max_turns`, failures, retries, streaming                                                                                                                           | [Rollout outcomes and retries](references/guides/rollout-outcomes.mdx)                  |
| Messages and content, stored records, transcripts, conversations in the viewer, checkpoints                                                                                              | [Conversation records and checkpoints](references/guides/conversation-records.mdx)      |
| Convert records for Docent                                                                                                                                                               | [Converting to Docent](references/guides/conversation-records.mdx#converting-to-docent) |
| Start containers (one, or several that talk to each other) on the user's Docker daemon, on Modal, or on AWS (EC2), run code in them and move files, allow internet access, set lifetimes | [Running code in containers](references/guides/sandboxes.mdx)                           |
| Choose a layer; imports, adapters (including Gemini and OpenRouter) and their options, model providers, sampling, reasoning and speed settings, requests and responses                   | [API overview](references/reference/api.mdx)                                            |
| Steps, workflows, arrays, launching jobs, and the step cache                                                                                                                             | the adjacent [fxtr skill](../fxtr/SKILL.md)                                             |

## Best practices

* **Judge with `gpt-6-luna` by default.** For an LLM judge, use `gpt-6-luna` through the
  `OpenAIResponsesAPI` adapter, unless the user asks for another model.
* **Keep the model the user names.** Verify its exact ID from the provider's listing, as Choosing
  models shows, rather than substituting another. Without credentials to check, take candidate
  IDs from the provider's published catalog, and tell the user that account access has not been
  verified.
* **Make each argument of a model call its own step input.** Then every result points at the
  exact settings that produced it, and the cache sees every setting. Hard-code nothing that
  affects a request in a step.
  * The model is a `model_name` string, such as `openai/gpt-6-luna`. The project's own
    `make_api(model_name)` builds the `ModelAPI` from it, and the step closes the API in
    `finally`. The string is the record of which model was called: a `Judgment` holds none.
  * Sampling is a `SamplingParamsEntity` the project defines, a frozen `DataclassEntity` with one
    field, `params: SamplingParams`. An fxtr array can't hold a `SamplingParams` as a value, but
    it can hold a reference to an entity. behaviors provides no such type.
  * A prompt, a rubric, the judge's instructions, and an output schema (as JSON text) are
    `TextEntity` inputs.
* **Shape model experiments as the guide does**: one step per conversation; fxtr replicas for
  repeated samples; and separate steps for transcripts, judging, and aggregating judgments.
* **Judge with behaviors' `judge`**, from `behaviors.judging.judge`, which returns a `Judgment`.
  Write its output schema with a `behaviors.judging.schemas` function (`binary_schema`,
  `continuous_schema`, `categorical_schema`, `structured_schema`). Each starts with a
  `discussion`, so the judge explains before it decides. For the instructions, start from
  `DEFAULT_SYSTEM_INSTRUCTIONS_ENTITY`, from `behaviors.judging.defaults`. `judge` needs
  `jsonschema`, which a project adds itself: `uv add "behaviors[models]" jsonschema`.
* **Point at evidence with a citation, not a number.** When a judge's answer has to name a place
  in an entity (the message where a behavior first appears, the line a score rests on), make that
  field a citation field, written by a `CustomFormat`'s `schema` method, and ask for exactly one
  citation, or an empty string when there is none. The viewer draws such a field as a link that opens the entity at that place. An integer
  index is drawn as a bare number.
* **Link a judge's call output first.** When you link the user to one call of a judge step, add
  `section_order=output_first` to its `invocation` view, so the judgment shows above the
  transcript and rubric it was given:
  `p=invocation(/judge,item=0127,judge=sonnet,section_order=output_first)`.
* **Use as many citation fields as the answer needs.** One schema can have several, and they need
  not be checked the same way: each way is a `CustomFormat` with a name of its own, which writes
  its field with `schema(description=...)` and is passed to `judge` in `custom_formats` (lines in
  a discussion, a whole message in a field that points at one). See
  [Citations](references/reference/api.mdx#citations).
* **Say where a new citation format's addresses open.** When you define a `CustomFormat` whose
  addresses name places in an entity, give it `viewer_params`, so links that cite it open the
  viewer at that place rather than at the whole entity, and register it in the
  `fxtr.citation_formats` entry points. See the `custom_formats` entry in
  [the API reference](references/reference/api.mdx).

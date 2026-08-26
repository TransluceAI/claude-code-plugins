# Rubric Writing Reference

Read this before writing or revising a Docent rubric, rubric-like classifier prompt, output schema, or analysis step that asks an LLM judge to make a structured behavioral decision.

## Goal

You are helping the user turn a vague idea of a behavior they are looking for in a dataset of AI agent run transcripts into a concrete specification of what they are looking for.

## Canonical rubric components

The following rules govern how you should write rubrics and their schemas:

A rubric must contain exactly these components:

- One paragraph with an insightful high-level framing that makes the ensuing specification highly simple and parsimonious. Usually, this requires identifying the correct abstractions and decision principles.
- A decision procedure, specified as a natural-language decision tree, that anyone can follow to determine whether a transcript contains instances of a behavior. The procedure must be specific, unambiguous, and consistent: multiple humans should be able to agree on the outcome.
- An output schema, specified as JSON Schema, that describes the output of the decision procedure.

## Rubric-writing rules

- The level of specificity and detail in the decision procedure should be commensurate with the amount of information available to you. If the user has only provided a vague one-line statement, there is no need to overfit to a complex rubric.
- It's extremely important that the decision procedure is concise, simple, and clear. Each natural language predicate or decision point is an opportunity for ambiguity.
- It must be explicitly explained which output values correspond to which decisions.
- Unless otherwise stated, revisions to existing complex rubrics should be as minimal and targeted as possible. Do not make gratuitous changes to wording unless absolutely necessary. As you generate each line of the revision, consult the last version of the rubric and consider whether your planned change is strictly necessary; if not, rewrite it exactly as it was before.

## Output schema rules

- If unspecified, keep the rubric schema as simple as possible, but of course include what the user requests.
- The output schema must conform to Docent's restricted subset of JSON Schema 2020-12.
- Keep the schema aligned with the decision procedure. Every top-level field should be produced by a stated decision in the rubric.
- For match/no-match rubrics, prefer a small enum such as `["match", "no match"]` plus an explanation field with citations when the analysis needs evidence.
- Do not create speculative category enums during first-pass extraction or exploratory scans. If the possible categories are not already known from the user request or prior analysis, use free-text fields for the observed behavior and defer any taxonomy or enum until after reviewing extracted examples.
- If the user asks for something that could have intensity, add an integer enum field with values 0-10.

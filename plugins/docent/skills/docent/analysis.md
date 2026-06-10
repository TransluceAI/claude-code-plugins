---
name: analysis
description: Docent is a platform for analyzing AI agent behavior. Use this skill anytime you want to use Docent to analyze AI agent behavior.
alwaysApply: true
---

# Docent Analysis Guide

**The goal of a Docent analysis is to give the user justifiable trust in the results.** The user should have clear insight into what the analysis is doing and why it is being run. This is accomplished through two channels:
* **Communication via the command line.** Explain what you found, what you plan to do, and why — before writing code. Surface blockers and intermediate findings in plain language. The user should never be left watching scripts run with no understanding of the analysis taking shape.
* **Analysis plans in the Docent UI.** Analysis plans make the analysis legible: the user can see every prompt sent to the LLM, every transcript analyzed, and every result returned — with citations back to the source material. (Note: you may see references to "reading plans", which is an outdated term for analysis plans. They're the same thing.)

You can interact with Docent by writing Python scripts that use the Docent SDK, and by calling Docent MCP tools. If Docent MCP tools are not available, alert the user that the Docent MCP server is not installed correctly.

## Principles

These apply throughout the entire analysis session:

* **Keep the user in the driver's seat on analytical choices.** You choose implementation details (query syntax, script structure). The user chooses analytical direction (which dimensions, what thresholds, which comparisons). When you're about to embed an analytical choice in code — a threshold, a sampling strategy, a decision about which rubrics matter — that's a signal to explain the choice and let the user redirect before you commit. Proposing a direction is good; proposing and immediately executing is not. The difference is whether you stop.
* **The user's understanding of the analysis should match reality — continuously, not just at the end.** At every point in the session, could the user accurately describe what has happened so far? If they'd say "the agent just ran a fresh analysis" when it actually replayed cached results, something is wrong. If they'd say "that concern was checked" when it was hand-waved, something is wrong. If they'd say "I can verify these claims" but can't find the link, something is wrong. This applies to provenance (cached vs. fresh), methodology (why these choices), scope (sample vs. complete), and inspectability (where to check the evidence).
* **Provide value early and continuously.** The user came to analyze data, not to watch you set up. Share what you're learning as you learn it — one sentence after each query is enough. Don't accumulate findings silently for a big reveal later.
* **Explain your reasoning before each step, not just results after.** Before running a query or script, tell the user *what* you're about to do and *why* — the analytical reasoning, not just "let me check X." The user should understand your analytical approach well enough to redirect it before you run the code.

  Bad — narrates the action without reasoning:
  > "Let me check the safety scores across models."

  Good — explains the analytical choice so the user can redirect:
  > "Safety-monitoring is the broadest single safety indicator and it's scored for every run, so I'll use that as the primary ranking. I'll sample the 25 worst-scoring transcripts — enough to see patterns without blowing the analysis budget. If you'd rather focus on a specific failure type like co-rumination, we can narrow the filter."
* **Minimize wasted user attention.** Keep inline scripts short (under ~15 lines) so the user can read and approve them at a glance. For anything longer, write a named script file — the user then approves a short `uv run script_name.py` command instead of scrolling through 60 lines of inline Python. Run orientation queries independently (not in a monolithic script that fails as a unit). Fix syntax errors in-place rather than requiring an edit-rerun approval loop.
* **Avoid unnecessary docent-internal jargon.** The user is here to understand their data, not to learn Docent internals.
  - "flush" → never mention to the user
  - "DQL" / "DQL query" → "query," or just describe what you're checking
  - "template reading" / "scripted reading" → never mention; these are implementation details
  - "orientation queries" → "exploring the data" or "checking the numbers"
  - "multi-approval flow" → "this analysis has two phases — you'll need to approve each one"
  - "metadata fields" / "metadata_json" → describe the actual content ("model name", "safety scores")

  The deeper rule: **describe what you're investigating, not what tools you're running.** Most jargon leaks happen when you narrate your own tool use to the user. The user doesn't need to know which system you're querying or what the query language is called — they need to know what you're learning about their data.

  Bad — narrates tool use:
  > "Let me run DQL queries to aggregate the metadata fields and check the score distributions across models."

  Good — narrates the investigation:
  > "Let me check how the models compare on safety scores — I'll look at the averages and the distribution of failures."
* **Surface blocking errors to the user immediately.** If a script fails on permissions, unexpected data, or a problem you can't fix in one retry, tell the user what happened and why before attempting a fix. Don't silently retry multiple times — the user loses trust when they can't see what's going on.
* **Don't raise concerns and then drop them.** If you notice a potential data integrity issue (e.g., "these score columns might be keyed by judge model, not subject model"), resolve it before proceeding — run a quick verification query, check the metadata, or ask the user. Raising a concern, saying "let me verify," and then continuing without verifying is worse than not noticing: the user now has false confidence that the issue was checked.

## Data models and key concepts
* A transcript is a sequence of messages from the system, the agent (aka assistant), the user, and/or tools that the agent calls.
* An agent run represents an AI agent attempting a task or interacting with a user. An agent run may contain one or more transcripts.
* A collection contains agent runs from a certain experiment or benchmark. When we query, analyze, or compare agent runs, we do so within one collection at a time.

## SDK basics and getting oriented
The Docent SDK can be installed via `docent-python` (e.g., `uv add docent-python`).

```python
from docent.sdk.client import Docent
client = Docent()
```

If the user provides a dashboard URL, you can create a client directly from it:
```python
client = Docent.from_url("https://docent.transluce.org/dashboard/668354d8-...")
```
This parses the domain and collection ID from the URL automatically.

The Docent SDK can be configured by a `docent.env` file. The default global config file is `~/.docent/docent.env`. The SDK also honors project-level `docent.env` files from the current working directory upward as local overrides. You do not need to explicitly source `docent.env`. Config files may use INI-style `[section]` headers for multi-profile support; select a profile with `Docent(profile="my-profile")` or the `DOCENT_PROFILE` environment variable.

If you're not sure what collection the user is talking about:
* If the user provides a Docent dashboard URL (e.g., `https://docent.transluce.org/dashboard/668354d8-...`), use `Docent.from_url()` or extract the collection ID from the last path segment (the UUID).
* Otherwise, check the SDK-discovered `docent.env` file for `DOCENT_COLLECTION_ID`.
* If neither is available, ask the user to paste the collection UUID.

The main Docent deployment lives at https://docent.transluce.org but the user may connect a different deployment by overriding DOCENT_FRONTEND_URL in docent.env. The Docent SDK will print out the frontend URL when it is initialized, e.g. `Authenticating Docent client with frontend_url='https://docent.transluce.org'`. If you see a different frontend URL, use that URL in place of `https://docent.transluce.org` for any links.

## Troubleshooting

If you run into any issues or unexpected behavior with the Docent platform, pause and alert the user. Do not try to work around them autonomously.

* If authentication fails (HTTP 401) or no API key is configured, walk the user through setup:
  1. Open the API keys page for them: `open https://docent.transluce.org/settings/api-keys` (macOS) or `xdg-open https://docent.transluce.org/settings/api-keys` (Linux).
  2. Ask them to create a new API key (it will start with `dk_`).
  3. Write the key to `~/.docent/docent.env`: `DOCENT_API_KEY=dk_...` (plus `DOCENT_API_URL` and `DOCENT_FRONTEND_URL` if not using the default instance). Use a project-level `docent.env` only when the project needs a local override.
  4. Verify connectivity by constructing a `Docent()` client — the constructor validates the API key automatically.
* If the SDK does not match what's documented here, check whether the SDK is up to date.
* If the Docent MCP server is available but doesn't match the tools documented here, check whether the MCP server needs an upgrade (`uv tool upgrade docent`). If an upgrade was needed, ask the user to restart the session or MCP server.
* Use the `get_reading_plan_results` MCP tool to inspect the results of an analysis. Call it with just `collection_id` and `plan_name` to see an overview of all steps and their statuses. Call it with an additional `step_name` to see the actual results for a specific step.
* **When debugging, try first, ask second.** If the user asks you to debug a failed analysis and gives you a plan name, collection ID, or other identifying info, attempt the lookup immediately with whatever you have. A failed tool call is instant, informative, and free — it tells you exactly what went wrong. Asking the user to confirm inputs before trying adds a round-trip that produces nothing the tool call wouldn't have revealed faster. If the lookup fails, *then* ask for corrections with the error context in hand.

## Linking to content in the Docent UI

When the user asks to see something in the Docent UI, or when you want to point the user at specific content, **construct a direct URL** rather than writing a script to extract and redisplay the content. The Docent frontend supports deep links to most content types.

| Content | URL pattern |
|---|---|
| Collection dashboard | `https://docent.transluce.org/dashboard/{collection_id}` |
| Agent run | `https://docent.transluce.org/dashboard/{collection_id}/agent_run/{agent_run_id}` |
| Agent run at specific transcript/block | Same as above + `?transcript_idx={N}&block_idx={M}` |
| Analysis plan | `https://docent.transluce.org/dashboard/{collection_id}/analysis-plan/{reading_plan_id}` |

**When to use UI links instead of scripts:**
* The user asks to "see" or "browse" something (e.g., rubric definitions, specific transcripts, judge outputs) — link them directly rather than extracting content into the terminal.
* You want the user to inspect specific evidence — provide the URL so they can drill in.
* You're presenting analysis findings — include the analysis plan URL so the user can verify claims.

**How to find IDs for constructing URLs:** Use `execute_dql` MCP tool queries against the relevant tables (`agent_runs`, `transcripts`, `judge_results`, `readings`, etc.) to look up IDs, then construct the URL.

## Overview of analysis tools and terminology

DQL is a read-only subset of DQL that you can use to query agent runs in the docent database. DQL is useful for quantitative analysis of agent run metadata (e.g. which model gets the highest average score). DQL should never be used to inspect transcript content. Read ./dql-reference.md before using DQL.

A reading is a structured batch of LLM calls. Readings are useful for qualitative analysis of agent run content (e.g. what mistakes is the agent making, how is it interacting with the user). Use readings instead of inspecting transcript content directly. See details in ./readings-reference.md.

An analysis script is a Python script you write using the Docent SDK. An analysis script can perform DQL queries (client.query) and readings (client.read).

When you run an analysis script, an analysis plan is displayed in the Docent UI. Each query and reading in the script is displayed as a separate card in the analysis plan. Readings require approval from the user before they are run. Results for both step types (DQL and reading) are displayed in interactive tables.

Once you have a question where qualitative analysis is clearly required, you can go ahead and create + run an analysis script with readings. If you need the user to clarify or refine the question, do that before writing the script.

Note: the Docent UI is the primary place to view reading results. You do not need to fetch them, read them, and restate them to the user. If a summary or synthesis would be helpful, perform that as another reading in the same analysis script so it will show up in the UI. If a structured aggregation of reading results would be helpful, perform that as another DQL query in the same analysis script.

# Example workflow

This section describes the end-to-end process for a Docent analysis session.

## Step 1: Orient and brief the user

This step should feel like a brief conversation, not a long preamble. Target under 60 seconds of wall time. The user should be building understanding alongside you — not waiting for a summary at the end.

### 1a. Fetch metadata and brief the user

If the user provided a dashboard URL, use `Docent.from_url()` in all scripts throughout the session — this ensures the correct domain and collection are used regardless of what `docent.env` is configured for.

Use the `get_metadata_fields` MCP tool to understand the structure of agent run metadata for the current collection. Agent runs contain metadata that varies by collection — do not make assumptions about its structure.

Also call `list_reading_presets` to check if the collection has any saved reading presets. These can be reused and are worth knowing about before proposing analysis directions.

**Immediately after these calls return, tell the user what you see** in 2-3 sentences: what kind of data is in this collection, what the key dimensions are (e.g., models, tasks, environments), and what scores or metrics are available. This is the user's first orientation to the dataset — don't skip it, and don't jump straight into writing queries.

### 1b. Run orientation queries, reporting as you go

Read `./dql-reference.md` for detailed information on how to write DQL queries.

Explore the data with a small number of targeted queries — 2-3 is usually enough; don't write 5+ "just in case." **Always use the `execute_dql` MCP tool, never a Python script or local aggregation.** It runs read-only DQL directly without an approval round-trip. If you have a genuine reason to use Python here (e.g., chaining a couple of queries), the aggregations themselves must still go through `client.execute_dql` using `uv run python3 -c "..."`.

**Before each query, explain which metrics you chose and why** — not just "let me check scores." The user should understand your analytical reasoning well enough to redirect it before you run the query. Because they don't see the raw query output (only your reported findings), your one-line framing is the only window they have into what you're learning and why it matters.

Report each finding as you get it — one sentence per query is enough. If a query fails, fix and retry immediately; the MCP tool returns errors inline, so you can adjust without a separate approval cycle.

**When presenting numbers, always explain the scale.** Don't show a table of values without telling the user what they mean. Are these averages of binary 0/10 scores (i.e., pass rates)? Continuous scores on a 0-10 scale? Higher-is-better or higher-is-worse? If the metric names are opaque (e.g., "poetic escalation," "beneficent goal-directed tenacity"), give the user a one-line plain-language description of what each one measures. If you don't know exactly how a metric is defined, say so rather than letting the user assume your labels are precise.

**Formatting ASCII tables:**
You may format findings as ASCII tables where appropriate. Only use ASCII tables for quick, informal updates. For presenting aggregations or slices of final results, use client.query in your analysis script. For any table of individual agent runs or transcripts, use client.query. (The Docent UI makes it convenient to inspect individual transcripts, unlike an ASCII table.)
* Use plain-language column headers, not internal field names (e.g., "Co-rumination" not "avg_co_rum")
* Label the scale once (e.g., "All scores 0-10, higher = safer" or "Pass rate out of 252 runs")
* Don't bold arbitrary values without explaining the logic — if you bold the worst values, say "worst in bold"
* Include row/column context: model names, sample sizes, what each row represents

### DQL gotchas for orientation queries

* **Use the subquery pattern by default** for every query involving GROUP BY, CASE, COALESCE, or aliases on `agent_runs`. This is never wrong and avoids the most common DQL errors. See the DQL quirks section in `./dql-reference.md`.
* **Always cast to NUMERIC before ROUND.** Another common preventable error.
* It's fine to include many metrics in a single query if you're confident in the syntax. If you're less sure (e.g., unfamiliar metadata paths or complex CASE expressions), split into a couple of queries so a syntax error in one doesn't block the rest.

### Orientation query templates

These templates already incorporate DQL quirks (subquery pattern, NUMERIC cast, COUNT on column not `*`). Copy and adapt them rather than writing from scratch.

Run each query independently using the `execute_dql` MCP tool. **Adapt the metadata paths** (e.g., `model_name`, `reward`, `exception` below) based on what `get_metadata_fields` returned — these are placeholders, not universal field names.

**Dataset overview by dimension:**
```sql
SELECT model_name, COUNT(model_name) AS run_count,
       ROUND(CAST(AVG(reward) AS NUMERIC), 3) AS avg_reward
FROM (
    SELECT
        COALESCE(metadata_json->>'model_name', 'unknown') AS model_name,
        CAST(metadata_json->>'reward' AS DOUBLE PRECISION) AS reward
    FROM agent_runs
) AS subq
GROUP BY model_name
```

**Score distribution:**
```sql
SELECT reward_bucket, COUNT(reward_bucket) AS run_count
FROM (
    SELECT
        CASE
            WHEN CAST(metadata_json->>'reward' AS DOUBLE PRECISION) = 0 THEN 'zero'
            WHEN CAST(metadata_json->>'reward' AS DOUBLE PRECISION) = 1 THEN 'perfect'
            ELSE 'partial'
        END AS reward_bucket
    FROM agent_runs
) AS subq
GROUP BY reward_bucket
```

**Exception/error breakdown:**
```sql
SELECT exception, COUNT(exception) AS run_count
FROM (
    SELECT COALESCE(metadata_json->>'exception', 'none') AS exception
    FROM agent_runs
) AS subq
GROUP BY exception
ORDER BY run_count DESC
```

## Step 2: Checkpoint and design the analysis

### 2a. Checkpoint on the analysis angle

If the user has not precisely stated what analysis they want you to run, now is a good time to check in. Summarize what you learned in plain language (not raw query output) and propose 2-3 analysis directions. Let the user choose which question they want to focus on. The user needs early visibility and control over both the analytical direction and the intended deliverable.

**Stop and wait for the user to respond.** Do not propose directions and then immediately commit to one.

Bad — proposes then bulldozes:
> "Here are three directions we could take: (1) safety failures, (2) hardest scenarios, (3) empathy vs. safety tradeoff. Assuming you'd pick option 1, let me go ahead and write the analysis..."

Good — proposes and stops:
> "Here are three directions: (1) safety failures across models, (2) which scenarios trip up models the most, (3) the tension between empathy and safety. Which sounds most useful?"

Because you've been reporting findings throughout Step 1, this checkpoint should feel like a natural conclusion — not a sudden info-dump.

Tips for an effective checkpoint:
* **Use a comparison table** when the collection compares models, configurations, or conditions — tables make relative differences scannable at a glance.
* **Ground each proposed direction in something specific from the data.** Not "we could look at failure modes" but "Gemini and Grok show 3-5x higher scores on poetic escalation and lock-in — analysis could focus on what failure pattern is driving that gap and what interventions it suggests."
* **Keep it short.** The checkpoint is a decision point, not a final report. 1 paragraph of summary + 2-3 bullet-point proposals is usually right.

### 2b. Surface analytical choices and design the pipeline

This step typically happens in the same conversation turn as the user's reply to Step 2a. The user picks a direction; you respond with the analytical choices that will shape it. Don't treat this as a second separate checkpoint — it's the natural continuation of the same conversation.

**Do not skip this step.** Before writing any code, surface the 2-3 most consequential **analytical choices** in your plan and let the user weigh in. Analytical choices are things like: what metric defines "failure," what threshold separates good from bad, how you're grouping or sampling, which dimensions you're comparing. These are the decisions that determine what the analysis finds — the user needs to see them before you embed them in code.

Pipeline structure (which steps, what order, DQL vs. LLM analysis) and model choice are implementation details the user doesn't need to approve. What they need to approve is the analytical framing.

Bad — describes pipeline steps the user can't meaningfully evaluate:
> "Here's my plan: Step 1, explore scores. Step 2, summarize the 50 worst transcripts. Step 3, cluster failure modes. Step 4, classify all runs."

Good — surfaces the choices that shape what the analysis will find:
> "I'll compare models pairwise on each scenario type rather than averaging across all scenarios, because the orientation data suggests model rankings shift depending on the scenario. I'll group the 126 scenarios into ~6 thematic categories — letting the LLM propose categories from the data rather than using a fixed taxonomy. For the safety metric, I'll use safety-monitoring specifically (not a composite) since it's scored for every run and showed the clearest model separation. Want me to adjust any of those choices?"

For each piece of analytical work, decide: is this a **DQL query** (aggregation, filtering, counting), an **LLM analysis** (categorization, summarization, qualitative judgment), or **Python glue** (orchestrating queries and analyses, reformatting data)?

**The self-check:** If your plan includes substantial Python logic — statistical tests, clustering algorithms, scoring functions, classification rules — stop and reconsider. You may be planning work that should be an LLM analysis instead. The user cannot verify, inspect, or drill into results that come from opaque Python. Docent's value is inspectable analysis, not opaque computation.

#### Translating "computational" questions into the Docent pipeline

When the user asks a question that *feels* like it needs computation (grouping, statistical comparison, categorization), your instinct may be to write Python. Resist this. Instead, translate each analytical operation into the pipeline:

| The question feels like... | Use this instead |
|---|---|
| "Group/categorize these items" | LLM analysis — have the LLM read transcripts and assign categories. See the **clustering pattern** in `./readings-reference.md`. |
| "Compare across groups" | DQL aggregation over LLM analysis output (e.g., `SELECT category, model, AVG(score) ... GROUP BY category, model`). |
| "Find outliers / anomalies" | LLM analysis on the items with extreme metadata scores — have the LLM explain *why* each is unusual, with cited evidence. |
| "Account for statistical noise" | Group items to increase sample size per cell. Show sample sizes alongside aggregates so the user can judge confidence. Use LLM analysis to assess qualitative confidence when quantitative power is limited. |
| "Rank or score items" | LLM analysis with structured output (e.g., an enum or numeric scale), then DQL aggregation over the output. |
| "What's different about these runs?" | LLM analysis comparing runs, with cited evidence. Not a Python script computing feature differences. |
| "Summarize / synthesize across many items" | Hierarchical LLM synthesis — batch items into groups of 15-20, summarize each batch, then synthesize the batch summaries. See **Hierarchical synthesis** in Step 3. |
| "Is there a relationship between X and Y?" | DQL to compute per-group averages on both dimensions, then LLM analysis to interpret the pattern qualitatively with cited evidence. |

**Example — the right way to handle "which scenario types cause the biggest safety gaps between models":**

The key analytical choices here are: how to define scenario types, which safety metric to compare, and what counts as "anomalous." A good plan surfaces these:

1. **Categorize scenarios by theme** (targeting 5-8 groups — enough granularity to see patterns, few enough that each group has sufficient sample size). Let the LLM propose categories from the data rather than using a predetermined taxonomy. The user can inspect every categorization decision in the Docent UI.
2. **Compare per-category safety scores across models** using the safety-monitoring metric specifically (not a composite), since it showed the clearest model separation in orientation. Show sample sizes alongside averages so the user can judge confidence.
3. **Deep dive on the anomalous combinations** — where model rankings shift vs. the aggregate picture. Analyze those specific transcripts to explain what's happening, with cited evidence.

**What's wrong with doing this in Python instead:** Writing a script that clusters scenarios by k-means on dimension vectors, computes composite safety scores, and runs bootstrap significance tests gives the user a table they can't verify. They can't check why scenario X was grouped with scenario Y, whether the composite weighting is appropriate, or whether the statistical claims hold up. The same analysis done through the Docent pipeline gives the user inspectable LLM categorizations with cited evidence, transparent DQL aggregations, and qualitative deep dives they can drill into.

#### Present the plan to the user

Before coding, briefly describe the analytical framing — not the pipeline steps, but the choices that shape what the analysis finds. This is the moment where the user can still redirect cheaply: e.g., "actually, I already have a categorization — use the dimension scores instead," or "use co-rumination instead of safety-monitoring." Once you start writing the analysis script, redirects get more expensive, so make this framing explicit rather than burying the choices in code.

## Step 3: Write and run the analysis script

Consult `./readings-reference.md` for the Readings API, coding tips, and example patterns (especially the clustering example). Consult `./dql-reference.md` for DQL syntax, table schemas, and quirks.

Write a Python script implementing the pipeline you designed in Step 2b. Keep the script clean. Do not put exploratory queries in the analysis script — those belong in Step 1 orientation. However, you may add DQL queries to the script to present key findings (e.g. if an important reading outputs categories, you could count the frequency of each category). Do this sparingly, only when it will help the user understand the findings beyond seeing a table of reading results.

If you feel the urge to write substantial Python logic (clustering, scoring, statistical tests), go back to the **translation table in Step 2b** and express the work as LLM analyses and DQL aggregations instead.

### Validate before submitting

Before running your first analysis script against a collection:

1. **Test every DQL query in the script** using `execute_dql()` first. DQL has non-obvious restrictions (no `DISTINCT ON`, no `SELECT *`, no `COUNT(*)`). A query that fails inside an analysis wastes an approval round-trip. Validate queries in a quick inline script before embedding them in an analysis script.
2. **Run one script first as a canary.** If you have multiple analysis scripts, run one first and confirm it submits successfully before running the rest. This catches permission errors, query issues, and submission failures before they multiply across all scripts.
3. **Estimate whether synthesis steps will fit in context.** If a synthesis step aggregates N results via `array_agg()`, and N > 30, the combined input will likely exceed the model's context or output limits. Use hierarchical synthesis instead (see below).
4. **Estimate total LLM call volume before you submit.** After all filtering and reshaping is done, check how many per-item analyses the reading would actually run. If the plan would trigger more than 1,000 LLM calls, stop and ask the user to confirm before submitting it. Be explicit that this is likely expensive, state the estimated call count, and offer a cheaper fallback such as running the same analysis on a 100-item subsample first.

### Build incrementally

A phase is one analytical step: summarize, cluster, classify, compare. Each phase becomes a separate run-and-review cycle. Write the first phase of your script (e.g., summarize transcripts + propose clusters), run it, confirm it works and report the intermediate results to the user. Then extend the script with the next phase and run again — earlier steps are cached and won't re-run. See the phased clustering example in `./readings-reference.md` for this pattern.

Do not write a script covering all phases at once. A monolithic script that fails on line 50 wastes all the work after it and forces a full debug-edit-rerun cycle. Worse, you spend your entire turn budget debugging DQL syntax instead of delivering results. The phased approach means each run is short, each failure is isolated, and the user sees intermediate progress.

### Running and communicating

Analysis plans appear in a web UI for the user to approve — this is a key control affordance. You are responsible for running analysis scripts when appropriate; the user should not have to do so manually. Prefer to run analysis scripts in the background, so that you can still communicate with the user if the script pauses to wait for approval.

**Surface the Docent UI link as soon as the analysis is submitted** — don't wait until results come back. The SDK's `flush()` opens a browser tab, but the user may not notice or may lose it among other tabs. Always tell the user explicitly: "The analysis is running — you can follow along and approve it here: [link]." This is especially important because the link is how the user inspects the evidence behind every finding.

**Be explicit about partial data.** When `get_reading_plan_results` returns truncated output (e.g., 50 of 132 results visible), state the exact fraction you saw and caveat derived numbers. Prefer using query aggregation over `reading_results.output` to get complete counts rather than parsing truncated tool output. For example, to get the full distribution of a structured output field across all results, query `reading_results` directly:

```sql
SELECT category, COUNT(category) AS cnt
FROM (
    SELECT rr.output->>'failure_category' AS category
    FROM reading_results rr
    JOIN reading_result_links rrl ON rrl.result_id = rr.id
    WHERE rrl.reading_id = '<reading-uuid>'
) AS subq
GROUP BY category
ORDER BY cnt DESC
```

## Critical workflow rules

These are specific rules that follow from the principles above. They apply throughout the analysis:

* **Never present opaque Python computation as analysis results.** Orientation queries (Step 1) are for *your* understanding and can use `execute_dql()` and local Python. But once you move past orientation into actual analysis (Step 3), findings must go through Docent's inspectable pipeline — DQL query steps visible in the UI and analysis-plan readings with citable evidence. If the user's question requires categorization, comparison, or synthesis, use Docent analyses, not a Python script that outputs a table. The user has no way to verify, inspect, or drill into results that come from opaque code. Metadata aggregations via DQL are acceptable as supporting context (e.g., counts, averages), but the analytical conclusions should come from inspectable analyses the user can review in the Docent UI.
* **Don't fall back to manual synthesis when an analysis step fails.** If a synthesis step fails (e.g., context overflow), fix the analysis design (batch it, sample it, use structured aggregation) and re-submit. Do not absorb the synthesis work into opaque Python scripts or agent-side summarization — this defeats the core value of Docent's inspectable, citable analysis. If you must do agent-side aggregation as a stopgap (e.g., counting structured output fields via a query), explicitly flag to the user that this step is not inspectable in the Docent UI and offer to re-run it properly.
* If the user asks you to "read the agent runs", "summarize 10 transcripts", "classify the results", or similar, that not mean that you (the coding agent) should do so directly. Prefer to do this in an analysis plan using readings.
* **Be transparent about reused work.** This has two parts:
  - **Existing scripts:** If you find an analysis script already on disk from a prior session, don't silently reuse or overwrite it. Tell the user what it does, what analytical choices are embedded in it (thresholds, sample sizes, which dimensions), and ask whether to reuse it or write a fresh one.
  - **Cached results:** After `flush()` returns, check the output for cache indicators (e.g., "cached (5 results)" in step status). If results came back cached, tell the user immediately: "These results are from a prior session — I'm pulling existing results rather than re-running. Want me to force a fresh analysis?" Do not narrate cached results as if you just computed them. The user needs to know whether they're looking at fresh work or replayed results.
* When referring to analysis steps (e.g., in error messages or status updates), use the step's display name so the user can find it in the UI.

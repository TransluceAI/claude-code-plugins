---
name: first-experiment
description: Walk someone new to fxtr through their first experiment with language models, from their own question to results in the viewer. The user proposes a question about model behavior; you help scope it, design it with them, set up the project, write the experiment with behaviors, run a small pilot and then the full run, and change it with their input. Use when the user asks for a walkthrough, tutorial, or guided start with fxtr, asks for help with their first fxtr experiment, or invokes this skill. For later work in a project they already know, use the fxtr and behaviors skills instead.
---

# Your first experiment

You are guiding someone through their first fxtr experiment. They bring the question; you help
them turn it into an experiment that calls language models, build it, run it, and read what it
found, explaining the fxtr ideas as each one comes up. By the end they should have results they
care about and know where each part of the experiment lives, so they can change it themselves.

This skill sets the order of the work and when to check in with the user. How to write each part
is in the adjacent [fxtr skill](../fxtr/SKILL.md) and [behaviors skill](../behaviors/SKILL.md):
read the pages they point to for each task, and follow their best practices.
[Your first experiment](../fxtr/references/first-experiment.mdx) shows an example of a first
experiment. By default you should follow along with this example, but if the user has a different
question they want to study or decides to deviate from the example in some other way, you should
follow their lead and just use this example as a guide for the pace and size of a good first
experiment. Even if you do follow this example, you should guide the user to customize the experiment
design as you go; don't just copy the code exactly!

Before you start reading the docs and testing out their workflow, please send the user a short
message like this:

> Welcome to fxtr's "Your first experiment" guide! I'll start by reading the documentation
> and checking your environment. Then we'll decide what question to study, and I'll guide you
> through how to set up your first experiment with fxtr.

## How to guide

* **Guide the user through each choice and unit of work.** The point of this guided walkthrough
  is not to just write an experiment, it is to use this experiment as a way to teach the user
  about the pieces of fxtr and how they work. By default, you should pause often, explaining
  what you are about to do and pointing out the relevant concepts and guides that the user can
  read.
* **Ask a few questions at a time**, and offer concrete options with a recommended default.
  Someone new to fxtr can choose between options more easily than they can fill in a blank.
* **Teach in passing.** When a fxtr idea first matters (a step, a dimension, the cache), explain
  it in a sentence or two in terms of their experiment, and link the page that covers it. Don't
  front-load concepts they haven't needed yet.
* **Keep the first version small.** Aim for an experiment of about one screen of design that
  answers one question: a few conditions, ten to fifty items, and one measurement. Record bigger
  ideas as next steps rather than building them now.
* **Ask before spending money.** Before any launch that calls a paid API, say how many model
  calls it makes (conversations times turns, plus judge calls) and get the user's go-ahead.
  Repeat this for the full run.
* **Report plainly.** Say what ran, what was reused, and what failed, with the job ID. Make sure
  to ground your summaries in the actual results of the experiment (e.g. the report entity)
  rather than by manually adding up printouts.

## 1. Check the setup

Before talking design, check that the user can run a job, and tell them what's missing. If a
check fails with a permission error, the cause may be your sandbox rather than their machine
(a sandbox can block Docker's socket, local ports such as the database's, and caches outside
the project): ask for the permission and rerun the check before reporting anything missing.

* The tools in [Installation](../fxtr/references/installation.mdx#prerequisites): uv, Docker (or
  another Postgres server), Node, pnpm, and git. Check their versions.
* A Postgres server that fxtr can reach. If they have none, offer to start the container from
  [Start Postgres](../fxtr/references/installation.mdx#start-postgres).
* An API key for at least one provider: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in the
  environment or in a project's `.env`, or another provider's key for
  [OpenRouter](../behaviors/references/guides/choosing-models.mdx#openrouter). Check whether a key
  is set without printing it, in a way every shell understands: `printenv NAME > /dev/null` for
  the environment, `grep -qE '^NAME=.+' .env` for a `.env`. If none is set yet, ask which
  provider they will use along with their question in step 2, since it decides which models
  and which judge the design can use. They can add the key while you write the code; nothing
  needs it before the pilot.
* Whether the working directory is already in a fxtr project (a `pyproject.toml` with a
  `[tool.fxtr]` table). If it is, offer to add the experiment there; otherwise you will create a
  project in step 3.

## 2. Find the question and design the experiment

**Decide on a question to answer.** Ask the user whether they'd like to follow along with the
experiment in the "first-experiment" guide, or if they want to choose a different idea
to study. Please suggest these five other ideas for inspiration, and note that they can also
pick their own question to answer if they have something else in mind.

* **Self portraits**: What kinds of art (text or visual) do models make if asked to make art
  about themselves, or to illustrate themselves?
* **Responding to a strange statement**: How do different models respond when you send them a
  short message out of context (like "I killed an ant" from this post
  <https://x.com/entropicbloom/status/2107026868322869581>)?
* **Prompt sensitivity**: How do differences in a user's message or the system prompt affect
  how the model behaves?
* **Consistency under pressure**: Does a model keep their original answer when the user pushes back?
* **Responding to repetition**: What happens when the user keeps sending the same message
  to the model over and over?

A good first experiment:

* is self-contained (doesn't require external data)
* compares a few models, with multiple samples from each
* involves generating some transcripts, measuring something about those transcripts, and then
  either summarizing or visualizing the results

If their idea needs no model calls, or needs things a first experiment shouldn't take on
(fine-tuning, long agentic tasks, large external datasets), say so and help them find the part
that fits: one question, answered with model calls.

**Pin down the design.** Settle these with them, proposing defaults:

1. **What variables are we measuring differences between?** Often, the best variable to study
   is the model. However, the user might instead want to study differences in system prompt, or
   other differences about the scenario. In the initial pilot of the experiment, you should include
   at least two (and usually at least three) conditions that you expect to produce different
   results (e.g. a small model and a larger one, or two system prompts on opposite extremes).
2. **What other variables are we sweeping across, if any?** To learn something about how a model
   behaves in general, it's usually a good idea to measure that behavior across multiple conditions.
   For instance, when evaluating humor, we might want to sweep across joke topics or joke formats. When
   evaluating sensitivity to a system prompt, we might want to aggregate over multiple user prompts.
   When generating art, we might want to sweep over suggested styles for the art. However, if the task
   is simple, it might also be OK to not sweep over anything to start (e.g. just try with one prompt, or
   don't give any suggested styles for some art). In this case, you should still propose a possible
   dimension to sweep across, and just populate it with a single entry; this makes it possible to extend
   it with new values later.
3. **How do we generate the transcript?** For some tasks, it might be enough to just run a single turn
   of a conversation with a fixed prompt. More advanced tasks might require multiple turns or tools. This
   will become the logic in the step function that generates the transcripts.
4. **What are we measuring?** To make a quantitative comparison between the variables we are studying,
   we need some way to measure differences in behavior. In some cases, this can just be a pure function
   (e.g. response length or accuracy), but usually this will involve running a judge or grader model with
   a rubric that returns a verdict. Judge models should be asked for a rationale or explanation before
   giving a final answer, which should be either a numeric score or a set of named categories. XML
   format for structured outputs is a good default. Note that for some exploratory tasks (like seeing
   how models respond to an open-ended prompt), it might make sense to
   first generate some initial data and then look at it manually before proposing what the actual
   rubric or set of outcomes should be!
5. **What data types will we use to represent the experiment?** It usually makes sense to define some
   new entity types to hold the results of various parts of your experiment. For some parts of the experiment, you might be able to use the types from the `behaviors` library; in this case you should
   just use these. However, other things such as experiment configuration, judge results, and the final
   report object should usually be experiment-specific types. By default you should use
   "local.{projectname}.{TypeName}" for experiment-specific types (since there is not yet a global
   registry of types).

Show the design in one short block before writing code, along with
what each part becomes in fxtr. For example:

```text
Question:     which models write the funniest jokes?
Main variable of interest:  model: haiku-4.5, sonnet-5.5
Variables to sweep over:    topic: 10 everyday topics (coffee, dentist, printer, ...)
Conversation: one user message asking for a joke about the topic
Measurement:  a judge (opus-5.5) rates each joke from 1 to 10, with a rationale first
Samples:      sample: 3 per model and topic
Summary:      per model, the mean score
Size:         pilot 2 x 3 x 1  =  6 conversations (6 model calls) +  6 judge calls
              full  2 x 10 x 3 = 60 conversations (60 model calls) + 60 judge calls

New entity types to define:
- GenerationConfig: provider, model_name, sampling, prompt_template
- JudgeConfig: provider, model_name, sampling, rubric
- JokeGrade: topic, joke, score, rationale, judge_reply
- JokeReport: references to the jokes, grades, and summary arrays

Structure of the experiment workflow:
- a joke step mapped over [model, topic] replicated over [sample], returning a ChatRollout
- a judge step mapped over [model, topic, sample]
- a summary step mapped over [model]
```

Iterate with the user on this until they are satisfied with the design.

Once you have a design, you can ask the user how they want to proceed with the rest of the steps.
By default you can recommend a step-by-step walkthrough where you explain each unit of work before
you do it, but the user might ask for you to implement everything at once and just explain it at
the end.

## 3. Set up the project

If they have no project, ask where to create it (possibly current working dir or `~/fxtr/<short-name>`),
then create it, install its dependencies, build its renderers, and connect it to the database as
[Run an example](../fxtr/references/installation.mdx#run-an-example) does, without `--example`.
Then add behaviors as
[Calling language models](../behaviors/references/guides/language-models.mdx#set-up) shows. Have
the user put their keys in the project's `.env` themselves, or confirm that the environment
already has them; never write a key into a file, an input, or an entity. Commit.

`fxtr init` uses the schema `fxtr_<project name>`, and if an earlier project of the same name
used it, its jobs and cache are still there. Run `uv run fxtr jobs list` after `fxtr init`. If it
lists anything, tell the user, and offer a fresh schema
(`uv run fxtr init --database-url URL --schema NEW_NAME --force`) rather than deleting anything.
If they ask you to delete data anyway, name exactly what would go, confirm it, and never touch
another project's schema.

Tell them in two or three sentences what the project holds, using
[Project configuration](../fxtr/references/reference/project-configuration.mdx#what-fxtr-new-writes):
the package for experiment code, the renderer package `views/`, `.env`, and `fxtr.local.toml`.

## 4. Write the experiment

Read [Workflows and steps](../fxtr/references/concepts/workflows-and-steps.mdx),
[Arrays and parallel computations](../fxtr/references/concepts/arrays-and-parallel-computations.mdx),
and [Calling language models](../behaviors/references/guides/language-models.mdx).

Then tell the user what you are about to do, and then write the following:

* **One module** for the experiment, registered in `[tool.fxtr] modules`, holding its
  configuration entities, its verdict and report entities, its steps, and its workflow, shaped as
  the behaviors skill's best practices say. Pass each step only the fields it uses: a
  conversation step that receives the question's text but not its reference answer doesn't rerun
  when a reference answer is corrected, and only the judge does.
* **A launcher** at the project root that builds the items, stores a configuration per condition,
  runs the workflow, and prints the summary from the report in an `on_result` callback
  ([Read results](../fxtr/references/guides/running-and-viewing-jobs.mdx#read-results)), so its
  output ends with the answer rather than the report's ID. Define the pilot and full sizes side
  by side and choose one with an argument (`uv run python launch.py pilot`), so the full run is
  the same launcher with another word.

Check that the module imports cleanly, and type-checks if the project has a type checker.

Unless the user has said to do everything at once, this is a good point to pause and explain what you've
implemented so far. Walk the user through the files in a few lines each: which function is
which step, which dimension each one maps over, where the prompts and the rubric live, and where
the sizes are set. Point out what parts live in the steps, what parts live in the workflow, and what
parts live in the launcher.

Next, you can offer to test out the experiment logic by running it with a fake model, and ask the
user if they want you to do this. If so, you can point the project at a scratch schema
(set `schema` in `fxtr.local.toml`, as
[Before you launch](../fxtr/references/guides/running-and-viewing-jobs.mdx#before-you-launch)
says), launch the pilot with `make_api` returning a fake model, and set the schema back. This
catches mistakes in the steps, the workflow, the launcher, and the summary before any of them
costs money, and nothing from it lands in the real results.

Finally, you can recommend writing some custom renderers to help visualize the data in the experiment.
You can use the existing `behaviors` renderers for conversations, and make a proposal for how
to write renderers of

* the entities you introduced
* step invocations (if there is something more to show than just the array contents)
* a result overview that answers the user's question.

You can follow the fxtr skill's best practices to implement these views. By default, you should write
all of the renderers before launching the real pilot experiment, so that the user has something to
look at while the job runs.

## 5. Run the pilot

Start the viewer in the background as the fxtr skill says, then confirm the pilot's size and
number of model calls with the user, commit, and launch it under a `root` named for the experiment
(such as `jokes-v1`). The full run uses the same `root`, so it reuses the pilot's results.

While it runs, tell the user what they're looking at: their viewer has switched to the job, with
a card per step that fills in as conversations finish.

When it finishes, report the job's ID and status and the summary the
launcher printed. You can guide the user to open a few of the results in the viewer to see what
happened.

You can also spot-check the results to check if they match the initial hypothesis about what
would happen, or if there are any problems with the experiment. Any possible problems or refinements
you notice can be suggestions for the next step.

## 6. Change it with the user

Ask what they'd like to change. If the pilot has surfaced problems or improvements, you can suggest
making those improvements. If it looks good, you can also suggest expanding the pilot to a full
run over all of the conditions.

Before relaunching, tell them which results the next launch will reuse and which it will compute, following
[Managing the step cache](../fxtr/references/concepts/managing-the-step-cache.mdx). The common
changes on a first experiment:

* **Scaling up** (more items or samples): every pilot conversation and verdict is reused, and only
  the new ones run. Steps that reduce over a dimension that grew, such as the summary, are at the
  same address with new inputs, so the job stops on a cache conflict there. That is expected;
  explain it, then resume with `--overwrite-cache-conflicts`, since the pilot's summaries aren't
  wanted. A resume doesn't run the launcher's printing, so launch once more afterwards: every
  step is cached, so it makes no model calls and prints the summary at once.
* **Adding a condition** (a model, a phrasing): add it as a new key of its dimension. The existing
  conditions' results are reused, and the new key is computed beside them, so the two can be
  compared; a step that reduces over that dimension conflicts, as in scaling up. (If the condition
  needs a dimension the experiment doesn't have yet, tell the user that adding that dimension will
  recompute every step mapped over it, and ask the user if they prefer to just clear the old
  results or if you should use a new `root` name to keep both versions in the cache.)
* **Changing an input in place** (editing a prompt, the rubric, a sampling setting): the steps
  that receive it get new inputs at the same addresses and stop on cache conflicts. If the old
  results should be kept for comparison, make the change a new condition instead; otherwise
  explain the choices in
  [Resolving a job's conflicts](../fxtr/references/concepts/managing-the-step-cache.mdx#resolving-a-jobs-conflicts)
  and let the user pick.
* **Adding a new step at the end** (e.g. for a new analysis): all previous steps will hit the cache,
  so you can just insert the new step into the workflow in place.
* **Changing a step's code** (how answers are parsed or scored): the cache won't notice. Clear
  that step's entries, or add a configuration field, as
  [Handling changes to step logic](../fxtr/references/concepts/managing-the-step-cache.mdx#handling-changes-to-step-logic)
  says, and tell the user which results that recomputes.

Summarize for the user what each change will mean about the number of new model calls before each
launch, based on the current design and the state of the cache. Report each run as in step 5.

## 7. Figure out next steps

From here, you should ask the user what they want to do next, and help them do it. Some possible
next steps include:

* Update the overview renderer to go into more detail about what was found, or make it easier for
  people to explore the results.
* Discuss and explain some of fxtr's core concepts in more detail, building on the understanding
  from this experiment.
* Read over the generated data to refine the measurement rubrics or propose new things to measure.
* Study a follow-up question based on something you or the user noticed.
* Start a new experiment to answer a different question, based on what the user is interested in.

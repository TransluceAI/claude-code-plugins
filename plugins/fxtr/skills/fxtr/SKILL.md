---
name: fxtr
description: Set up, write, run, and view fxtr experiments, including new projects (`fxtr new`), steps and workflows, sweeps over models, prompts, or datasets, reductions, querying arrays (filter, aggregate, join, SQL), input datasets, reports, launching and resuming jobs, cached step results and reruns, and viewer renderers, results overviews, and the charts and visualizations in them. Use whenever starting or working in a fxtr project, creating or changing an experiment, or when a run reused results it should have recomputed (or recomputed results it should have reused).
---

# fxtr

fxtr runs experiments as durable, inspectable DAGs. An experiment is Python code in a fxtr
project: steps do the computation, and workflows schedule steps over arrays with named
dimensions. A launch runs a workflow as a job on the project's Postgres database, which caches
every step's result, and the experiment viewer shows the job's DAG and data through the
project's renderers.

The pages below are fxtr's documentation, grouped by the part of the work they cover. Read the
ones a task needs before writing code. [Core concepts](references/concepts/overview.mdx)
shows how the parts fit together, and its
[glossary](references/concepts/overview.mdx#glossary) defines the terms the pages use.

## Where to read

### Setting up a project

Installing fxtr, and a project's configuration, dependencies, and database.

| Task                                                                    | Read                                                                                                                 |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Start a project, or change its configuration, dependencies, or database | [Installation](references/installation.mdx), [Project configuration](references/reference/project-configuration.mdx) |

### Writing experiments

Steps and workflows, the arrays they compute over, and the records they store. A new experiment
usually means reading Workflows and steps and Arrays and parallel computations.

| Task                                                                                       | Read                                                                                         |
| ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| Guide someone new to fxtr through designing and running their first experiment             | the adjacent [first-experiment skill](../first-experiment/SKILL.md)                          |
| Write or change steps and workflows: signatures, determinism, hermeticity, failures        | [Workflows and steps](references/concepts/workflows-and-steps.mdx)                           |
| Shape data and sweeps: arrays, handles, mapping, alignment, reductions, replicas           | [Arrays and parallel computations](references/concepts/arrays-and-parallel-computations.mdx) |
| Filter, select, aggregate, or join arrays, or write SQL over them, in a workflow or a step | [Array queries](references/reference/array-queries.mdx)                                      |
| Define records: entities or structs, configurations, verdicts, reports                     | [Entities and custom types](references/concepts/entities-and-custom-types.mdx)               |
| Import external datasets, pass configuration, and store entities                           | [Importing external datasets](references/guides/importing-external-datasets.mdx)             |
| Call a language model, hold a conversation, or judge outputs                               | the adjacent [behaviors skill](../behaviors/SKILL.md)                                        |

### Visualizing experiments

Renderers, which draw the project's entities, steps, and results in the viewer. Read Designing
views before drawing anything in a renderer.

| Task                                                                                               | Read                                                                                                                                              |
| -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Write and register renderers for entity types, steps, and workflows, including results overviews   | [Visualization and custom renderers](references/concepts/visualization-and-custom-renderers.mdx), [Renderers](references/reference/renderers.mdx) |
| Design a view, chart, or visualization to fit the viewer                                           | [Designing views](references/guides/designing-views.mdx)                                                                                          |
| Build the renderer package, fix a bundle that doesn't build or load, or add a package to a project | [The renderer package](references/reference/renderers.mdx#the-renderer-package)                                                                   |

### Running jobs

Launching and following jobs, and the step cache that decides what a launch recomputes. Read
Running and viewing jobs before the first launch.

| Task                                                                                                   | Read                                                                                                                  |
| ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| Launch a job, watch it in the viewer, return a report and read results, resume, inspect, or share jobs | [Running and viewing jobs](references/guides/running-and-viewing-jobs.mdx)                                            |
| Choose how many steps run at once, or speed up a job whose steps call APIs                             | [Choose how many steps run at once](references/guides/running-and-viewing-jobs.mdx#choose-how-many-steps-run-at-once) |
| Set up a remote, push a job to a fxtr hub or an OCI registry, or pull one                              | [Pushing and pulling jobs](references/guides/pushing-and-pulling-jobs.mdx)                                            |
| Reuse or recompute cached results, resolve cache conflicts, change a step's logic                      | [Managing the step cache](references/concepts/managing-the-step-cache.mdx)                                            |
| Look up a command's options                                                                            | [CLI reference](references/reference/cli.mdx)                                                                         |

## Best practices

Do these by default, unless the user asks otherwise.

### Writing experiments

* **Name every step and workflow.** Pass `name=` to each `@step` and `@workflow`. The step cache,
  resumed jobs, and the viewer's renderers find a function by its
  [registered name](references/concepts/workflows-and-steps.mdx#registered-names), and the
  default name, taken from the function's module, changes when the function moves.
* **Write each docstring's first sentence for the viewer.** The operation's card shows it, so make
  it a short imperative sentence saying what the operation does
  ([Watch jobs in the viewer](references/guides/running-and-viewing-jobs.mdx#watch-jobs-in-the-viewer)).
* **Describe the experiment in `EXPERIMENT.md`** at the project root, which the viewer's rail
  links to: the question, what is compared or measured and why, and how scores are defined, in
  plain English for a reader new to the experiment. Keep it current as the experiment changes
  ([Watch jobs in the viewer](references/guides/running-and-viewing-jobs.mdx#watch-jobs-in-the-viewer)).
* **Return a report from the root workflow**: one entity that references every result worth
  presenting, for the launcher and the results overview to read
  ([Read results](references/guides/running-and-viewing-jobs.mdx#read-results)).
* **Keep the graph's edges.** If an unavoidable reconstruction loses an edge in the viewer (an
  array observed, transformed in Python, and added back as a source), tell the user.
* **Keep stale results out of a changed step.** The cache matches a step by its name and inputs,
  not its code. After changing what a step computes, handle the change as
  [Handling changes to step logic](references/concepts/managing-the-step-cache.mdx#handling-changes-to-step-logic)
  describes before relaunching, and tell the user which results the next launch recomputes.

### Visualizing experiments

Write renderers in the project's renderer package, `views/`. If the project has none, ask the user
before [adding one](references/reference/renderers.mdx#adding-a-package-to-a-project).

* **Give every entity type you introduce its renderers**, registered under its type tag: an
  `EntityPanel` that leads with what matters in the entity, and an `EntityInlineLink` that names
  it in a few words, since the default link shows only its type and a short ID. For a type with
  many fields, add an `EntityHoverPreview` showing the few that identify it. Records from
  behaviors already have renderers; the [behaviors skill](../behaviors/SKILL.md) says how to
  include them.
* **Give each step an `InvocationPanel`**, registered
  under the step's name, whenever there is something useful to show beyond the output array itself. The step's pane already shows its arrays as tables, so don't redraw them
  ([Where a view appears](references/guides/designing-views.mdx#where-a-view-appears)).
  The panel becomes the step's default view, in the pane its card opens, and it is
  handed every invocation the viewer's selection picks out, up to all of a mapped step's. Show
  one in full and several together (a chart or a summary), loading their outputs with `LoadEach`
  ([Step panels](references/reference/renderers.mdx#step-panels)). Never show a note
  asking the reader to select one; `singleInvocation`, which does that, is deprecated.
* **Give the root workflow a results overview**: an `InvocationPanel` that reads the workflow's
  report and presents the experiment's findings
  ([Results overviews](references/concepts/visualization-and-custom-renderers.mdx#results-overviews)).
* **Check a view without opening it.** After changing a view, confirm it builds and run the
  searches in [Check it](references/guides/designing-views.mdx#check-it), then tell the
  user it is ready to look at in their viewer. Don't open the viewer in a browser yourself, or set
  up Playwright or a headless browser to screenshot it, unless the user asks you to.

### Running jobs

* **Start the viewer once.** The first time the user asks for a job to run, start
  `uv run fxtr view` in the background, as a long-running process of its own (don't wait for it to
  exit), and before the launch wait until it prints `the viewer is at <url>`. It opens the viewer
  in the user's browser. Don't run `fxtr view` again for later launches: each run opens another
  tab. While it runs, each launch shows its job in the viewer the user has open, or in a new tab
  when none is open: tell the user it is there, and report the job's ID and status from the
  launch's output. A launch that finds no viewer prints `no viewer is running for this project`
  with the command to start one: start it then.
* **Keep the viewer running** across launches and renderer edits. It rebuilds the renderers when
  their sources change, and the open viewer switches to them in place, so never ask the user to
  reload or restart it.
* **Link the user to what you are pointing at.** The viewer's URL holds the job, the level shown,
  the slice, and the open panels, so instead of describing where to click, give the user a link:
  the viewer's URL (the one `fxtr view` printed, also saved in `.fxtr/viewer.json` within the project), then `#` and `&`-separated parts.

  ```
  http://127.0.0.1:8000/#job=<job id>&w=flowchart(/outer,model=sonnet)&slice=(prompt=3)&card=judge&p=table(/outer/judge,model=sonnet)&p=.output.transcript
  ```

  `job` is the job's ID (left out, the newest job). `w` is the workflow invocation shown (left
  out, the root's trace): `trace`, `flowchart`, or the id of an `InvocationPanel` renderer
  of that workflow, applied to its step path from the root, with the keys of the mapped workflows
  on the way. `slice` picks dim values for every card and panel. `card` names a step of that workflow (or
  `return`, what it returned) whose card to scroll to. Each `p` opens a panel, in order,
  each following the one before it; `pin` opens one that stays as it is. A panel is an address,
  a view applied to a location and params: the view is `table`, `invocation`, `tree`, `code`, a
  renderer's or page's id, or nothing for the default; the location is a step path from the root
  (`/outer/judge`), or `cid:<cid>` for an entity, then a field path (`.output.transcript`,
  `.inputs.prompt`, `[2]` for a list item); params bind dims and the params a view declares, by
  name, as bare values (`3`, `sonnet`) or JSON (`"two words"`, `{"message":2}`). The `invocation`
  view shows one call: its status line, then its inputs, a workflow's runs, and its output; with
  `section_order=output_first` the output comes right under the status line instead
  (`section_order=inputs_first` is the default). Link output first when the user wants to read
  what the call returned. After the first
  panel, a location may be relative to the panel before it: `.field…` below it, `../step` a
  sibling. Percent-encode only spaces, `%`, `&`, `#`, `+`, and quotes.

### Reading the documentation

* **Know which documentation you have.** Distributed in the fxtr plugin for Claude Code or
  Codex, this skill carries a copy of the pages, and `provenance.json` beside this file records
  the fxtr and behaviors versions they describe. If the project depends on another fxtr version
  (its `uv.lock` says which), tell the user. The plugin has its own version and update cycle; docs.transluce.ai has
  the newest pages.

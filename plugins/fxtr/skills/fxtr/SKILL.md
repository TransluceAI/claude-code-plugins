---
name: fxtr
description: Set up, write, run, and view fxtr experiments, including new projects (`fxtr new`), steps and workflows, sweeps over models, prompts, or datasets, reductions, querying arrays (filter, aggregate, join, SQL), input datasets, reports, launching and resuming jobs, cached step results and reruns, and viewer renderers, results overviews, and the charts and visualizations in them. Use whenever starting or working in a fxtr project, creating or changing an experiment, when a run reused results it should have recomputed (or recomputed results it should have reused), or to answer questions about a job's results, such as finding interesting runs and reading transcripts, judgments, errors, and logs, and citing them with viewer links.
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
| Answer questions about a job's data, or cite it to the user                                            | [Asking an agent about a job](references/guides/asking-an-agent-about-a-job.mdx)                                      |
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
* **Show hover content with `HoverCard`.** To show more about an element that is not a chart's
  mark (a chip in text, a cell of a table), wrap the element in `HoverCard` from `fxtr-view-kit`.
  Don't draw your own card with `position: absolute`: each pane is a scroll box, and the pane cuts
  off a card that extends past its edges. `HoverCard` draws the card above every pane.
* **Open details in a pane beside the view.** When the reader presses an element that points at
  another entity, or at a part of one (a citation, a row's transcript, an event of a game), open
  the entity beside the view with `EntityLink`, or with `useEntityLinks().open(id, params)` when the
  view draws the element itself. Name the part with a selector param, which the entity's view
  declares and reads
  ([Params of an entity's views](references/reference/renderers.mdx#params-of-an-entitys-views)).
  Don't scroll to a copy of the entity embedded further down the view.
* **Ship a citation format with its renderer.** When you define a format, translate each saved
  `address_in_entity` into parameters the cited entity's renderer uses to show the evidence.
  The hub loads the compatible renderer bundle attached to the job's push. The local viewer
  uses the project's current bundle, so check saved citations when rebuilding for older jobs.
  [Params of an entity's views](references/reference/renderers.mdx#params-of-an-entitys-views)
* **Scroll to a selected part with `scrollIntoPane`.** In a view that reads a selector, get the
  part's element from a ref and call `scrollIntoPane` from `fxtr-view-kit` in an effect, returning
  its result. Don't call `scrollIntoView`, which also moves the viewer's panes sideways, and don't
  find the element by a document id, because the page can show two views of one entity.
  `HoverCard` and `scrollIntoPane` each explain themselves in their module comments, in
  `views/node_modules/fxtr-view-kit/src/`.
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
  the slice, and the open panels, so instead of describing where to click, give the user a link.
  Make it with the fxtr MCP tools' `make_viewer_link`. Without them, write it as
  [The viewer's URL](references/guides/asking-an-agent-about-a-job.mdx#the-viewers-url)
  says, and tell the user you wrote it by hand. When such a link passes params to an entity's
  view, link the entity by its cid: an older viewer does not pass params to an entity at a
  step's field path.

### Answering questions about a job

Read a job's data with the fxtr MCP tools (`list_steps`, `read_step_output`, `read_invocation`,
`read_entity`), as [Asking an agent about a job](references/guides/asking-an-agent-about-a-job.mdx) describes. Don't read the viewer's
GraphQL API: it is not a supported interface.

* **Add the tools when they are missing.** If you have no fxtr MCP tools in an fxtr project, ask
  the user whether to add them. On a yes, run `uv run fxtr mcp add` in the project (in Codex,
  `uv run fxtr mcp add --codex`). The command writes or updates `.mcp.json`, which the user can
  commit so teammates get the tools too. Then tell the user to start a new session, which has the
  tools, and to approve the `fxtr` server when Claude Code asks. Until then, answer from
  `fxtr jobs` and the files you can read.
  * The tools load only in a session started in the project. If your session started elsewhere,
    find the project from the user's request (a path, a job id, or a viewer URL), offer
    `fxtr mcp add` there, and tell the user to start the next session in the project.
  * If `fxtr mcp add` fails with no `mcp` command, the project's fxtr is too old for the tools.
    Tell the user, and write links by hand as "Link the user to what you are pointing at" says.

* **Start from what the experiment's author wrote.** Read `EXPERIMENT.md` and use
  `read_step_output` with `step_path="/"` to read the root workflow's report, when available.
  For a particular step invocation, give its path, such as `/outer/judge`, and dimension keys,
  such as `{"model": "sonnet", "prompt": 3}`.

* **Name a job by its full id, from `list_jobs`.** The tools take only a whole UUID
  (`801488ae-7ed8-4af6-8904-1133deba0201`). `EXPERIMENT.md`, reports, and the viewer often cite a
  short id (`801488ae`), and the job a document cites may be in another database, such as its
  author's. Find the full id with `list_jobs` first. If no job matches, tell the user which jobs
  the project has.

* **Read code at the job's commit,** with `read_step_code` or `git show <commit>:<path>`, not the
  working tree, which may have changed since the job ran.

* **Read a transcript before you say what a model did in it.** Say which claims are a judge's and
  which you checked.

* **For a question across many rows, count with a script** over the rows you read, and say how
  you counted.

* **To show the interesting parts of one transcript or a few,** read each with
  `read_entity(as_prompt_text=True, job=...)`, pick the parts, and link each part's lines.

* **To find interesting runs, or interesting parts of transcripts, across a job,** write a judge
  step with behaviors' `judge` and its line citations (the [behaviors skill](../behaviors/SKILL.md)),
  add it to the workflow, and launch the workflow again: the step cache reuses the results of the
  steps that did not change. Then rank the judge's scores and show the user the highest and the
  lowest, citing the judge's lines. Ask before you launch: a judge sweep calls a model for every
  row, so say how many calls it makes.

* **Cite each claim about the data,** at the finest granularity that supports it: a line rather
  than a message, a message rather than a transcript, an invocation rather than a step.
  * When the user asks to see, show, or find something in a job, answer with links: one for
    each place you point at.
  * Make every link with `make_viewer_link`. Write one by hand only when you have no tools, as
    "Link the user to what you are pointing at" says.
  * A view's own params go in the panel's `params`. To find a project view's params, read
    where its renderer declares them in `views/src` (`declareView(..., { params: [...] })`), and
    read the renderer for each param's shape. Never guess a param's name: a view ignores a param
    it does not declare.
  * A view gets the panel's params only when the panel shows the entity: by its cid, or at a
    step's field path that holds a reference to the entity. At a field path that holds anything
    else, the viewer shows the value as data and ignores the params, and `make_viewer_link`
    notes it. Then link the entity that takes them instead.
  * Pass `job` to `read_entity` to get the entity's link with what you read.
  * Put each link on the claim's own words, never on "here", and give a short exact quote next to
    it, so the user can check the claim without clicking.
  * Reuse a judge's stored citation as it is: its entity and its `address_in_entity`. If the
    viewer can't open a citation's address at its place, link the entity and write the address in
    the link's text. Never drop a citation for that reason.
  * For a custom citation format, use the registered entry point's name as `citation_format` in
    `make_viewer_link`. To expose a new format to MCP, give the format a `viewer_params` function
    and register the format in `fxtr.citation_formats`.
    [Custom formats](../behaviors/references/reference/api.mdx#judging)

* **Give links. Open the viewer only when the user asks to see something,** with
  `open_in_viewer`. The tool shows the linked workflow in the center and pins any requested panels
  beside the user's panels. With no page open, the tool opens a new tab.

### Reading the documentation

* **Know which documentation you have.** Distributed in the fxtr plugin for Claude Code or
  Codex, this skill carries a copy of the pages, and `provenance.json` beside this file records
  the fxtr and behaviors versions they describe. If the project depends on another fxtr version
  (its `uv.lock` says which), tell the user. The plugin has its own version and update cycle; docs.transluce.ai has
  the newest pages.

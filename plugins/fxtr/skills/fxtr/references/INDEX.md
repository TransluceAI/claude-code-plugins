# The fxtr documentation

The pages of https://docs.transluce.ai/fxtr, copied with this skill: `provenance.json`,
beside its `SKILL.md`, says from which version. Each is listed with what it covers,
in the order of the site's navigation.

## Get started

- [Introduction](index.mdx): fxtr is an experiment orchestration system for verifiable AI-powered analyses
- [Installation](installation.mdx): Install fxtr from PyPI and verify the setup with an example project.
- [Your first experiment](first-experiment.mdx): Write a small experiment with a mapped step and a reduction, launch it, and see how caching works.

## Concepts

- [Core concepts](concepts/overview.mdx): How projects, steps, workflows, jobs, arrays, and entities fit together.
- [Workflows and steps](concepts/workflows-and-steps.mdx): How an experiment is written: workflows describe the structure, steps do the work.
- [Arrays and parallel computations](concepts/arrays-and-parallel-computations.mdx): The data model: arrays indexed by named dimensions, and how steps are mapped over them.
- [Entities and custom types](concepts/entities-and-custom-types.mdx): Stored records with identities of their own: when to define one, how to store and load it, and how it differs from a struct in an array.
- [Managing the step cache](concepts/managing-the-step-cache.mdx): How fxtr reuses step results across jobs, when it refuses to, and how to control it.
- [Visualization and custom renderers](concepts/visualization-and-custom-renderers.mdx): How the viewer draws a job, and how renderers teach it to show your own types, steps, and results.

## Guides

- [Running and viewing jobs](guides/running-and-viewing-jobs.mdx): Launch jobs from Python or the command line, watch them in the viewer, read their results, and resume, inspect, or share them.
- [Importing external datasets](guides/importing-external-datasets.mdx): Bring external datasets into fxtr as typed arrays for processing in workflows.

## Reference

- [CLI reference](reference/cli.mdx): The fxtr command-line interface.

## Other pages

- [Designing views](guides/designing-views.mdx): How a renderer's views should look and behave in the viewer: surfaces, type, color, charts, links, controls, and how to check them.
- [Array queries](reference/array-queries.mdx): Filter, reshape, aggregate, and join arrays with the query builder or SQL, in a workflow or in a step.
- [Project configuration](reference/project-configuration.mdx): What fxtr new writes, and the settings in pyproject.toml and fxtr.local.toml.
- [Renderers](reference/renderers.mdx): The renderer API: slots and registration, loading entities and invocations, step panels, links, panel state, the kit, and building the renderer package.

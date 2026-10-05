# Claude Code Plugins

A collection of plugins for Claude Code.

## Available Plugins

| Plugin | Description |
|--------|-------------|
| [docent](./plugins/docent) | Docent AI analysis tools |
| [fxtr](./plugins/fxtr) | Skills for writing, running, and viewing fxtr experiments, and for calling models from them with behaviors |

The docent plugin includes two skills:
- **analysis** - Analyzing agent behavior with Docent
- **ingestion** - Structured workflow for ingesting agent run data into Docent

The fxtr plugin includes two skills, each with a copy of the documentation it links from
[docs.transluce.ai](https://docs.transluce.ai):
- **fxtr** - Setting up, writing, running, and viewing fxtr experiments
- **behaviors** - Calling language models from fxtr experiments with the behaviors library

## Installation

Add this marketplace to Claude Code:

```shell
/plugin marketplace add TransluceAI/claude-code-plugins
```

Then install a plugin:

```shell
/plugin install docent@transluce-plugins
/plugin install fxtr@transluce-plugins
```

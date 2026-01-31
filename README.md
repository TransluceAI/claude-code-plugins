# Claude Code Plugins

A collection of plugins for Claude Code.

## Available Plugins

| Plugin | Description | Version |
|--------|-------------|---------|
| [docent](./plugins/docent) | Docent AI analysis tools | 1.0.0 |

The docent plugin includes two skills:
- **analysis** - Analyzing agent behavior with Docent
- **ingestion** - Structured workflow for ingesting agent run data into Docent

## Installation

Add this marketplace to Claude Code:

```shell
/plugin marketplace add TransluceAI/claude-code-plugins
```

Then install the plugin:

```shell
/plugin install docent@transluce-plugins
```

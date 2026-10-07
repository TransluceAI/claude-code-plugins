"""Sanity checks for the marketplace and every plugin in it.

Run from the repository root: ``python .github/scripts/plugin_sanity.py``. Every plugin gets the
generic checks (its marketplace entry, manifest, and skill frontmatter); a plugin with checks of
its own below gets those too.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path.cwd()
VERSION = re.compile(r"\d+\.\d+\.\d+")
LINK = re.compile(r"\]\(([^)\s]+)\)")


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{path} is not valid JSON: {exc}")


def frontmatter(path: Path) -> dict[str, str]:
    """The top-level keys of a SKILL.md's YAML frontmatter, as raw strings."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if match is None:
        fail(f"{path} has no frontmatter")
    keys = {}
    for line in match.group(1).splitlines():
        key = re.match(r"([A-Za-z][\w-]*):\s*(.*)$", line)
        if key:
            keys[key.group(1)] = key.group(2).strip()
    return keys


def check_plugin(entry: dict[str, Any]) -> Path:
    """The checks every plugin gets; returns its directory."""
    name = entry.get("name")
    plugin_dir = ROOT / entry.get("source", "")
    if not plugin_dir.is_dir():
        fail(f"marketplace source of {name} does not exist: {plugin_dir}")
    manifest = load_json(plugin_dir / ".claude-plugin" / "plugin.json")
    if manifest.get("name") != name:
        fail(f"plugin manifest name must be {name}")
    version = manifest.get("version")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        fail(f"{name} plugin manifest version must be plain major.minor.patch")
    if entry.get("version") != version:
        fail(f"marketplace {name} version must match its plugin manifest version")
    for skill in sorted((plugin_dir / "skills").glob("*/SKILL.md")):
        keys = frontmatter(skill)
        if keys.get("name") != skill.parent.name:
            fail(f"{skill} frontmatter name must be {skill.parent.name}")
        if not keys.get("description"):
            fail(f"{skill} frontmatter needs a description")
    return plugin_dir


def check_docent(plugin_dir: Path) -> None:
    required_files = [
        ".claude-plugin/plugin.json",
        ".mcp.json",
        "skills/docent/SKILL.md",
        "skills/docent/analysis.md",
        "skills/docent/dql-reference.md",
        "skills/docent/ingestion-reference.md",
        "skills/docent/ingestion.md",
        "skills/docent/readings-reference.md",
        "skills/docent/report.md",
    ]
    for rel_path in required_files:
        path = plugin_dir / rel_path
        if not path.is_file():
            fail(f"required plugin file is missing: {rel_path}")
        if path.suffix == ".md" and not path.read_text(encoding="utf-8").strip():
            fail(f"markdown file is empty: {rel_path}")

    mcp = load_json(plugin_dir / ".mcp.json")
    server = mcp.get("mcpServers", {}).get("docent")
    if not isinstance(server, dict):
        fail(".mcp.json must define mcpServers.docent")
    if server.get("type") != "stdio" or server.get("command") != "uv":
        fail("docent MCP server must run as uv stdio")
    args = server.get("args")
    if not isinstance(args, list) or "--from" not in args:
        fail("docent MCP server args must include --from")

    forbidden_names = {".mcp.local.json", "docent.env"}
    for path in plugin_dir.rglob("*"):
        if path.name in forbidden_names or path.name.startswith("docent.env."):
            fail(f"local credential/config file must not be published: {path}")


FXTR_SKILLS = ["behaviors", "first-experiment", "fxtr"]
SKILLS_WITH_REFERENCES = {"behaviors", "fxtr"}


def check_fxtr(plugin_dir: Path) -> None:
    """The behaviors, first-experiment, and fxtr skills, as fxtr3's `pnpm sync:plugin` prepares
    them: all from one clean revision of fxtr3, with links that resolve. The behaviors and fxtr
    skills each hold a copy of the pages they link; first-experiment links into those copies."""
    skills = sorted(path.name for path in (plugin_dir / "skills").iterdir() if path.is_dir())
    if skills != FXTR_SKILLS:
        fail(f"fxtr plugin must hold exactly the skills {FXTR_SKILLS}, not {skills}")
    revisions = set()
    for name in skills:
        skill_dir = plugin_dir / "skills" / name
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file() or not skill_md.read_text(encoding="utf-8").strip():
            fail(f"{name} skill needs a non-empty SKILL.md")
        references = [p for p in (skill_dir / "references").rglob("*") if p.is_file()]
        if not references and name in SKILLS_WITH_REFERENCES:
            fail(f"{name} skill has no references")
        for page in references:
            if page.suffix in {".md", ".mdx"} and not page.read_text(encoding="utf-8").strip():
                fail(f"reference page is empty: {page.relative_to(plugin_dir)}")

        provenance = load_json(skill_dir / "provenance.json")
        if provenance.get("skill") != name:
            fail(f"{name} provenance names the skill {provenance.get('skill')!r}")
        revision = provenance.get("revision")
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
            fail(f"{name} provenance needs the full fxtr3 revision it was prepared from")
        if provenance.get("modified") is not False:
            fail(f"{name} was prepared from a modified fxtr3 checkout; sync from a clean one")
        revisions.add(revision)

        for target in LINK.findall(skill_md.read_text(encoding="utf-8")):
            if re.match(r"[a-z][a-z0-9+.-]*:", target) or target.startswith("#"):
                continue  # a URL or an anchor in the page itself
            path = (skill_dir / target.split("#", 1)[0]).resolve()
            if not path.is_file():
                fail(f"{name}/SKILL.md links to a missing file: {target}")
    if len(revisions) != 1:
        fail("the fxtr plugin's skills must be prepared from the same fxtr3 revision")


PLUGIN_CHECKS: dict[str, Callable[[Path], None]] = {
    "docent": check_docent,
    "fxtr": check_fxtr,
}


def main() -> None:
    marketplace = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    entries = marketplace.get("plugins")
    if not isinstance(entries, list):
        fail("marketplace plugins must be a list")
    names = [entry.get("name") for entry in entries]
    if len(set(names)) != len(names):
        fail(f"marketplace plugin names must be unique: {names}")
    for name in PLUGIN_CHECKS:
        if names.count(name) != 1:
            fail(f"marketplace must contain exactly one {name} plugin entry")
    for entry in entries:
        plugin_dir = check_plugin(entry)
        if entry["name"] in PLUGIN_CHECKS:
            PLUGIN_CHECKS[entry["name"]](plugin_dir)
    print(f"Claude Code plugin sanity checks passed: {', '.join(names)}")


if __name__ == "__main__":
    sys.exit(main())

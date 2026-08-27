#!/usr/bin/env python3
"""SessionEnd hook: hand the session to a detached uploader, in milliseconds.

Claude Code runs SessionEnd hooks synchronously and may kill them almost
immediately when the CLI exits, so anything slow here either stalls the
user's exit or silently dies mid-upload. This script therefore does only
millisecond-scale work with the system python3 and no third-party imports:
re-check the opt-out gates, then spawn the real uploader as a fully detached
process (its own session on POSIX, detached process group on Windows, all
stdio on /dev/null) and exit. The hook returns before any package resolution
or network happens, and the detached uploader survives both the CLI exiting
and the terminal closing.

SessionEnd hook output is ignored but stderr is shown to the user, so every
path must stay silent and exit cleanly.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

UPLOADER_REQUIREMENT = "docent-python>=0.1.83"


def _spawn_detached(args: list[str]) -> None:
    """Start `args` so it is immune to the hook's death.

    A new session (POSIX) or detached process group (Windows) keeps the
    uploader out of the hook's process group, so killing the hook — which
    Claude Code does on exit — cannot take the upload down with it. All
    stdio on devnull so no inherited pipe keeps Claude Code waiting on us.
    """
    if os.name == "nt":
        flags = getattr(subprocess, "DETACHED_PROCESS", 0x00000008) | getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200
        )
        subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=flags,
        )
    else:
        subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
        )


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return
    if not isinstance(payload, dict):
        return
    if os.environ.get("DOCENT_ENABLE_SESSION_LOGGING") != "1" or os.environ.get(
        "DOCENT_DISABLE_SESSION_LOGGING"
    ):
        return
    if not isinstance(payload.get("session_id"), str) or not isinstance(
        payload.get("transcript_path"), str
    ):
        return

    home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    if not home:
        return
    state_path = os.path.join(home, ".docent", "claude-code-logging.json")
    try:
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
    except FileNotFoundError:
        state = {}
    except Exception:
        return
    if not isinstance(state, dict):
        return
    analytics = state.get("analytics")
    choice = analytics.get("choice") if isinstance(analytics, dict) else None
    if choice == "no":
        return

    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _spawn_detached(
        [
            "uv",
            "tool",
            "run",
            "--quiet",
            "--from",
            UPLOADER_REQUIREMENT,
            "python",
            "-m",
            "docent.plugin.session_upload",
            json.dumps(payload),
            plugin_root,
        ]
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass

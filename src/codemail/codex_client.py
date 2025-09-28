"""Run Codex CLI commands and parse their streamed JSON output."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Set, Tuple

from . import config
from .log import log

CODEX_TIMEOUT = int(os.environ.get("CODEMAIL_CODEX_TIMEOUT", "3600"))


def _list_session_files() -> Set[str]:
    if not config.SESSION_ROOT.exists():
        return set()
    return {p.as_posix() for p in config.SESSION_ROOT.rglob("*.jsonl")}


def _capture_latest_session(before: Set[str]) -> Optional[str]:
    if not config.SESSION_ROOT.exists():
        return None
    files = sorted(
        (p for p in config.SESSION_ROOT.rglob("*.jsonl")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for path in files:
        candidate = path.as_posix()
        if candidate in before:
            continue
        parts = path.stem.split("-")
        if len(parts) >= 6:
            return "-".join(parts[-5:])
        if parts:
            return parts[-1]
    return None


def run_codex(
    prompt: str, resume_session: Optional[str]
) -> Tuple[int, Optional[str], List[str]]:
    base_cmd = [config.CODEX_BIN, "exec", "--skip-git-repo-check", "--json"]
    if resume_session:
        cmd = base_cmd + ["resume", resume_session, "-"]
    else:
        cmd = base_cmd + ["-"]

    env = os.environ.copy()
    env.setdefault("HOME", str(config.ENV_HOME))

    # Preserve historical node path tweaks for Codex CLI helper scripts.
    node_bin = Path.home() / ".nvm" / "versions" / "node" / "v22.19.0" / "bin"
    path_parts = [str(node_bin)] if node_bin.exists() else []
    path_parts.append(env.get("PATH", ""))
    env["PATH"] = ":".join(part for part in path_parts if part)

    before = _list_session_files()

    try:
        proc = subprocess.run(
            cmd,
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=str(config.ENV_HOME),
            timeout=CODEX_TIMEOUT,
        )
    except subprocess.TimeoutExpired as exc:
        return (
            124,
            resume_session,
            [f"Codex execution timed out after {exc.timeout} seconds."],
        )

    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")

    messages: List[str] = []
    session = resume_session

    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg = event.get("msg")
        if isinstance(msg, dict):
            if msg.get("type") == "agent_message" and msg.get("message"):
                messages.append(msg["message"].strip())
            elif msg.get("type") == "error" and msg.get("message"):
                messages.append(f"Agent error: {msg['message']}")

        if not session:
            sid = event.get("session_id") or event.get("id")
            if isinstance(sid, str) and len(sid) >= 10 and sid.count("-") >= 4:
                session = sid

    if not session:
        latest = _capture_latest_session(before)
        if latest:
            session = latest

    if stderr.strip():
        messages.append(f"[stderr]\n{stderr.strip()}")

    if proc.returncode != 0:
        log(f"Codex exited with status {proc.returncode}")

    return proc.returncode, session, messages or ["No response from Codex."]

"""Lightweight logging utility."""

from __future__ import annotations

from datetime import datetime, timezone

from . import config


def log(message: str) -> None:
    """Append *message* to the configured log file with UTC timestamp."""
    config.ensure_parent(config.LOG_PATH)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with config.LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"[{ts}] {message}\n")

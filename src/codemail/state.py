"""State management for message-to-session mapping."""

from __future__ import annotations

import json
from typing import Dict

from . import config
from .log import log


StateDict = Dict[str, Dict[str, str]]


def load_state() -> StateDict:
    if config.STATE_PATH.exists():
        try:
            with config.STATE_PATH.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:  # pragma: no cover - defensive logging
            log(f"Failed to load state: {exc}")
    return {"messages": {}}


def save_state(state: StateDict) -> None:
    config.ensure_parent(config.STATE_PATH)
    tmp = config.STATE_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    tmp.replace(config.STATE_PATH)

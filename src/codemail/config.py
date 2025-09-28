"""Configuration helpers for Codemail."""

from __future__ import annotations

import os
from pathlib import Path

HOME = Path.home()

MAIL_USER = os.environ.get("CODEMAIL_MAIL_USER", "codex@branch.bet")
MAIL_PASS = os.environ.get("CODEMAIL_MAIL_PASS")
PASSWORD_FILE = Path(
    os.environ.get("CODEMAIL_PASSWORD_FILE", HOME / ".codex_mail_pass")
).expanduser()

SMTP_HOST = os.environ.get("CODEMAIL_SMTP_HOST", "mail.branch.bet")
SMTP_PORT = int(os.environ.get("CODEMAIL_SMTP_PORT", "587"))

STATE_PATH = Path(
    os.environ.get("CODEMAIL_STATE_PATH", HOME / ".codex" / "task_mail_map.json")
).expanduser()
LOG_PATH = Path(
    os.environ.get("CODEMAIL_LOG_PATH", HOME / ".codex" / "task-mail-runner.log")
).expanduser()
SESSION_ROOT = Path(
    os.environ.get("CODEMAIL_SESSION_ROOT", HOME / ".codex" / "sessions")
).expanduser()

REPLY_TO = os.environ.get("CODEMAIL_REPLY_TO", "tasks@branch.bet")
DEFAULT_FALLBACK_RECIPIENT = os.environ.get(
    "CODEMAIL_FALLBACK_RECIPIENT", "branch@branch.bet"
)

CODEX_BIN = os.environ.get("CODEMAIL_CODEX_BIN", "codex")

ENV_HOME = Path(os.environ.get("CODEMAIL_HOME", HOME)).expanduser()

ALLOWED_SENDERS = [
    entry.strip().lower()
    for entry in os.environ.get("CODEMAIL_ALLOWED_SENDERS", "").split(",")
    if entry.strip()
]


def ensure_parent(path: Path) -> None:
    """Create parent directory for *path* if it doesn't already exist."""
    path.parent.mkdir(parents=True, exist_ok=True)


def resolve_mail_password() -> str:
    """Return the SMTP password, reading from PASSWORD_FILE if necessary."""
    if MAIL_PASS:
        return MAIL_PASS
    if PASSWORD_FILE.exists():
        return PASSWORD_FILE.read_text(encoding="utf-8").strip()
    raise RuntimeError(
        "SMTP password not provided; set CODEMAIL_MAIL_PASS or CODEMAIL_PASSWORD_FILE"
    )

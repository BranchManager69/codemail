"""Utilities for working with email messages."""

from __future__ import annotations

import html
import re
from email.message import EmailMessage
from email.parser import BytesParser
from email import policy
from email.utils import getaddresses
from typing import Iterable, List, Optional

from . import config

MSG_ID_RE = re.compile(r"<([^>]+)>")


def parse_bytes(raw: bytes) -> EmailMessage:
    parser = BytesParser(policy=policy.default)
    return parser.parsebytes(raw)


def normalize_msg_id(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    match = MSG_ID_RE.fullmatch(value)
    if match:
        value = match.group(1)
    elif value.startswith("<") and value.endswith(">"):
        value = value[1:-1]
    return value.strip() or None


def extract_referenced_ids(header_value: Optional[str]) -> List[str]:
    if not header_value:
        return []
    return [match.strip() for match in MSG_ID_RE.findall(header_value)]


def extract_body(msg: EmailMessage) -> str:
    body_part = msg.get_body(preferencelist=("plain", "html"))
    if body_part is None and not msg.is_multipart():
        body_part = msg

    text = ""
    if body_part is not None:
        try:
            text = body_part.get_content()
        except Exception:  # pragma: no cover - protective fallback
            payload = body_part.get_payload(decode=True)
            if payload:
                text = payload.decode(
                    body_part.get_content_charset("utf-8"), errors="replace"
                )

    if body_part is not None and body_part.get_content_type() == "text/html":
        text = html.unescape(text)
        text = re.sub(r"<\s*br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<\s*/p\s*>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)

    return text.strip()


def resolve_recipients(msg: EmailMessage) -> List[str]:
    reply_headers: Iterable[str] = msg.get_all("Reply-To", []) or msg.get_all(
        "From", []
    )
    addresses = [addr for _, addr in getaddresses(reply_headers) if addr]
    return addresses or [config.DEFAULT_FALLBACK_RECIPIENT]

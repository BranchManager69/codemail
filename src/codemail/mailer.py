"""Outbound email support."""

from __future__ import annotations

import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import make_msgid
from typing import Iterable, List, Optional

from . import config
from .log import log
from .markdown_render import render_markdown


def _join_addresses(addresses: Iterable[str]) -> str:
    return ", ".join(addresses)


def send_email(
    *,
    to_addrs: List[str],
    subject: str,
    body: str,
    session_id: str,
    in_reply_to: Optional[str] = None,
    references: Optional[List[str]] = None,
) -> str:
    mail_user = config.MAIL_USER
    password = config.resolve_mail_password()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = mail_user
    msg["To"] = _join_addresses(to_addrs)
    if config.REPLY_TO:
        msg["Reply-To"] = config.REPLY_TO

    if in_reply_to:
        msg["In-Reply-To"] = (
            in_reply_to if in_reply_to.startswith("<") else f"<{in_reply_to}>"
        )

    if references:
        dedup: List[str] = []
        for ref in references:
            norm = ref if ref.startswith("<") else f"<{ref}>"
            if norm not in dedup:
                dedup.append(norm)
        msg["References"] = " ".join(dedup)

    msg["X-Codex-Session"] = session_id
    msg["X-Codex-Processed"] = datetime.now(timezone.utc).isoformat()

    reply_body = f"Codex session: {session_id}\n\n{body.strip()}\n"
    msg.set_content(reply_body)
    msg.add_alternative(render_markdown(reply_body), subtype="html")

    message_id = make_msgid(domain="branch.bet")
    msg["Message-ID"] = message_id

    bcc = [mail_user]

    context = ssl.create_default_context()
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(config.MAIL_USER.split("@", 1)[0], password)
        server.send_message(msg, to_addrs=to_addrs + bcc)

    log(f"Sent response to {to_addrs} for session {session_id}")
    return message_id.strip("<>")

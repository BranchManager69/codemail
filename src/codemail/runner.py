"""Command-line entrypoint for Codemail."""

from __future__ import annotations

import json
import sys
from email.utils import getaddresses

from . import config
from .codex_client import run_codex
from .email_utils import (
    extract_body,
    extract_referenced_ids,
    normalize_msg_id,
    parse_bytes,
    resolve_recipients,
)
from .log import log
from .mailer import send_email
from .prompt import build_prompt
from .state import load_state, save_state


def main() -> int:
    raw = sys.stdin.buffer.read()
    if not raw:
        log("Received empty payload")
        return 75

    msg = parse_bytes(raw)

    message_id = (
        normalize_msg_id(msg.get("Message-ID"))
        or f"generated-{int(configure_time_ms())}"
    )
    from_addresses = msg.get_all("From", [])

    addresses = getaddresses(from_addresses)
    sender_email = addresses[0][1] if addresses else ""
    sender_display = addresses[0][0] or sender_email or "unknown"
    normalized_sender = sender_email.lower() if sender_email else ""
    mail_user_lower = config.MAIL_USER.lower()
    subject = msg.get("Subject", "(no subject)").strip()

    state = load_state()
    assignments = state.setdefault("messages", {})

    if msg.get("X-Codex-Processed"):
        log(f"Skipping already-processed message {message_id}")
        return 0

    if normalized_sender and normalized_sender == mail_user_lower:
        log(f"Skipping self-triggered message {message_id}")
        return 0

    if config.ALLOWED_SENDERS and normalized_sender not in config.ALLOWED_SENDERS:
        log(
            "Skipping message {mid} from unauthorized sender {sender}".format(
                mid=message_id,
                sender=normalized_sender or sender_display,
            )
        )
        notice_recipient = sender_email or config.DEFAULT_FALLBACK_RECIPIENT
        notice_subject = (
            f"Re: {subject}"
            if subject and not subject.lower().startswith("re:")
            else subject or "Codemail request"
        )
        notice_body = (
            "Codex task rejected.\n\n"
            "**Why**\n"
            "- Your address is not authorised to trigger Codemail.\n\n"
            "**What to do**\n"
            "- Contact the operator to be added to the allow-list."
        )
        try:
            send_email(
                to_addrs=[notice_recipient],
                subject=notice_subject,
                body=notice_body,
                session_id="unauthorised",
                in_reply_to=message_id,
                references=[message_id],
            )
        except Exception as exc:  # pragma: no cover - only on mail failures
            log(f"Failed to notify unauthorised sender: {exc}")
        return 0

    references = extract_referenced_ids(msg.get("References"))
    in_reply_to = normalize_msg_id(msg.get("In-Reply-To"))

    session_id = None
    header_session = msg.get("X-Codex-Session")
    if header_session:
        session_id = header_session.strip()
    else:
        for ref in [in_reply_to] + references:
            if not ref:
                continue
            norm = normalize_msg_id(ref)
            if norm and norm in assignments:
                session_id = assignments[norm]
                break

    log(f"START message={message_id} sender={sender_display} subject={subject}")

    body = extract_body(msg)
    prompt = build_prompt(sender_display, subject, body)

    rc, session_output, responses = run_codex(prompt, session_id)
    session_id = session_output or session_id or "unknown"

    assignments[message_id] = session_id

    status_line = (
        "Codex task completed." if rc == 0 else f"Codex exited with status {rc}."
    )
    response_text = status_line + "\n\n" + "\n\n".join(responses)

    if in_reply_to and in_reply_to not in references:
        references.append(in_reply_to)
    if message_id not in references:
        references.append(message_id)

    to_addrs = resolve_recipients(msg)
    try:
        response_mid = send_email(
            to_addrs=to_addrs,
            subject=f"Re: {subject}"
            if not subject.lower().startswith("re:")
            else subject,
            body=response_text,
            session_id=session_id,
            in_reply_to=message_id,
            references=references,
        )
        assignments[response_mid] = session_id
    except Exception as exc:
        log(f"Failed to send email: {exc}")
        save_state(state)
        return 75

    summary_text = " ".join(response_text.split())
    status_text = "success" if rc == 0 else "error"
    log(
        "SUMMARY status={status} session={session} recipients={recipients} task={task} text={text}".format(
            status=status_text,
            session=session_id,
            recipients=",".join(to_addrs),
            task=body.strip(),
            text=summary_text,
        )
    )

    result_payload = {
        "status": status_text,
        "session": session_id,
        "recipients": to_addrs,
        "summary": summary_text,
        "task": body.strip(),
    }
    print(json.dumps(result_payload))

    save_state(state)
    return 0


def configure_time_ms() -> int:
    import time

    return int(time.time() * 1000)


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    try:
        sys.exit(main())
    except Exception as exc:  # pragma: no cover - defensive logging
        log(f"Unhandled exception: {exc}")
        raise

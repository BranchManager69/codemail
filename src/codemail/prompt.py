"""Prompt construction for Codemail."""

from __future__ import annotations

import textwrap


def build_prompt(sender: str, subject: str, body: str) -> str:
    template = textwrap.dedent(
        f"""Incoming email task.
        Sender: {sender}
        Subject: {subject}

        Body:
        {body}

        Please interpret this email as instructions for the autonomous Codex agent.
        Execute any required actions within the server environment, maintain necessary records,
        and report everything in a structured Markdown summary (headings, bullet lists, bold emphasis)
        so the automation can render rich HTML. Do not email the original sender yourself unless the task
        explicitly requests it; otherwise the pipeline will deliver the summary. Reference the session id
        if applicable. You are authorized to act fully to satisfy the request.
        """
    ).strip()
    return template

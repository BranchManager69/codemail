"""Markdown to HTML rendering for Codemail."""

from __future__ import annotations

import html

try:  # pragma: no cover - optional dependency import
    import markdown  # type: ignore
except ImportError:  # pragma: no cover - fallback used when dependency missing
    markdown = None


CARD_TEMPLATE = """<html>
  <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color:#e2ebff; background:#060b16; margin:0;">
    <div style="max-width:640px;margin:28px auto;padding:32px 40px;background:#0c172d;border-radius:20px;border:1px solid rgba(94,148,255,0.25);box-shadow:0 20px 45px rgba(8,14,40,0.45);">
      <div style="font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:#7ca7ff;opacity:0.85;margin-bottom:20px;">Codex session update</div>
      <div style="font-size:15px;line-height:1.65;color:#e2ebff;">{body}</div>
    </div>
  </body>
</html>"""


def render_markdown(markdown_text: str) -> str:
    if markdown:
        html_body = markdown.markdown(markdown_text, extensions=["extra", "sane_lists"])
    else:  # pragma: no cover - executed only when dependency missing
        escaped = html.escape(markdown_text)
        html_body = "<br>".join(escaped.splitlines())
    return CARD_TEMPLATE.format(body=html_body)

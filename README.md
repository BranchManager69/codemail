# Codemail

Codemail turns an email inbox into an automation trigger for the Codex CLI.
Any message delivered to a configured address is piped into the runner, which
parses the mail, resumes the appropriate Codex session, executes the request,
and replies with a structured status report.

## Features

- End-to-end email ingestion with support for threading and session resume
- Structured Markdown summary rendered to HTML for human-friendly responses
- Optional BCC logging and message-ID → session mapping
- Configurable paths and credentials via environment variables
- Ready to integrate with Postfix aliases or `.forward` hooks

## Architecture

```
email → Postfix alias → codemail-runner → Codex CLI
                              ↓
                       status email (HTML)
```

The runner is split into small modules under `codemail/`:

- `config.py` – resolves paths, environment variables, and constants
- `log.py` – timestamped log utility
- `mailer.py` – reply/notification delivery
- `prompt.py` – builds the Codex prompt (Markdown instructions)
- `state.py` – message-ID to session tracking
- `codex_client.py` – shells out to `codex exec`
- `runner.py` – entrypoint wired to Postfix (`codemail-runner`)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Codemail relies on a few environment variables. Create an `.env` file or export
variables directly (use the `.env.example` template):

| Variable | Description |
| --- | --- |
| `CODEMAIL_MAIL_USER` | Address used for outbound mail (defaults to `codex@branch.bet`) |
| `CODEMAIL_MAIL_PASS` | Password for the SMTP account |
| `CODEMAIL_SMTP_HOST` | SMTP host (default `mail.branch.bet`) |
| `CODEMAIL_SMTP_PORT` | SMTP port (default `587`) |
| `CODEMAIL_STATE_PATH` | JSON file mapping message IDs to Codex sessions |
| `CODEMAIL_LOG_PATH` | Runner log file |
| `CODEMAIL_SESSION_ROOT` | Directory containing Codex CLI session transcripts |

Any variable not explicitly set falls back to the historical Codex defaults.

## Postfix / `.forward` Integration

Point the trigger address at the runner. Example `.forward+tasks` file:

```
|/usr/bin/env CODEMAIL_MAIL_USER=codex@branch.bet CODEMAIL_MAIL_PASS=... codemail-runner
```

Or use `/etc/aliases`:

```
tasks: "|/usr/bin/env CODEMAIL_MAIL_USER=codex@branch.bet CODEMAIL_MAIL_PASS=... codemail-runner"
```

After editing aliases run `newaliases` and reload Postfix.

## Development

- Format: `ruff format src tests`
- Tests: `pytest`
- Lint: `ruff check src tests`

## License

MIT

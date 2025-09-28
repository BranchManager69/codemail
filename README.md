<div align="center">

# Codemail

_Automate Codex CLI tasks straight from your inbox and reply with polished HTML reports._

[![shell](https://img.shields.io/badge/shell-bash-4EAA25.svg)](#install--first-run)
[![python](https://img.shields.io/badge/python-3.10%2B-3776AB.svg)](#requirements)
[![license](https://img.shields.io/github/license/BranchManager69/codemail.svg?color=blue)](./LICENSE)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/BranchManager69/codemail/pulls)

</div>

---

## Quick Navigation
- [Why Codemail](#why-codemail)
- [Requirements](#requirements)
- [Install & First Run](#install--first-run)
- [How It Works](#how-it-works)
- [Email Flow](#email-flow)
- [Configuration Cheat Sheet](#configuration-cheat-sheet)
- [Development](#development)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [License](#license)

## Why Codemail
Codemail turns an email inbox into a Codex automation trigger. Any message you send to the
configured address is parsed, mapped to the right Codex session, executed, and answered with a
single HTML recap (complete with headings, bullet lists, and Reply-To pointing back at the task
pipeline). No more juggling CLI windows when you just want to fire off a quick instruction from
your phone.

Highlights:
- **Drop-in Postfix hook** – point an alias or `.forward` at the runner and you are live.
- **Markdown-driven reports** – agent output is converted to a dark, shareable status card.
- **Session smart** – references and message IDs keep threads tied to Codex sessions.
- **Operator friendly** – logs, state, and transcripts stay in the same places you already use.

## Requirements
- Python 3.10+
- Codex CLI available on `PATH` (`codex exec`)
- Postfix (or another MTA) capable of piping mail to shell commands
- Access to the inbox you want Codemail to reply from (IMAP/SMTP credentials)

## Install & First Run
1. **Clone & install**
   ```bash
   cd ~/tools
   git clone https://github.com/BranchManager69/codemail.git
   cd codemail
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
2. **Copy the environment template**
   ```bash
   cp .env.example .env
   # edit .env with your SMTP user, password, and desired paths
   ```
3. **Create the wrapper used by Postfix**
   ```bash
   cat > bin/codemail-wrapper <<'EOF_WRAPPER'
   #!/bin/bash
   set -a
   source /home/branchmanager/tools/codemail/.env
   set +a
   exec /home/branchmanager/tools/codemail/.venv/bin/codemail-runner
   EOF_WRAPPER
   chmod +x bin/codemail-wrapper
   ```
4. **Point your trigger address at the wrapper**
   - `.forward+tasks`
     ```text
     |/home/branchmanager/tools/codemail/bin/codemail-wrapper
     ```
   - or `/etc/aliases`
     ```text
     tasks: "|/home/branchmanager/tools/codemail/bin/codemail-wrapper"
     ```
     After editing aliases run `newaliases`.
5. **Send a smoke test**
   Email `tasks@branch.bet` (or your alias) with a short request. You should receive a single HTML
   reply summarising the work, and `~/.codex/task-mail-runner.log` will show the `START`/`SUMMARY`
   entries.

## How It Works
```
email → Postfix alias/.forward → codemail-wrapper → codemail-runner → Codex CLI
                                               ↓
                                      HTML summary email
```

- `runner.py` handles parsing, prompt construction, Codex invocation, and reply delivery.
- `state.py` keeps a JSON map of message-id → session across runs.
- `markdown_render.py` turns Markdown summaries into the dark status card.
- `config.py` centralises env lookups so you can override paths or credentials.

## Email Flow
1. Incoming mail hits Postfix and is piped into `codemail-wrapper`.
2. The wrapper exports your `.env`, then executes `codemail-runner`.
3. The runner parses the message, finds any previous session, and shells out to `codex exec` in
   JSON streaming mode.
4. Codex emits Markdown summary text; Codemail renders it to HTML, sets `Reply-To` to the task
   address, and emails the sender.
5. Logs and state are appended so the next message in the thread resumes the same session.

## Configuration Cheat Sheet
| Variable | Default | Purpose |
| --- | --- | --- |
| `CODEMAIL_MAIL_USER` | `codex@branch.bet` | From/BCC address for replies |
| `CODEMAIL_MAIL_PASS` | *(required)* | SMTP password (or app password) |
| `CODEMAIL_PASSWORD_FILE` | `~/.codex_mail_pass` | Optional file-based password fallback |
| `CODEMAIL_SMTP_HOST` | `mail.branch.bet` | SMTP host |
| `CODEMAIL_SMTP_PORT` | `587` | SMTP port |
| `CODEMAIL_STATE_PATH` | `~/.codex/task_mail_map.json` | Session mapping file |
| `CODEMAIL_LOG_PATH` | `~/.codex/task-mail-runner.log` | Runner log |
| `CODEMAIL_SESSION_ROOT` | `~/.codex/sessions` | Codex transcript directory |
| `CODEMAIL_REPLY_TO` | `tasks@branch.bet` | Reply-To header used on summaries |
| `CODEMAIL_FALLBACK_RECIPIENT` | `branch@branch.bet` | Where to send reports if no recipient headers are found |
| `CODEMAIL_CODEX_BIN` | `codex` | Override Codex CLI binary name/path |
| `CODEMAIL_ALLOWED_SENDERS` | *(unset)* | Comma-separated list of email addresses allowed to trigger tasks; when set, Codemail rejects other senders and emails them a notice |

All variables can be set in the `.env` file or exported before the wrapper executes.

## Mail Security Hardening
Codemail assumes you already run a responsible MTA. To keep task traffic from being spoofed (or
flagged as spam) you should wire in the following before inviting other operators to email your
automation inbox.

### 1. SPF
- Publish an SPF TXT record for the domain you use in `CODEMAIL_MAIL_USER`.
- Example (Cloudflare → DNS): `v=spf1 mx include:_spf.google.com -all` – swap in the MTAs that
  are actually allowed to send on your behalf.

### 2. DKIM
1. Install and enable OpenDKIM (or your platform’s equivalent) and generate a key pair:
   ```bash
   sudo opendkim-genkey -D /etc/opendkim/keys/yourdomain -d yourdomain -s mail
   sudo chown opendkim:opendkim /etc/opendkim/keys/yourdomain/mail.private
   ```
2. Add a DNS TXT record named `mail._domainkey.yourdomain` whose value is the contents of
   `mail.txt` produced by the command above.
3. Wire the key into Postfix by adding to `/etc/opendkim/KeyTable` and `/etc/opendkim/SigningTable`,
   then set in `/etc/opendkim.conf`:
   ```text
   Domain                  yourdomain
   KeyFile                 /etc/opendkim/keys/yourdomain/mail.private
   Selector                mail
   Socket                  local:/var/spool/postfix/opendkim/opendkim.sock
   ```
4. Restart OpenDKIM and Postfix, then verify DNS propagation:
   ```bash
   sudo systemctl restart opendkim postfix
   sudo opendkim-testkey -d yourdomain -s mail -k /etc/opendkim/keys/yourdomain/mail.private
   ```

### 3. DMARC
1. Publish a DMARC TXT record (again via DNS) such as:
   ```text
   _dmarc.yourdomain  IN  TXT  "v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain; ruf=mailto:dmarc@yourdomain"
   ```
   Start with `p=none` if you want reports before enforcing policy.
2. Install and enable OpenDMARC (optional but recommended). Postfix main.cf should include:
   ```text
   smtpd_milters = inet:localhost:8893, inet:localhost:8891
   non_smtpd_milters = inet:localhost:8893, inet:localhost:8891
   ```
   (with 8893 as OpenDMARC and 8891 as OpenDKIM, adjust to match your install).
3. Watch the reports sent to the `rua` address—you can move to `p=reject` once you are satisfied
   that only authorized hosts are sending mail.

### 4. Allowed Sender List (Codemail)
- Use `CODEMAIL_ALLOWED_SENDERS` to whitelist trusted operators (example:
  `branch@branch.bet,nrsander@gmail.com`). Codemail politely rejects everyone else so you are aware
  of attempted usage.

> Tip: if you deploy Codemail on a fresh host, put the DKIM key, DMARC TXT, and allowed sender list
> into infrastructure-as-code or scripts so future reinstalls stay consistent.

## Development
```bash
source .venv/bin/activate
pip install -e .
ruff format src tests
ruff check src tests
pytest
```

## Troubleshooting & FAQ
- **Getting two emails per task?** Make sure the prompt hasn’t been modified—Codemail’s default
  instructs the agent not to send extra mail unless the task explicitly requires it.
- **Runner exits with status 75?** Check that the wrapper can read `.env` and that the SMTP
  credentials are valid.
- **Want multiple configurations?** Create separate `.env` files and wrapper scripts, then point
  different aliases at each.

## License
[MIT](./LICENSE)

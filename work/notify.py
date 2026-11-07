#!/usr/bin/env python3
"""Email the result of a sync run.

The nightly harvest already says what it did in the Actions log, which is fine
unless you want to know without opening a browser. This sends that summary to a
mailbox instead — on success, on a quiet night, and on failure.

    python3 work/notify.py --status success \
        --run-url https://github.com/owner/repo/actions/runs/123

It reads `state/sync.json`, which `work/sync_fr24.py` writes at the end of every
run, and sends through whichever transport the environment describes:

| transport | what to set |
|---|---|
| SMTP (default) | `MAIL_USER`, `MAIL_PASS` — the mail goes to that address unless `MAIL_TO` says otherwise; `SMTP_HOST` / `SMTP_PORT` optional |
| Resend | `MAIL_TO`, `RESEND_API_KEY`, optionally `MAIL_FROM` |
| SendGrid | `MAIL_TO`, `SENDGRID_API_KEY`, optionally `MAIL_FROM` |
| Mailgun | `MAIL_TO`, `MAILGUN_API_KEY`, `MAILGUN_DOMAIN`, optionally `MAIL_FROM` |

For a personal archive the SMTP route is the least fuss: a Gmail address and an
app password (My Account → Security → 2-Step Verification → App passwords) will
do, and it needs no domain to be verified.

With no credentials in the environment it prints the message and exits 0 — the
notification is opt-in, and a missing mailbox must never fail a night's work.

`--format issue` writes the same summary as a Markdown comment instead of an
email, for a tracking issue the workflow comments on. That needs no mailbox and
no password: GitHub sends the notification itself.

`--mode` decides what is worth an email: `always` (default), `work` (only when
tracks were fetched), or `never`.

    python3 work/notify.py --status success --dry-run
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import smtplib
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state" / "sync.json"

MODES = ("always", "work", "never")
DEFAULT_SMTP_PORT = 587


# --------------------------------------------------------------------------- #
# the message
# --------------------------------------------------------------------------- #

def read_state(path: Path = STATE) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def last_commit(root: Path = ROOT) -> str:
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%h %s"], cwd=root,
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _when(value) -> str:
    """`2026-11-06T13:00:00Z` -> `2026-11-06 13:00Z`, and nothing if unusable."""
    if not value or not isinstance(value, str):
        return ""
    stamp = value.replace("T", " ").replace(":00Z", "Z")
    return stamp.removesuffix("Z").strip() + "Z" if stamp.endswith("Z") else stamp


def build_message(state: dict, status: str, run_url: str = "",
                  repo: str = "") -> tuple[str, str]:
    """The subject and the body, from the run's own account of itself."""
    fetched = int(state.get("fetched") or 0)
    failed = int(state.get("failed") or 0)
    seen = int(state.get("seen") or 0)
    months = ", ".join(state.get("months") or []) or "none"
    airframes = state.get("airframes") or []
    window = state.get("window") or []
    notes = state.get("notes") or []
    ok = status == "success"

    if not ok:
        subject = f"FR24 sync: FAILED ({status})"
    elif fetched:
        subject = f"FR24 sync: {fetched} track{'s' if fetched != 1 else ''} ({months})"
    elif failed:
        subject = f"FR24 sync: {failed} fetch{'es' if failed != 1 else ''} failed"
    else:
        subject = "FR24 sync: nothing new"

    rows = [
        ("Result", status.upper() if not ok else "ran clean"),
        ("Window", f"{_when(window[0])} → {_when(window[1])}" if len(window) == 2 else "—"),
        ("Airframes", str(len(airframes)) if airframes else "—"),
        ("Flights", f"{seen} seen, {int(state.get('new') if state.get('new') is not None else fetched)} new"),
        ("Tracks", f"{fetched} fetched, {failed} failed"),
        ("Months", months),
    ]
    if repo:
        rows.append(("Repository", repo))
    commit = last_commit()
    if commit:
        rows.append(("On main", commit))

    width = max(len(label) for label, _ in rows)
    lines = ["Uganda Airlines archive — nightly sync", ""]
    lines += [f"{label.ljust(width)}  {value}" for label, value in rows]
    if run_url:
        lines += ["", f"Run  {run_url}"]

    if notes:
        lines += ["", "Notes"]
        lines += [f"  - {note}" for note in notes[-10:]]

    if not ok:
        lines += ["",
                  "The archive is not growing until this is fixed. The usual causes",
                  "are an expired Flightradar24 token, a rate limit, or a run of",
                  "playbacks the API would not serve."]
    elif not fetched:
        lines += ["", "Nothing new — either no flying since the last run, or it was all",
                  "already in the archive."]
    else:
        lines += ["", "The tracks are committed, the months are rebuilt, and the index",
                  "is up to date."]

    return subject, "\n".join(lines) + "\n"


def build_issue_comment(state: dict, status: str, run_url: str = "",
                        repo: str = "") -> str:
    """The same summary as a Markdown comment, for GitHub to notify on.

    A repository can be watched, an issue comment mailed — so this is the route
    that needs no mailbox, no app password and no third-party account.
    """
    fetched = int(state.get("fetched") or 0)
    failed = int(state.get("failed") or 0)
    seen = int(state.get("seen") or 0)
    new = int(state.get("new") or 0)
    months = ", ".join(state.get("months") or []) or "none"
    window = state.get("window") or []
    notes = state.get("notes") or []
    ok = status == "success"
    headline = ("**FR24 sync — ran clean**" if ok else f"**FR24 sync — {status.upper()}**")
    if fetched:
        headline += f" · {fetched} track{'s' if fetched != 1 else ''} fetched · {months}"
    elif ok:
        headline += " · nothing new"

    rows = [
        ("window", f"{_when(window[0])} → {_when(window[1])}" if len(window) == 2 else "—"),
        ("flights", f"{seen} seen, {new} new"),
        ("tracks", f"{fetched} fetched, {failed} failed"),
        ("months", months),
    ]
    commit = last_commit()
    if commit:
        rows.append(("on main", f"`{commit}`"))

    lines = [headline, "", "| | |", "|---|---|"]
    lines += [f"| {label} | {value} |" for label, value in rows]
    if run_url:
        lines += ["", f"[Run log]({run_url})"]
    if notes:
        lines += ["", "<details><summary>notes</summary>", ""]
        lines += [f"- {note}" for note in notes[-10:]]
        lines += ["", "</details>"]
    if not ok:
        lines += ["", "⚠️ The archive is not growing until this is fixed."]
    return "\n".join(lines) + "\n"


def build_test_message() -> tuple[str, str]:
    """What a one-click delivery test sends."""
    subject = "FR24 sync: test message"
    body = "\n".join([
        "Uganda Airlines archive — mailbox test",
        "",
        "If you are reading this, the nightly sync will reach you: the same",
        "credentials, the same transport, the same address. Nothing was fetched",
        "and nothing was committed to make it happen.",
        "",
        "The next real run reports itself here, whether it fills the archive or",
        "finds that nothing moved.",
        "",
    ])
    return subject, body


def worth_sending(state: dict, status: str, mode: str) -> bool:
    if mode == "never":
        return False
    if mode == "work":
        return status != "success" or int(state.get("fetched") or 0) > 0
    return True


# --------------------------------------------------------------------------- #
# the transports
# --------------------------------------------------------------------------- #

@dataclass
class Config:
    transport: str
    mail_to: str
    mail_from: str
    host: str = ""
    port: int = DEFAULT_SMTP_PORT
    user: str = ""
    password: str = ""
    api_key: str = ""
    domain: str = ""
    api_base: str = ""


def _clean_secret(value: str | None) -> str:
    """Undo what a clipboard does to an app password.

    Google shows them as four groups of four; the spaces are not part of the
    password. People also paste the quotes their shell or editor put around it,
    and a trailing newline comes along for free. Any of those turns a correct
    password into an authentication failure at 04:30 in the morning.
    """
    text = (value or "").strip().strip("'\"")
    return text.replace(" ", "").replace("\u00a0", "") if text else ""


def config_from_env() -> Config | None:
    user = (os.environ.get("MAIL_USER") or "").strip().strip("'\"")
    password = _clean_secret(os.environ.get("MAIL_PASS"))
    # mail yourself unless told otherwise: a login is a recipient
    mail_to = ((os.environ.get("MAIL_TO") or "").strip().strip("'\"")
               or (user if password else ""))
    mail_from = (os.environ.get("MAIL_FROM") or "").strip() or user or "fr24-archive@localhost"
    if not mail_to:
        return None
    if user and password:
        return Config(
            transport="smtp", mail_to=mail_to, mail_from=mail_from,
            host=(os.environ.get("SMTP_HOST") or "smtp.gmail.com").strip(),
            port=int(os.environ.get("SMTP_PORT") or DEFAULT_SMTP_PORT),
            user=user, password=password,
        )
    if (key := (os.environ.get("RESEND_API_KEY") or "").strip()):
        return Config(transport="resend", mail_to=mail_to, mail_from=mail_from,
                      api_key=key, api_base=(os.environ.get("MAIL_API_BASE") or
                                             "https://api.resend.com").rstrip("/"))
    if (key := (os.environ.get("SENDGRID_API_KEY") or "").strip()):
        return Config(transport="sendgrid", mail_to=mail_to, mail_from=mail_from,
                      api_key=key, api_base=(os.environ.get("MAIL_API_BASE") or
                                             "https://api.sendgrid.com").rstrip("/"))
    if (key := (os.environ.get("MAILGUN_API_KEY") or "").strip()) and \
            (domain := (os.environ.get("MAILGUN_DOMAIN") or "").strip()):
        return Config(transport="mailgun", mail_to=mail_to, mail_from=mail_from,
                      api_key=key, domain=domain,
                      api_base=(os.environ.get("MAIL_API_BASE") or
                                "https://api.mailgun.net").rstrip("/"))
    return None


def describe(config: Config) -> str:
    target = config.mail_to
    name, _, domain = target.partition("@")
    masked = f"{name[:1]}{'*' * max(1, len(name) - 1)}@{domain}" if domain else target
    return f"{config.transport} → {masked}"


def send_smtp(config: Config, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = config.mail_from
    message["To"] = config.mail_to
    message["Subject"] = subject
    message.set_content(body)
    context = ssl.create_default_context()
    if config.port == 465:
        with smtplib.SMTP_SSL(config.host, config.port, timeout=30,
                              context=context) as server:
            server.login(config.user, config.password)
            server.send_message(message)
        return
    with smtplib.SMTP(config.host, config.port, timeout=30) as server:
        server.ehlo()
        server.starttls(context=context)
        server.login(config.user, config.password)
        server.send_message(message)


def _post_json(url: str, payload: dict, headers: dict) -> None:
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        response.read()


def send_http(config: Config, subject: str, body: str) -> None:
    if config.transport == "resend":
        _post_json(f"{config.api_base}/emails", {
            "from": config.mail_from, "to": [config.mail_to],
            "subject": subject, "text": body,
        }, {"Authorization": f"Bearer {config.api_key}"})
        return
    if config.transport == "sendgrid":
        _post_json(f"{config.api_base}/v3/mail/send", {
            "personalizations": [{"to": [{"email": config.mail_to}]}],
            "from": {"email": config.mail_from},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        }, {"Authorization": f"Bearer {config.api_key}"})
        return
    if config.transport == "mailgun":
        data = urllib.parse.urlencode({
            "from": config.mail_from, "to": config.mail_to,
            "subject": subject, "text": body,
        }).encode("utf-8")
        token = base64.b64encode(f"api:{config.api_key}".encode()).decode()
        request = urllib.request.Request(
            f"{config.api_base}/v3/{config.domain}/messages", data=data,
            headers={"Authorization": f"Basic {token}",
                     "Content-Type": "application/x-www-form-urlencoded"},
            method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
        return
    raise ValueError(f"unknown transport {config.transport}")


def send(config: Config, subject: str, body: str) -> None:
    if config.transport == "smtp":
        send_smtp(config, subject, body)
    else:
        send_http(config, subject, body)


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Email the result of a sync run.")
    parser.add_argument("--status", default="success",
                        help="the job's outcome: success, failure, cancelled")
    parser.add_argument("--run-url", default="", help="link to the Actions run")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--mode", choices=MODES,
                        default=(os.environ.get("MAIL_MODE") or "always").strip(),
                        help="always (default), work (only when tracks were fetched), never")
    parser.add_argument("--state", default=str(STATE), help="path to state/sync.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the message instead of sending it")
    parser.add_argument("--format", choices=("text", "issue"), default="text",
                        help="text for an email, issue for a Markdown comment")
    parser.add_argument("--test", action="store_true",
                        help="send a delivery test instead of a run summary")
    parser.add_argument("--require-config", action="store_true",
                        help="fail when nothing is configured, so a green check "
                             "means an email really left")
    parser.add_argument("--always-exit-0", action="store_true",
                        help="never fail, whatever the transport does")
    args = parser.parse_args(argv)

    if args.test:
        return _deliver(*build_test_message(), dry_run=args.dry_run,
                        always_exit_0=args.always_exit_0,
                        require_config=args.require_config)

    state = read_state(Path(args.state))
    if not worth_sending(state, args.status, args.mode):
        # stderr, so that --format issue yields an empty body and the caller can
        # tell "nothing to report" from "report this"
        print(f"nothing worth sending (mode {args.mode}, status {args.status})",
              file=sys.stderr)
        return 0
    if args.format == "issue":
        print(build_issue_comment(state, args.status, args.run_url, args.repo), end="")
        return 0

    subject, body = build_message(state, args.status, args.run_url, args.repo)
    return _deliver(subject, body, dry_run=args.dry_run,
                    always_exit_0=args.always_exit_0)


def _deliver(subject: str, body: str, dry_run: bool = False,
             always_exit_0: bool = False, require_config: bool = False) -> int:
    """Print, or send, and decide what a failure here is worth."""
    if dry_run:
        print(f"To: (dry run)\nSubject: {subject}\n\n{body}")
        return 0

    config = config_from_env()
    if config is None:
        if require_config and not always_exit_0:
            print("no mail credentials: set SYNC_MAIL_USER and SYNC_MAIL_PASS "
                  "(or an API key) before expecting a delivery", file=sys.stderr)
            return 1
        print("no mail credentials in the environment — message not sent:\n")
        print(f"Subject: {subject}\n\n{body}")
        return 0

    try:
        send(config, subject, body)
    except Exception as error:  # noqa: BLE001 - a mail problem is not the night's problem
        print(f"could not send the mail via {config.transport}: "
              f"{type(error).__name__}: {error}", file=sys.stderr)
        return 0 if always_exit_0 else 1
    print(f"sent to {describe(config)}: {subject}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Tests for work/notify.py — the email the sync sends when it is done.

    python3 -m unittest discover -s tests -v

No mailbox, no network: SMTP is a stand-in, and the HTTP transports are pointed at
a server the test raises for the length of one assertion.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "work"))

import notify  # noqa: E402

STATE = {
    "window": ["2026-11-05T11:00:00Z", "2026-11-06T13:00:00Z"],
    "airframes": ["5X-EQU", "5X-KOB", "ET-APL"],
    "seen": 74, "new": 31, "fetched": 31, "failed": 0,
    "months": ["2026-11"], "notes": [],
}
QUIET = {**STATE, "seen": 74, "new": 0, "fetched": 0, "months": []}


def env(**values):
    """A clean environment for one assertion."""
    keys = ["MAIL_TO", "MAIL_USER", "MAIL_PASS", "MAIL_FROM", "SMTP_HOST",
            "SMTP_PORT", "RESEND_API_KEY", "SENDGRID_API_KEY", "MAILGUN_API_KEY",
            "MAILGUN_DOMAIN", "MAIL_API_BASE", "MAIL_MODE", "GITHUB_REPOSITORY"]
    stripped = {key: "" for key in keys}
    stripped.update(values)
    return mock.patch.dict(os.environ, stripped, clear=False)


class MessageTests(unittest.TestCase):
    def test_a_night_with_tracks_says_so_in_the_subject(self):
        subject, body = notify.build_message(STATE, "success")
        self.assertEqual(subject, "FR24 sync: 31 tracks (2026-11)")
        self.assertIn("2026-11-05 11:00Z → 2026-11-06 13:00Z", body)
        self.assertIn("31 fetched, 0 failed", body)
        self.assertIn("74 seen, 31 new", body)
        self.assertIn("the months are rebuilt", body)

    def test_a_quiet_night_says_nothing_new(self):
        subject, body = notify.build_message(QUIET, "success")
        self.assertEqual(subject, "FR24 sync: nothing new")
        self.assertIn("Nothing new", body)

    def test_a_failed_run_says_so(self):
        subject, body = notify.build_message(STATE, "failure")
        self.assertEqual(subject, "FR24 sync: FAILED (failure)")
        self.assertIn("not growing until this is fixed", body)

    def test_the_run_link_and_notes_are_included(self):
        state = {**STATE, "notes": ["5X-KOB UR720: HTTPStatusError: 429"]}
        _, body = notify.build_message(state, "success",
                                       run_url="https://example.test/run/7",
                                       repo="owner/repo")
        self.assertIn("https://example.test/run/7", body)
        self.assertIn("HTTPStatusError: 429", body)
        self.assertIn("owner/repo", body)

    def test_a_missing_state_file_still_produces_a_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = notify.read_state(Path(tmp) / "absent.json")
        subject, _ = notify.build_message(state, "success")
        self.assertEqual(subject, "FR24 sync: nothing new")


class BacklogTests(unittest.TestCase):
    """The sweep's numbers, carried into what the night reports."""

    def test_nothing_missing_says_nothing(self):
        self.assertEqual(notify.backlog_line({}), "")

    def test_the_line_counts_what_is_open_parked_and_closed(self):
        text = notify.backlog_line({"open": 189, "parked": 6, "closed": 22})
        self.assertEqual(text, "189 sectors still missing, 6 given up on, "
                               "22 closed so far")

    def test_one_sector_is_not_sectors(self):
        self.assertIn("1 sector still missing", notify.backlog_line({"open": 1}))

    def test_the_email_carries_the_backlog(self):
        with mock.patch.object(notify, "read_sweep",
                               return_value={"open": 12, "closed": 3}):
            _, body = notify.build_message(STATE, "success")
        self.assertIn("12 sectors still missing, 3 closed so far", body)

    def test_the_issue_comment_carries_it_too(self):
        with mock.patch.object(notify, "read_sweep",
                               return_value={"open": 12, "closed": 3}):
            comment = notify.build_issue_comment(STATE, "success")
        self.assertIn("| missing | 12 sectors still missing, 3 closed so far |", comment)

    def test_a_missing_sweep_file_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(notify.read_sweep(Path(tmp) / "absent.json"), {})


class IssueFormatTests(unittest.TestCase):
    """The route that needs no mailbox: GitHub sends the notification itself."""

    def test_a_night_with_tracks_reads_as_a_comment(self):
        comment = notify.build_issue_comment(
            STATE, "success", run_url="https://example.test/run/7", repo="owner/repo")
        self.assertIn("**FR24 sync — ran clean** · 31 tracks fetched · 2026-11", comment)
        self.assertIn("| tracks | 31 fetched, 0 failed |", comment)
        self.assertIn("[Run log](https://example.test/run/7)", comment)
        self.assertNotIn("not growing", comment)

    def test_a_quiet_night_says_nothing_new(self):
        comment = notify.build_issue_comment(QUIET, "success")
        self.assertIn("nothing new", comment)

    def test_a_failure_warns_in_the_comment(self):
        comment = notify.build_issue_comment(STATE, "failure")
        self.assertIn("**FR24 sync — FAILURE**", comment)
        self.assertIn("not growing until this is fixed", comment)

    def test_the_comment_can_be_printed_without_any_credentials(self):
        with env(MAIL_TO="", MAIL_USER="", MAIL_PASS=""):
            with mock.patch("builtins.print") as printed:
                code = notify.main(["--status", "success", "--format", "issue",
                                    "--state", "/tmp/does-not-exist.json"])
        self.assertEqual(code, 0)
        self.assertIn("FR24 sync", printed.call_args[0][0])

    def test_work_mode_prints_nothing_on_a_quiet_night(self):
        """An empty body is how the workflow knows not to comment."""
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "sync.json"
            state.write_text(json.dumps(QUIET), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = notify.main(["--status", "success", "--format", "issue",
                                    "--mode", "work", "--state", str(state)])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "")


class ModeTests(unittest.TestCase):
    def test_always_sends_even_on_a_quiet_night(self):
        self.assertTrue(notify.worth_sending(QUIET, "success", "always"))

    def test_work_mode_stays_quiet_unless_something_was_fetched(self):
        self.assertFalse(notify.worth_sending(QUIET, "success", "work"))
        self.assertTrue(notify.worth_sending(STATE, "success", "work"))

    def test_work_mode_still_reports_a_failure(self):
        self.assertTrue(notify.worth_sending(QUIET, "failure", "work"))

    def test_never_sends_nothing(self):
        self.assertFalse(notify.worth_sending(STATE, "failure", "never"))


class TransportTests(unittest.TestCase):
    def test_smtp_is_chosen_when_a_login_is_present(self):
        with env(MAIL_TO="me@example.com", MAIL_USER="me@example.com",
                 MAIL_PASS="app-password", SMTP_HOST="smtp.gmail.com"):
            config = notify.config_from_env()
        self.assertEqual(config.transport, "smtp")
        self.assertEqual(config.host, "smtp.gmail.com")
        self.assertEqual(config.port, 587)

    def test_no_credentials_means_no_config(self):
        with env(MAIL_TO="me@example.com"):
            self.assertIsNone(notify.config_from_env())

    def test_a_login_without_a_recipient_mails_itself(self):
        with env(MAIL_USER="me@example.com", MAIL_PASS="x"):
            config = notify.config_from_env()
        self.assertEqual(config.mail_to, "me@example.com")

    def test_an_api_key_is_enough(self):
        with env(MAIL_TO="me@example.com", RESEND_API_KEY="re_123"):
            config = notify.config_from_env()
        self.assertEqual(config.transport, "resend")

    def test_the_recipient_is_masked_in_the_log(self):
        with env(MAIL_TO="jonathan@example.com", MAIL_USER="u", MAIL_PASS="p"):
            config = notify.config_from_env()
        described = notify.describe(config)
        self.assertNotIn("jonathan", described)
        self.assertIn("example.com", described)

    def test_smtp_sends_a_message_with_the_subject(self):
        fake = mock.MagicMock()
        fake.__enter__.return_value = fake
        with env(MAIL_TO="me@example.com", MAIL_USER="me@example.com",
                 MAIL_PASS="app-password"):
            config = notify.config_from_env()
        with mock.patch.object(notify.smtplib, "SMTP", return_value=fake):
            notify.send(config, "FR24 sync: 31 tracks (2026-11)", "body\n")
        fake.starttls.assert_called_once()
        fake.login.assert_called_once_with("me@example.com", "app-password")
        message = fake.send_message.call_args[0][0]
        self.assertEqual(message["Subject"], "FR24 sync: 31 tracks (2026-11)")
        self.assertEqual(message["To"], "me@example.com")

    def test_a_pasted_app_password_is_cleaned(self):
        """Google shows four groups of four; the spaces and quotes are not secret."""
        with env(MAIL_USER=" me@example.com ", MAIL_PASS=' "abcd efgh ijkl mnop" \n'):
            config = notify.config_from_env()
        self.assertEqual(config.password, "abcdefghijklmnop")
        self.assertEqual(config.mail_to, "me@example.com")

    def test_the_http_transport_posts_the_message_it_was_given(self):
        captured = {}

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802 - the name is the framework's
                length = int(self.headers.get("Content-Length") or 0)
                captured["path"] = self.path
                captured["auth"] = self.headers.get("Authorization")
                captured["body"] = json.loads(self.rfile.read(length) or b"{}")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"id":"1"}')

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()
        with env(MAIL_TO="me@example.com", RESEND_API_KEY="re_123",
                 MAIL_API_BASE=f"http://127.0.0.1:{server.server_port}"):
            config = notify.config_from_env()
            notify.send(config, "FR24 sync: 1 track (2026-11)", "body text")
        thread.join(timeout=5)
        server.server_close()

        self.assertEqual(captured["path"], "/emails")
        self.assertEqual(captured["auth"], "Bearer re_123")
        self.assertEqual(captured["body"]["to"], ["me@example.com"])
        self.assertEqual(captured["body"]["subject"], "FR24 sync: 1 track (2026-11)")
        self.assertEqual(captured["body"]["text"], "body text")


class DeliveryTestTests(unittest.TestCase):
    """The one-click check: prove the mailbox without waiting for a night."""

    def test_the_test_message_says_it_is_a_test(self):
        subject, body = notify.build_test_message()
        self.assertEqual(subject, "FR24 sync: test message")
        self.assertIn("mailbox test", body)
        self.assertIn("nothing was committed", body)

    def test_a_test_is_sent_even_when_a_real_night_would_be_silent(self):
        with env(MAIL_TO="me@example.com", MAIL_USER="me@example.com",
                 MAIL_PASS="app-password", MAIL_MODE="work"):
            with mock.patch.object(notify, "send") as sender:
                code = notify.main(["--test", "--state", "/tmp/does-not-exist.json"])
        self.assertEqual(code, 0)
        sender.assert_called_once()

    def test_a_required_test_fails_when_nothing_is_configured(self):
        """Green must mean an email left, not that the script had nothing to do."""
        with env():
            code = notify.main(["--test", "--require-config"])
        self.assertEqual(code, 1)

    def test_a_required_test_passes_when_it_really_sends(self):
        with env(MAIL_TO="me@example.com", MAIL_USER="me@example.com",
                 MAIL_PASS="app-password"):
            with mock.patch.object(notify, "send") as sender:
                code = notify.main(["--test", "--require-config"])
        self.assertEqual(code, 0)
        sender.assert_called_once()

    def test_a_test_can_be_dry_run(self):
        with env(MAIL_TO="me@example.com", MAIL_USER="me@example.com",
                 MAIL_PASS="app-password"):
            with mock.patch.object(notify, "send") as sender:
                code = notify.main(["--test", "--dry-run"])
        self.assertEqual(code, 0)
        sender.assert_not_called()


class MainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / "sync.json"
        self.state.write_text(json.dumps(STATE), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_prints_and_sends_nothing(self):
        with env(MAIL_TO="me@example.com", MAIL_USER="u", MAIL_PASS="p"):
            with mock.patch.object(notify, "send") as sender:
                code = notify.main(["--status", "success", "--state", str(self.state),
                                    "--dry-run"])
        self.assertEqual(code, 0)
        sender.assert_not_called()

    def test_without_credentials_it_says_so_and_does_not_fail(self):
        with env():
            with mock.patch.object(notify, "send") as sender:
                code = notify.main(["--status", "success", "--state", str(self.state)])
        self.assertEqual(code, 0)
        sender.assert_not_called()

    def test_a_broken_mailbox_does_not_fail_the_night(self):
        with env(MAIL_TO="me@example.com", MAIL_USER="u", MAIL_PASS="p"):
            with mock.patch.object(notify, "send", side_effect=OSError("no route")):
                code = notify.main(["--status", "success", "--state", str(self.state)])
                soft = notify.main(["--status", "success", "--state", str(self.state),
                                    "--always-exit-0"])
        self.assertEqual(code, 1)
        self.assertEqual(soft, 0)

    def test_mode_work_skips_a_quiet_night(self):
        self.state.write_text(json.dumps(QUIET), encoding="utf-8")
        with env(MAIL_TO="me@example.com", MAIL_USER="u", MAIL_PASS="p"):
            with mock.patch.object(notify, "send") as sender:
                code = notify.main(["--status", "success", "--mode", "work",
                                    "--state", str(self.state)])
        self.assertEqual(code, 0)
        sender.assert_not_called()


if __name__ == "__main__":
    unittest.main()

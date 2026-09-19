"""Real mailboxes: IMAP (Gmail, Outlook, any provider) and uploaded .eml files.

Both parse RFC-822 messages into the same `Email` model the pipeline already
consumes, and cache attachments on disk so `read_bytes()` works unchanged.
Credentials are held in memory for the session only, never written to disk.
"""
from __future__ import annotations

import email as email_lib
import hashlib
import html
import imaplib
import re
from email.header import decode_header, make_header
from email.message import Message
from pathlib import Path
from typing import Optional

from .inbox import InboxRepository
from .models import Email

DOC_EXT = (".txt", ".pdf", ".docx", ".xlsx", ".xlsm")


def _decode(value: Optional[str]) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def _body_text(msg: Message) -> str:
    plain, html_part = "", ""
    for part in msg.walk():
        if part.get_content_disposition() == "attachment":
            continue
        ctype = part.get_content_type()
        if ctype not in ("text/plain", "text/html"):
            continue
        payload = part.get_payload(decode=True) or b""
        text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        if ctype == "text/plain" and not plain:
            plain = text
        elif ctype == "text/html" and not html_part:
            html_part = text
    if plain:
        return plain
    text = re.sub(r"<(script|style).*?</\1>", " ", html_part, flags=re.S | re.I)
    text = re.sub(r"<br\s*/?>|</p>|</div>", "\n", text, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"[ \t]+", " ", text).strip()


class MailParser:
    """RFC-822 bytes -> (Email, {attachment_path: bytes})."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

    def parse(self, raw: bytes, email_id: str) -> Email:
        msg = email_lib.message_from_bytes(raw)
        attachments: list[str] = []
        for part in msg.walk():
            name = part.get_filename()
            if not name:
                continue
            name = _decode(name)
            if not name.lower().endswith(DOC_EXT):
                continue
            data = part.get_payload(decode=True) or b""
            safe = re.sub(r"[^\w.\-]+", "_", name)
            rel = f"attachments/{email_id}_{safe}"
            path = self.cache_dir / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            attachments.append(rel)
        return Email(email_id=email_id, **{"from": _decode(msg.get("From"))},
                     subject=_decode(msg.get("Subject")), body=_body_text(msg), attachments=attachments)


class UploadInbox(InboxRepository):
    """Emails added one at a time from uploaded .eml files."""

    def __init__(self, cache_dir: Path):
        self.parser = MailParser(cache_dir)
        self.cache_dir = cache_dir
        self._emails: dict[str, Email] = {}

    def add(self, raw: bytes, name: str = "upload") -> Email:
        digest = hashlib.sha1(raw).hexdigest()[:8]
        eid = f"upload_{digest}"
        e = self.parser.parse(raw, eid)
        self._emails[eid] = e
        return e

    def emails(self):
        return list(self._emails.values())

    def get(self, email_id):
        if email_id not in self._emails:
            raise FileNotFoundError(email_id)
        return self._emails[email_id]

    def read_bytes(self, attachment_path):
        return (self.cache_dir / attachment_path).read_bytes()


class ImapInbox(InboxRepository):
    """Read-only view of an IMAP folder. Gmail: host imap.gmail.com, an App
    Password (2-step verification on). Outlook: outlook.office365.com."""

    def __init__(self, host: str, user: str, password: str, cache_dir: Path,
                 folder: str = "INBOX", limit: int = 100, port: int = 993):
        self.host, self.user, self._password = host, user, password
        self.folder, self.limit, self.port = folder, limit, port
        self.parser = MailParser(cache_dir)
        self.cache_dir = cache_dir
        self._emails: dict[str, Email] = {}

    def _connect(self) -> imaplib.IMAP4_SSL:
        conn = imaplib.IMAP4_SSL(self.host, self.port)
        conn.login(self.user, self._password)
        conn.select(self.folder, readonly=True)
        return conn

    def test(self) -> int:
        conn = self._connect()
        try:
            _, data = conn.uid("search", None, "ALL")
            return len(data[0].split())
        finally:
            conn.logout()

    def refresh(self) -> list[Email]:
        conn = self._connect()
        try:
            _, data = conn.uid("search", None, "ALL")
            uids = data[0].split()[-self.limit:]
            fresh: list[Email] = []
            for uid in reversed(uids):
                eid = f"imap_{uid.decode()}"
                if eid in self._emails:
                    continue
                _, msg_data = conn.uid("fetch", uid, "(RFC822)")
                raw = next((p[1] for p in msg_data if isinstance(p, tuple)), b"")
                if raw:
                    e = self.parser.parse(raw, eid)
                    self._emails[eid] = e
                    fresh.append(e)
            return fresh
        finally:
            conn.logout()

    def emails(self):
        if not self._emails:
            self.refresh()
        return list(self._emails.values())

    def get(self, email_id):
        if email_id not in self._emails:
            raise FileNotFoundError(email_id)
        return self._emails[email_id]

    def read_bytes(self, attachment_path):
        return (self.cache_dir / attachment_path).read_bytes()


class CompositeInbox(InboxRepository):
    """The dataset plus any connected mailbox and uploaded emails, as one inbox."""

    def __init__(self, base: InboxRepository):
        self.base = base
        self.sources: dict[str, InboxRepository] = {}

    def add_source(self, name: str, source: InboxRepository) -> None:
        self.sources[name] = source

    def remove_source(self, name: str) -> None:
        self.sources.pop(name, None)

    def _all(self):
        yield self.base
        yield from self.sources.values()

    def emails(self):
        out: list[Email] = []
        for src in self._all():
            out.extend(src.emails())
        return out

    def get(self, email_id):
        for src in self._all():
            try:
                return src.get(email_id)
            except FileNotFoundError:
                continue
        raise FileNotFoundError(email_id)

    def read_bytes(self, attachment_path):
        for src in self._all():
            try:
                return src.read_bytes(attachment_path)
            except (FileNotFoundError, OSError):
                continue
        raise FileNotFoundError(attachment_path)

    def source_of(self, email_id: str) -> str:
        if email_id.startswith("imap_"):
            return "mailbox"
        if email_id.startswith("upload_"):
            return "upload"
        return "dataset"

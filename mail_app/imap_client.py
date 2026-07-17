"""
IMAP + email parsing helpers for Mail Viewer.
"""

from __future__ import annotations

import imaplib
import socket
from datetime import timedelta
from email import message_from_bytes
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from typing import Any

from django.utils import timezone


class IMAPAuthError(Exception):
    pass


class IMAPConnectionError(Exception):
    pass


def _decode_mime_header(value):
    if not value:
        return ""

    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)


def _decode_part_payload(part):
    try:
        payload = part.get_payload(decode=True)
    except Exception:
        return ""

    if payload is None:
        return ""

    charset = part.get_content_charset() or "utf-8"

    try:
        return payload.decode(charset, errors="replace")
    except Exception:
        return payload.decode("utf-8", errors="replace")


def extract_plain_text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            disp = (part.get_content_disposition() or "").lower()

            if disp == "attachment":
                continue

            if part.get_content_type() == "text/plain":
                text = _decode_part_payload(part)

                if text.strip():
                    return text

        return ""

    if msg.get_content_type() == "text/plain":
        return _decode_part_payload(msg)

    return ""


def _date_from_msg(msg):
    raw = msg.get("Date")

    if raw:
        try:
            dt = parsedate_to_datetime(raw)

            if dt:
                if timezone.is_naive(dt):
                    return timezone.make_aware(
                        dt,
                        timezone.get_current_timezone()
                    )
                return dt
        except Exception:
            pass

    return timezone.now()


def _sender_from_msg(msg):
    from_hdr = msg.get("From") or msg.get("Sender") or ""
    return _decode_mime_header(from_hdr).strip() or "(unknown sender)"


def _subject_from_msg(msg):
    subj = msg.get("Subject") or ""
    return _decode_mime_header(subj).strip() or "(no subject)"


def _parse_fetch_response(fetch_data: list[Any]):
    raw = None

    for item in fetch_data:
        if isinstance(item, tuple) and len(item) == 2:
            payload = item[1]

            if isinstance(payload, (bytes, bytearray)):
                raw = bytes(payload)

    return raw


def fetch_recent_emails_for_storage(
    email_address,
    password,
    *,
    host,
    port,
):
    """
    Fetch ONLY latest 30 emails from last 30 days.
    """

    try:
        conn = imaplib.IMAP4_SSL(host, port)

    except (socket.gaierror, socket.timeout, OSError) as exc:
        raise IMAPConnectionError(f"Could not reach server: {exc}")

    try:
        try:
            typ, _ = conn.login(email_address, password)

        except imaplib.IMAP4.error:
            raise IMAPAuthError("Invalid Gmail credentials.")

        if typ != "OK":
            raise IMAPAuthError("Mail server rejected login.")

        typ, _ = conn.select("INBOX", readonly=True)

        if typ != "OK":
            raise IMAPConnectionError("Could not open inbox.")

        since_date = (
            timezone.now() - timedelta(days=30)
        ).strftime("%d-%b-%Y")

        typ, data = conn.search(None, "SINCE", since_date)

        if typ != "OK" or not data:
            raise IMAPConnectionError("Mailbox search failed.")

        ids = data[0].split()

        if not ids:
            return []

        # ONLY LATEST 30 EMAILS
        ids = ids[-30:]
        ids.reverse()

        rows = []

        for msg_id in ids:
            typ, fetch_data = conn.fetch(msg_id, "(BODY.PEEK[])")

            if typ != "OK":
                continue

            raw = _parse_fetch_response(fetch_data)

            if not raw:
                continue

            try:
                msg = message_from_bytes(raw)

            except Exception:
                continue

            rows.append(
                {
                    "sender": _sender_from_msg(msg),
                    "subject": _subject_from_msg(msg),
                    "message": extract_plain_text(msg).strip(),
                    "email_date": _date_from_msg(msg),
                }
            )

        return rows

    finally:
        try:
            conn.logout()
        except Exception:
            pass
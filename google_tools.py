"""
tools/google_tools.py
─────────────────────
Google Calendar and Gmail tools.

Requirements:
  pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

Setup (one-time):
  1. Go to console.cloud.google.com
  2. Enable Gmail API + Google Calendar API
  3. Create OAuth 2.0 credentials (Desktop app)
  4. Download JSON → rename to credentials.json → place next to app.py
  5. Click "Connect Google Account" in the sidebar → browser login → done
"""

import os
import base64
import datetime
from email.mime.text import MIMEText
from langchain_core.tools import tool
from config import GOOGLE_SCOPES


# ── OAuth helper ──────────────────────────────────────────────────────────────

def get_google_creds():
    """
    Returns valid Google OAuth2 credentials.
    Caches token.json so the user only logs in once.
    Returns None if credentials.json is missing or auth fails.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow

        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", GOOGLE_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists("credentials.json"):
                    return None
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", GOOGLE_SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as f:
                f.write(creds.to_json())

        return creds
    except Exception:
        return None


# ── Calendar tools ────────────────────────────────────────────────────────────

def build_calendar_tools() -> list:
    creds = get_google_creds()
    if creds is None:
        return []

    try:
        from googleapiclient.discovery import build as gbuild
        service = gbuild("calendar", "v3", credentials=creds)

        @tool
        def google_calendar_list(days_ahead: int = 7, max_results: int = 10) -> str:
            """
            List the user's upcoming Google Calendar events.
            Use when the user asks about their schedule, meetings, or upcoming events.
            Default: next 7 days.
            """
            try:
                now   = datetime.datetime.utcnow().isoformat() + "Z"
                until = (
                    datetime.datetime.utcnow() + datetime.timedelta(days=days_ahead)
                ).isoformat() + "Z"

                result = service.events().list(
                    calendarId="primary",
                    timeMin=now, timeMax=until,
                    maxResults=max_results,
                    singleEvents=True, orderBy="startTime",
                ).execute()

                events = result.get("items", [])
                if not events:
                    return f"No events found in the next {days_ahead} day(s)."

                lines = []
                for e in events:
                    start    = e["start"].get("dateTime", e["start"].get("date", "?"))
                    title    = e.get("summary", "No title")
                    location = e.get("location", "")
                    loc_str  = f" @ {location}" if location else ""
                    lines.append(f"• **{title}**{loc_str} — {start}")

                return f"**Your upcoming events (next {days_ahead} days):**\n" + "\n".join(lines)
            except Exception as ex:
                return f"Calendar list error: {ex}"

        @tool
        def google_calendar_create(
            title: str,
            start_datetime: str,
            end_datetime: str,
            description: str = "",
            attendees: str = "",
        ) -> str:
            """
            Create a new event in Google Calendar.

            Args:
              title          : Event title / summary
              start_datetime : ISO 8601 format e.g. '2025-06-01T10:00:00'
              end_datetime   : ISO 8601 format e.g. '2025-06-01T11:00:00'
              description    : Optional event description
              attendees      : Comma-separated email addresses (optional)

            Use when the user asks to schedule a meeting, set a reminder, or create an event.
            """
            try:
                body: dict = {
                    "summary":     title,
                    "description": description,
                    "start": {"dateTime": start_datetime, "timeZone": "Asia/Kolkata"},
                    "end":   {"dateTime": end_datetime,   "timeZone": "Asia/Kolkata"},
                }
                if attendees:
                    body["attendees"] = [
                        {"email": e.strip()}
                        for e in attendees.split(",") if e.strip()
                    ]
                created = service.events().insert(
                    calendarId="primary", body=body
                ).execute()
                return (
                    f"✅ Event created: **{created.get('summary')}**\n"
                    f"🔗 {created.get('htmlLink', 'No link')}"
                )
            except Exception as ex:
                return f"Calendar create error: {ex}"

        return [google_calendar_list, google_calendar_create]

    except ImportError:
        print("⚠️  google-api-python-client not installed.")
        return []


# ── Gmail tools ───────────────────────────────────────────────────────────────

def build_gmail_tools() -> list:
    creds = get_google_creds()
    if creds is None:
        return []

    try:
        from googleapiclient.discovery import build as gbuild
        service = gbuild("gmail", "v1", credentials=creds)

        def _headers(msg_data: dict) -> dict:
            return {
                h["name"]: h["value"]
                for h in msg_data.get("payload", {}).get("headers", [])
            }

        def _body(msg_data: dict) -> str:
            payload = msg_data.get("payload", {})
            if "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain":
                        data = part.get("body", {}).get("data", "")
                        if data:
                            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            data = payload.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            return ""

        @tool
        def gmail_search(query: str, max_results: int = 5) -> str:
            """
            Search emails in Gmail using Gmail search syntax.
            Examples: 'from:boss@company.com', 'subject:invoice', 'is:unread', 'after:2024/01/01'
            Returns a list of matching emails with their IDs (needed for gmail_read).
            """
            try:
                result = service.users().messages().list(
                    userId="me", q=query, maxResults=max_results
                ).execute()
                messages = result.get("messages", [])
                if not messages:
                    return f"No emails found for: '{query}'"

                lines = []
                for msg in messages:
                    data = service.users().messages().get(
                        userId="me", id=msg["id"], format="metadata",
                        metadataHeaders=["From", "Subject", "Date"],
                    ).execute()
                    h = _headers(data)
                    lines.append(
                        f"• ID: `{msg['id']}`\n"
                        f"  From: {h.get('From', '?')}\n"
                        f"  Subject: {h.get('Subject', '?')}\n"
                        f"  Date: {h.get('Date', '?')}"
                    )
                return "**Matching Emails:**\n\n" + "\n\n".join(lines)
            except Exception as ex:
                return f"Gmail search error: {ex}"

        @tool
        def gmail_read(message_id: str) -> str:
            """
            Read the full content of a Gmail email using its message ID.
            Always call gmail_search first to get the message ID.
            """
            try:
                data = service.users().messages().get(
                    userId="me", id=message_id, format="full"
                ).execute()
                h    = _headers(data)
                body = _body(data)[:3000]
                return (
                    f"**From:** {h.get('From','?')}\n"
                    f"**To:** {h.get('To','?')}\n"
                    f"**Subject:** {h.get('Subject','?')}\n"
                    f"**Date:** {h.get('Date','?')}\n\n---\n{body}"
                )
            except Exception as ex:
                return f"Gmail read error: {ex}"

        @tool
        def gmail_send(to: str, subject: str, body: str) -> str:
            """
            Send an email via Gmail.
            IMPORTANT: Only call this AFTER the user has explicitly confirmed
            the recipient (to), subject, and body. Never send without confirmation.
            """
            try:
                msg          = MIMEText(body)
                msg["to"]    = to
                msg["subject"] = subject
                raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
                service.users().messages().send(
                    userId="me", body={"raw": raw}
                ).execute()
                return f"✅ Email sent to **{to}** — subject: **'{subject}'**"
            except Exception as ex:
                return f"Gmail send error: {ex}"

        return [gmail_search, gmail_read, gmail_send]

    except ImportError:
        print("⚠️  google-api-python-client not installed.")
        return []
"""
config.py
─────────
Central place for API keys, constants, and the system prompt.
Edit SYSTEM_PROMPT here to change Clara's personality or rules.
"""

import os
import datetime
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ──────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EXA_API_KEY    = os.getenv("EXA_API_KEY", "")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# ── Google OAuth scopes ───────────────────────────────────────────────────────
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.modify",
]

# ── LLM settings ─────────────────────────────────────────────────────────────
LLM_MODEL       = "gpt-4o-mini"       # swap to gpt-4o for smarter responses
EMBED_MODEL     = "text-embedding-3-small"
EMBED_DIMS      = 1024
FAISS_DB_PATH   = "faiss_local_db"
MEMORY_PATH     = "clara_memory.json"  # persisted long-term memory file

# ── Tool display labels (used by the UI status widget) ────────────────────────
TOOL_LABELS = {
    "local_pdf_search":       "📄 Searching your PDFs",
    "wikipedia_search":       "🌐 Searching Wikipedia",
    "arxiv_search":           "📚 Searching arXiv",
    "exa_web_search":         "🔍 Searching the web via Exa",
    "exa_find_similar":       "🔗 Finding similar pages",
    "exa_get_contents":       "📰 Fetching page content",
    "youtube_transcript":     "▶ Fetching YouTube transcript",
    "google_calendar_list":   "📅 Checking your calendar",
    "google_calendar_create": "📅 Creating calendar event",
    "gmail_search":           "📧 Searching your emails",
    "gmail_read":             "📧 Reading email",
    "gmail_send":             "📧 Sending email",
    "remember_fact":          "🧠 Saving to memory",
    "recall_memory":          "🧠 Recalling from memory",
}

# ── System prompt ─────────────────────────────────────────────────────────────
TODAY = datetime.date.today().strftime("%A, %B %d, %Y")

SYSTEM_PROMPT = f"""You are Clara 2.0, an advanced personal research and productivity assistant.
Today's date is {TODAY}.

## Your Tools:
1.  local_pdf_search       — Search the user's uploaded PDF documents.
2.  wikipedia_search       — Search Wikipedia for facts, history, people, places.
3.  arxiv_search           — Search academic papers on arXiv.
4.  exa_web_search         — Real-time web search via Exa.
5.  exa_find_similar       — Find pages similar to a given URL.
6.  exa_get_contents       — Fetch full content of a URL.
7.  youtube_transcript     — Get the full transcript of any YouTube video.
8.  google_calendar_list   — List the user's upcoming Google Calendar events.
9.  google_calendar_create — Create a new Google Calendar event.
10. gmail_search           — Search emails in Gmail.
11. gmail_read             — Read the full content of a specific email by ID.
12. gmail_send             — Send an email (ALWAYS confirm with user first).
13. remember_fact          — Save an important fact about the user to long-term memory.
14. recall_memory          — Retrieve facts previously saved about the user.

## Tool Selection Rules:
- Questions about uploaded files         → local_pdf_search FIRST
- General knowledge, history, people     → wikipedia_search
- Research papers, ML/AI, science        → arxiv_search
- Latest news, current events, live info → exa_web_search
- YouTube video summary or Q&A           → youtube_transcript
- User's schedule, meetings, events      → google_calendar_list
- Create a meeting or reminder           → google_calendar_create
- Find or read an email                  → gmail_search → gmail_read
- Send an email                          → gmail_send (confirm first!)
- User shares personal info (name, prefs, job) → remember_fact
- User asks "do you remember" or refers to past context → recall_memory
- Complex questions                      → combine multiple tools

## Memory Rules:
- If the user tells you something personal (name, preferences, goals, job, location),
  ALWAYS call remember_fact to store it.
- At the start of every conversation, call recall_memory("all") silently to load context.
- Use remembered facts naturally in responses — don't announce that you're using memory.

## Communication Rules:
- NEVER ask which tool to use — decide yourself.
- Always ground answers in tool results. Do not hallucinate.
- For gmail_send, repeat to/subject/body to the user and ask for confirmation BEFORE sending.
- Be concise and friendly. Use markdown formatting for clarity.
"""
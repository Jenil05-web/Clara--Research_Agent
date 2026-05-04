"""
agent.py
────────
Assembles every tool module and builds the LangGraph ReAct agent.
Cached with st.cache_resource so it only rebuilds when PDFs change.

Tool modules imported:
  memory.py       → remember_fact, recall_memory
  search.py       → wikipedia, arxiv, exa_*
  youtube.py      → youtube_transcript
  google_tools.py → google_calendar_*, gmail_*
"""

import os
import streamlit as st

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.tools.retriever import create_retriever_tool
from langgraph.prebuilt import create_react_agent

from config import (
    LLM_MODEL, EMBED_MODEL, EMBED_DIMS,
    FAISS_DB_PATH, SYSTEM_PROMPT,
)
from memory       import build_memory_tools
from search       import build_search_tools
from youtube      import build_youtube_tool
from google_tools import build_calendar_tools, build_gmail_tools


@st.cache_resource(show_spinner="⚡ Loading Clara 2.0…")
def build_agent():
    """
    Builds and returns (agent, has_local_db, tool_status_dict).
    tool_status_dict maps display name → bool (True = active).
    """
    llm        = ChatOpenAI(model=LLM_MODEL, temperature=0)
    embeddings = OpenAIEmbeddings(model=EMBED_MODEL, dimensions=EMBED_DIMS)

    tools       = []
    tool_status = {}

    # ── 1. Long-term memory ───────────────────────────────────
    mem_tools = build_memory_tools()
    tools.extend(mem_tools)
    tool_status["🧠 Memory"] = True

    # ── 2. Local PDF knowledge base ───────────────────────────
    has_local_db = os.path.exists(FAISS_DB_PATH)
    if has_local_db:
        vs = FAISS.load_local(
            FAISS_DB_PATH, embeddings, allow_dangerous_deserialization=True
        )
        tools.append(create_retriever_tool(
            retriever=vs.as_retriever(search_kwargs={"k": 5}),
            name="local_pdf_search",
            description=(
                "Search the user's uploaded PDF documents. "
                "Use this FIRST when the user asks about their uploaded files."
            ),
        ))
        tool_status["📄 Local PDFs"] = True
    else:
        tool_status["📄 Local PDFs"] = False

    # ── 3. Web & academic search ──────────────────────────────
    search_tools = build_search_tools()
    tools.extend(search_tools)
    tool_names   = [t.name for t in search_tools]
    tool_status["🌐 Wikipedia"]     = "wikipedia_search"  in tool_names
    tool_status["📚 arXiv"]         = "arxiv_search"      in tool_names
    tool_status["🔍 Exa Web Search"]= "exa_web_search"    in tool_names

    # ── 4. YouTube transcripts ────────────────────────────────
    yt_tools = build_youtube_tool()
    tools.extend(yt_tools)
    tool_status["▶ YouTube"] = len(yt_tools) > 0

    # ── 5. Google Calendar ────────────────────────────────────
    cal_tools = build_calendar_tools()
    tools.extend(cal_tools)
    tool_status["📅 Google Calendar"] = len(cal_tools) > 0

    # ── 6. Gmail ──────────────────────────────────────────────
    gmail_tools = build_gmail_tools()
    tools.extend(gmail_tools)
    tool_status["📧 Gmail"] = len(gmail_tools) > 0

    # ── Build agent ───────────────────────────────────────────
    agent = create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)
    return agent, has_local_db, tool_status
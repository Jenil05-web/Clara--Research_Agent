"""
tools/memory.py
───────────────
Long-term memory for Clara using a local JSON file.
Two tools are exposed to the agent:
  - remember_fact : saves a key→value fact about the user
  - recall_memory : retrieves stored facts

The memory file persists across sessions at MEMORY_PATH (see config.py).
"""

import json
import os
from langchain_core.tools import tool
from config import MEMORY_PATH


def _load() -> dict:
    if os.path.exists(MEMORY_PATH):
        with open(MEMORY_PATH, "r") as f:
            return json.load(f)
    return {}


def _save(data: dict) -> None:
    with open(MEMORY_PATH, "w") as f:
        json.dump(data, f, indent=2)


def build_memory_tools() -> list:

    @tool
    def remember_fact(key: str, value: str) -> str:
        """
        Save an important fact about the user to long-term memory.
        Use this whenever the user shares personal information such as their
        name, job, preferences, location, goals, or any detail worth remembering.

        Examples:
          key="name",        value="Jenil"
          key="job",         value="ML engineer"
          key="preference",  value="prefers concise answers"
          key="city",        value="Ahmedabad"
        """
        memory = _load()
        memory[key.lower().strip()] = value.strip()
        _save(memory)
        return f"✅ Remembered: {key} = {value}"

    @tool
    def recall_memory(query: str = "all") -> str:
        """
        Retrieve facts previously saved about the user from long-term memory.
        Pass 'all' to get everything, or a specific key like 'name' or 'job'.
        Use this when the user asks 'do you remember...?' or refers to past context.
        """
        memory = _load()
        if not memory:
            return "No memories stored yet."

        if query.strip().lower() == "all":
            lines = [f"• **{k}**: {v}" for k, v in memory.items()]
            return "**What I remember about you:**\n" + "\n".join(lines)

        key = query.strip().lower()
        if key in memory:
            return f"**{key}**: {memory[key]}"

        # fuzzy: return any key containing the query word
        matches = {k: v for k, v in memory.items() if query.lower() in k}
        if matches:
            lines = [f"• **{k}**: {v}" for k, v in matches.items()]
            return "\n".join(lines)

        return f"I don't have anything stored under '{query}'."

    return [remember_fact, recall_memory]
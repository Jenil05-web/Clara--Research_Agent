"""
app.py  ←  Entry point
───────────────────────
Only UI code lives here. All logic is in:
  config.py             → keys, constants, system prompt
  agent.py              → tool assembly + LangGraph agent
  tools/memory.py       → long-term memory
  tools/search.py       → Wikipedia, arXiv, Exa
  tools/youtube.py      → YouTube transcripts
  tools/google_tools.py → Google Calendar + Gmail

Run with:
  streamlit run app.py
"""

import os
import io
import shutil
import hashlib
import json
import streamlit as st
from openai import OpenAI

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import EMBED_MODEL, EMBED_DIMS, FAISS_DB_PATH, TOOL_LABELS, OPENAI_API_KEY
from agent import build_agent
from google_tools import get_google_creds

# ─────────────────────────────────────────────────────────────
# FFMPEG CONFIGURATION FOR AUDIO PROCESSING
# ─────────────────────────────────────────────────────────────
import platform
from pydub import AudioSegment

# Try to configure ffmpeg path for pydub
ffmpeg_paths = [
    "ffmpeg",  # System PATH
    "C:\\ffmpeg\\bin\\ffmpeg.exe",
    "C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe",
    "C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe",
]

for ffmpeg_path in ffmpeg_paths:
    try:
        # Test if ffmpeg is accessible
        import subprocess
        subprocess.run([ffmpeg_path, "-version"], capture_output=True, timeout=5)
        AudioSegment.converter = ffmpeg_path
        break
    except:
        continue

# ═════════════════════════════════════════════════════════════
# APP CONFIG & CLEAN CSS UI
# ═════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Clara 2.0",
    page_icon="🦜",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* ── Minimalist Global Reset ── */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 850px !important;
    }
    
    #MainMenu, footer, header {visibility: hidden;}

    /* ── Typography & Header ── */
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0;
        padding-bottom: 0;
    }
    .sub-title {
        color: #6b7280;
        font-size: 0.95rem;
        font-weight: 400;
        margin-top: 0.2rem;
        margin-bottom: 1.5rem;
    }

    /* ── Chat Message Styling ── */
    .stChatMessage {
        border-radius: 12px !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
    }
    /* User Message */
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background-color: rgba(102, 126, 234, 0.08) !important;
        border: 1px solid rgba(102, 126, 234, 0.2) !important;
    }
    /* Assistant Message */
    .stChatMessage[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
        background-color: transparent !important;
        border: 1px solid rgba(156, 163, 175, 0.2) !important;
    }

    /* ── Tool Status Pills ── */
    .tool-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 500;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .tool-active {
        background: rgba(34, 197, 94, 0.1);
        color: #15803d;
        border: 1px solid rgba(34, 197, 94, 0.2);
    }
    .tool-inactive {
        background: rgba(239, 68, 68, 0.05);
        color: #b91c1c;
        border: 1px solid rgba(239, 68, 68, 0.1);
    }

    /* ── Input Area Tweaks ── */
    .stChatInputContainer {
        padding-bottom: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# WHISPER TRANSCRIPTION HELPER
# ─────────────────────────────────────────────────────────────
def transcribe_audio(audio_bytes: bytes) -> str:
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "voice_input.webm" 
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en",
        )
        return result.text.strip()
    except Exception as e:
        return f"[Transcription error: {e}]"


# ═════════════════════════════════════════════════════════════
# STATE INITIALIZATION
# ═════════════════════════════════════════════════════════════
if "messages" not in st.session_state:
    st.session_state.messages = []
if "voice_transcript" not in st.session_state:
    st.session_state.voice_transcript = ""
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None


# ═════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem; margin-bottom: -10px;">🦜</div>
            <h2 style="margin-bottom: 0;">Clara</h2>
            <div style="font-size: 0.8rem; color: #6b7280;">v2.0.0</div>
        </div>
    """, unsafe_allow_html=True)

    # ── 1. Knowledge Base ──
    with st.expander("📄 Knowledge Base", expanded=False):
        uploaded_files = st.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)
        if st.button("Process & Embed", use_container_width=True):
            if uploaded_files:
                with st.spinner("Embedding documents…"):
                    os.makedirs("temp_uploads", exist_ok=True)
                    texts    = []
                    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                    
                    for file in uploaded_files:
                        tmp = os.path.join("temp_uploads", file.name)
                        with open(tmp, "wb") as f:
                            f.write(file.getbuffer())
                        texts.extend(splitter.split_documents(PyPDFLoader(tmp).load()))
                        os.remove(tmp)

                    emb = OpenAIEmbeddings(model=EMBED_MODEL, dimensions=EMBED_DIMS)
                    if os.path.exists(FAISS_DB_PATH):
                        vs = FAISS.load_local(FAISS_DB_PATH, emb, allow_dangerous_deserialization=True)
                        vs.add_documents(texts)
                    else:
                        vs = FAISS.from_documents(texts, emb)
                    vs.save_local(FAISS_DB_PATH)

                    st.success(f"Embedded {len(uploaded_files)} PDF(s)")
                    build_agent.clear()
                    st.rerun()
            else:
                st.warning("Upload at least one PDF first.")

    # ── 2. Google Account ──
    with st.expander("🔐 Integrations", expanded=False):
        if os.path.exists("token.json"):
            st.success("✅ Connected to Google")
            if st.button("Disconnect", use_container_width=True):
                os.remove("token.json")
                build_agent.clear()
                st.rerun()
        elif os.path.exists("credentials.json"):
            if st.button("Connect Google Account", use_container_width=True):
                with st.spinner("Opening browser..."):
                    build_agent.clear()
                    get_google_creds()
                    st.rerun()
        else:
            st.warning("⚠️ credentials.json not found")

    # ── 3. Memory ──
    with st.expander("🧠 Clara's Memory", expanded=False):
        if os.path.exists("clara_memory.json"):
            with open("clara_memory.json") as f:
                mem = json.load(f)
            if mem:
                for k, v in mem.items():
                    st.markdown(f"**{k}**: {v}")
                if st.button("Clear Memory", use_container_width=True):
                    os.remove("clara_memory.json")
                    st.rerun()
            else:
                st.caption("No memories stored.")
        else:
            st.caption("No memories stored.")

    # ── 4. System ──
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑️ Factory Reset App", use_container_width=True, type="secondary"):
        if os.path.exists(FAISS_DB_PATH):
            shutil.rmtree(FAISS_DB_PATH)
        build_agent.clear()
        st.session_state.clear()
        st.rerun()


# ═════════════════════════════════════════════════════════════
# HEADER & TOOL STATUS
# ═════════════════════════════════════════════════════════════
st.markdown('<div class="main-title">Clara 2.0</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Your proactive research & productivity agent.</div>', unsafe_allow_html=True)

agent, has_local_db, tool_status = build_agent()

# Render Active Tools neatly
tool_html = "<div>"
for name, active in tool_status.items():
    cls = "tool-active" if active else "tool-inactive"
    icon = "●" if active else "○"
    tool_html += f"<span class='tool-pill {cls}'>{icon} {name}</span>"
tool_html += "</div><hr style='margin-top: 1rem; margin-bottom: 1.5rem; opacity: 0.5;'>"
st.markdown(tool_html, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════
# CHAT HISTORY
# ═════════════════════════════════════════════════════════════
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ═════════════════════════════════════════════════════════════
# PERSISTENT VOICE & TEXT INPUT
# ═════════════════════════════════════════════════════════════
# By removing the `if show_voice_input` block and making the layout static,
# we prevent the jumping/disappearing bug entirely.
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 6])
with col1:
    try:
        from streamlit_mic_recorder import mic_recorder
        audio_data = mic_recorder(
            start_prompt="🎙️ Record",
            stop_prompt="⏹️ Stop",
            just_once=True,
            key="persistent_mic"
        )
        
        # Process newly recorded audio
        if audio_data and audio_data.get("bytes"):
            audio_bytes = audio_data["bytes"]
            audio_hash = hashlib.md5(audio_bytes).hexdigest()

            if audio_hash != st.session_state.last_audio_hash:
                st.session_state.last_audio_hash = audio_hash
                with st.spinner("Transcribing..."):
                    transcript = transcribe_audio(audio_bytes)
                st.session_state.voice_transcript = transcript
                st.rerun()
                
    except ImportError:
        st.caption("No mic library installed.")

with col2:
    if st.session_state.voice_transcript:
        st.info(f"**Draft:** {st.session_state.voice_transcript}")

# Standard text input
text_prompt = st.chat_input("Ask Clara anything...")

# Determine final prompt (Text overrides Voice)
prompt = text_prompt or st.session_state.voice_transcript or ""


# ═════════════════════════════════════════════════════════════
# RUN AGENT
# ═════════════════════════════════════════════════════════════
if prompt:
    # Clear voice transcript on submission
    st.session_state.voice_transcript = ""

    # Render user prompt
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Render Agent Response
    with st.chat_message("assistant"):
        status_box = st.status("Thinking...", expanded=True)
        final_answer = ""

        history = [
            ("user" if m["role"] == "user" else "assistant", m["content"])
            for m in st.session_state.messages
        ]

        for step in agent.stream({"messages": history}, stream_mode="values"):
            last = step["messages"][-1]

            if hasattr(last, "tool_calls") and last.tool_calls:
                for tc in last.tool_calls:
                    label = TOOL_LABELS.get(tc["name"], f"🔧 Using {tc['name']}")
                    status_box.write(f"{label}…")

            elif last.type == "ai" and last.content:
                final_answer = last.content

        status_box.update(label="Complete", state="complete", expanded=False)
        st.markdown(final_answer)

    st.session_state.messages.append({"role": "assistant", "content": final_answer})
    st.rerun()
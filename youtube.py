"""
tools/youtube.py
────────────────
YouTube transcript tool using youtube-transcript-api.
  pip install youtube-transcript-api

FIX vs previous version:
  - Uses fetch() + FetchedTranscript instead of deprecated get_transcript()
  - Handles both youtube.com/watch?v= and youtu.be/ short links
  - Strips ?si= and other tracking params from URLs
  - Falls back through multiple language codes
  - Returns timestamped chunks so the agent can reference specific moments
"""

import re
from langchain_core.tools import tool


def _extract_video_id(raw: str) -> str:
    """
    Extract the 11-character YouTube video ID from any URL format or return
    the raw string if it already looks like a bare ID.
    """
    raw = raw.strip()

    # Already a bare video ID (11 alphanumeric + _ -)
    if re.match(r'^[A-Za-z0-9_\-]{11}$', raw):
        return raw

    # youtu.be/VIDEO_ID
    m = re.search(r'youtu\.be/([A-Za-z0-9_\-]{11})', raw)
    if m:
        return m.group(1)

    # youtube.com/watch?v=VIDEO_ID  or  youtube.com/shorts/VIDEO_ID
    m = re.search(r'(?:v=|/shorts/)([A-Za-z0-9_\-]{11})', raw)
    if m:
        return m.group(1)

    # youtube.com/embed/VIDEO_ID
    m = re.search(r'/embed/([A-Za-z0-9_\-]{11})', raw)
    if m:
        return m.group(1)

    return raw   # best effort


def build_youtube_tool() -> list:
    try:
        # New API surface (youtube-transcript-api >= 0.6)
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import (
            TranscriptsDisabled,
            NoTranscriptFound,
            VideoUnavailable,
        )

        @tool
        def youtube_transcript(video_url_or_id: str, max_chars: int = 5000) -> str:
            """
            Get the full transcript/captions of a YouTube video.

            Accepts:
              - Full URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
              - Short URL: https://youtu.be/dQw4w9WgXcQ
              - Bare video ID: dQw4w9WgXcQ

            Use this to summarise videos, extract key points, or answer
            questions about specific video content.
            """
            vid_id = _extract_video_id(video_url_or_id)

            try:
                # List available transcripts first so we can pick the best one
                transcript_list = YouTubeTranscriptApi.list_transcripts(vid_id)

                transcript = None

                # 1. Try manually created English transcript
                try:
                    transcript = transcript_list.find_manually_created_transcript(
                        ["en", "en-US", "en-GB", "en-IN"]
                    )
                except Exception:
                    pass

                # 2. Fall back to auto-generated English
                if transcript is None:
                    try:
                        transcript = transcript_list.find_generated_transcript(
                            ["en", "en-US", "en-GB", "en-IN"]
                        )
                    except Exception:
                        pass

                # 3. Fall back to any available language and translate to English
                if transcript is None:
                    try:
                        available = list(transcript_list)
                        if available:
                            transcript = available[0].translate("en")
                    except Exception:
                        pass

                if transcript is None:
                    return f"No transcript available for video ID: {vid_id}"

                # Fetch and format
                entries = transcript.fetch()
                lines   = []
                chars   = 0
                for entry in entries:
                    # entry is a FetchedTranscriptSnippet object
                    text  = getattr(entry, "text", "")
                    start = getattr(entry, "start", 0)
                    mins  = int(start // 60)
                    secs  = int(start % 60)
                    line  = f"[{mins:02d}:{secs:02d}] {text}"
                    lines.append(line)
                    chars += len(line)
                    if chars >= max_chars:
                        lines.append("… [transcript truncated for length]")
                        break

                full = "\n".join(lines)
                return (
                    f"**YouTube Transcript** — video ID: `{vid_id}`\n"
                    f"Language: {transcript.language} "
                    f"({'auto-generated' if transcript.is_generated else 'manual'})\n\n"
                    f"{full}"
                )

            except VideoUnavailable:
                return f"Video `{vid_id}` is unavailable or private."
            except TranscriptsDisabled:
                return f"Transcripts are disabled for video `{vid_id}`."
            except NoTranscriptFound:
                return f"No transcript found for video `{vid_id}` in any language."
            except Exception as e:
                return f"YouTube transcript error: {type(e).__name__}: {e}"

        return [youtube_transcript]

    except ImportError:
        print("⚠️  youtube-transcript-api not installed. Run: pip install youtube-transcript-api")
        return []
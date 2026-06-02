import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Optional

from src.local.local_engine import LocalEngine
from src.api.cloud_service import CloudService
from src.utils.config import get_settings


# Load application settings (reads .env if present per Settings)
settings = get_settings()


def _mock_cloud_fallback_transcription(audio_file_path: str) -> str:
    """Return a deterministic mocked cloud transcription when allowed.

    This keeps the pipeline testable without enabling real cloud calls.
    """
    return "[Cloud-Fallback-Mock] This is a simulated cloud transcription for testing."


def transcribe_audio_local_first(audio_file_path: str, allow_cloud_fallback: Optional[bool] = None) -> str:
    """Run a local-first transcription pipeline using LocalEngine.

    If local transcription fails and allow_cloud_fallback is True, a mocked
    cloud transcription is returned. The function returns the transcript text.
    """
    allow_cloud = settings.allow_cloud_fallback if allow_cloud_fallback is None else allow_cloud_fallback

    audio_path = Path(audio_file_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    local_engine = LocalEngine()

    # If the provided path looks like a video, extract audio first (LocalEngine handles ffmpeg fallback)
    if audio_path.suffix.lower() not in [".wav", ".mp3", ".m4a", ".flac", ".aac"]:
        audio_path = local_engine.extract_audio(audio_path)

    try:
        result = local_engine.transcribe(audio_path)
        return result.get("text", "")
    except Exception as e:
        print(f"⚠️ [Local Transcription Error] {e}")
        if allow_cloud:
            print("🔁 Falling back to mocked cloud transcription (allow_cloud_fallback=True)")
            return _mock_cloud_fallback_transcription(str(audio_path))
        raise


def run_transcription_pipeline(input_path: Optional[str] = None) -> Optional[str]:
    """Entry point for transcription pipeline.

    If input_path is None, a default file in the configured storage path
    is used: <storage_path>/temp_audio.mp3
    """
    print("\n▶️ --- Running: transcription_manager.py (local-first) ---")

    input_path = input_path or str(Path(settings.storage_path) / "temp_audio.mp3")
    print(f" [Step] Processing: {input_path}")

    try:
        transcript_text = transcribe_audio_local_first(input_path)
    except FileNotFoundError as e:
        print(f"❌ [Transcription Error] {e}")
        return None
    except Exception as e:
        print(f"❌ [Transcription Error] {e}")
        return None

    if not transcript_text:
        print("❌ [Step] Transcription produced no text.")
        return None

    print(f"✅ [Local] Transcription completed ({len(transcript_text.split())} words).")

    # Persist to configured SQLite database path
    db_path = Path(settings.database_path)
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS project_transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audio_name TEXT,
                full_text TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            "INSERT INTO project_transcripts (audio_name, full_text) VALUES (?, ?)",
            (os.path.basename(input_path), transcript_text),
        )

        conn.commit()
        conn.close()
        print(f" [DB] Transcription indexed in: {db_path}")
    except Exception as e:
        print(f"❌ [DB Error] Failed to save transcript to SQLite: {e}")
        return None

    return transcript_text


if __name__ == "__main__":
    # Optional arg: path to audio/video file
    chosen = sys.argv[1] if len(sys.argv) > 1 else None
    run_transcription_pipeline(input_path=chosen)

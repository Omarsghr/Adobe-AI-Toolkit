from __future__ import annotations

import contextlib
import subprocess
import tempfile
import wave
import struct
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    # type-only import to avoid runtime cycles
    from src.utils.config import Settings

from src.utils.config import get_settings

class LocalEngine:
    """
    LocalEngine provides local media utilities (audio extraction, basic
    transcription scaffolding). This implementation intentionally uses
    mocked transcription output so it can be integrated and tested before
    real model integration (e.g., faster-whisper) is added.

    Methods:
        - extract_audio(video_path, out_audio_path=None, sample_rate=16000)
        - transcribe(audio_path, model='small', language=None)

    The extract_audio method attempts to call `ffmpeg` if available; if
    `ffmpeg` is not found or the call fails, a short (1s) silent WAV file is created as a mock output.
    The transcribe method returns a deterministic dummy transcription dict with segments suitable for downstream orchestration testing.
    """

    def __init__(
        self,
        use_gpu: Optional[bool] = None,
        ffmpeg_cmd: str = "ffmpeg",
        settings: Optional["Settings"] = None,
    ) -> None:
        """
        Initialize the LocalEngine.

        If `settings` is provided it will be used to drive transcription
        behaviour; otherwise `get_settings()` is called to obtain defaults.
        The explicit `use_gpu` argument overrides the settings value.
        """
        self.settings = settings or get_settings()
        self.use_gpu = use_gpu if use_gpu is not None else bool(getattr(self.settings, "use_gpu", False))
        self.ffmpeg_cmd = ffmpeg_cmd
        # Backend-specific model handles will be stored lazily here
        self._fw_model = None
        self._wx_model = None

    def extract_audio(
        self,
        video_path: Path | str,
        out_audio_path: Optional[Path | str] = None,
        sample_rate: int = 16000,
    ) -> Path:
        """
        Extract audio from a video file into a WAV file.

        If `ffmpeg` is available on PATH, this will call it. If ffmpeg is
        not available or the call fails, the function will create a
        short (1s) silent WAV file as a mock output so the rest of the
        pipeline can be exercised.

        Returns the Path to the audio file.
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"video file not found: {video_path}")

        if out_audio_path is None:
            tmpdir = Path(tempfile.mkdtemp(prefix="local_audio_"))
            out_audio_path = tmpdir / f"{video_path.stem}.wav"
        else:
            out_audio_path = Path(out_audio_path)
            out_audio_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.ffmpeg_cmd,
            "-y",
            "-i",
            str(video_path),
            "-ar",
            str(sample_rate),
            "-ac",
            "1",
            "-vn",
            str(out_audio_path),
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60,
            )
            logger.info("Audio extracted to %s using ffmpeg", out_audio_path)
            return out_audio_path
        except FileNotFoundError:
            logger.warning("ffmpeg not found on PATH. Falling back to mock audio.")
        except subprocess.CalledProcessError as e:
            logger.warning("ffmpeg failed (%s). Falling back to mock audio.", e)
        except subprocess.TimeoutExpired:
            logger.warning("ffmpeg timed out. Falling back to mock audio.")

        # Create a short silent WAV as a deterministic mock artifact
        self._create_silent_wav(out_audio_path, duration_seconds=1, sample_rate=sample_rate)
        logger.info("Created mock silent audio at %s", out_audio_path)
        return out_audio_path

    def transcribe(
        self,
        audio_path: Path | str,
        model: Optional[str] = None,
        language: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        backend: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe a local WAV audio file using the configured backend.

        This method supports three modes:
         - mock/dry-run: returns deterministic mocked output (when
           `settings.transcription_dry_run` is True or if real backends are missing)
         - faster-whisper: uses the `faster_whisper.WhisperModel` when available
         - whisperx: uses `whisperx` when selected

        The function returns a dictionary with the same shape as the
        previous mock implementation to keep the orchestrator stable.
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"audio file not found: {audio_path}")

        duration = self._get_wav_duration(audio_path)

        # Resolve effective settings
        model_name = model or getattr(self.settings, "local_model_name", "small")
        backend = backend or getattr(self.settings, "local_transcription_backend", "faster-whisper")
        timeout_seconds = timeout_seconds or getattr(self.settings, "transcription_timeout", 600)

        # If the user has requested dry-run, return the deterministic mock
        if getattr(self.settings, "transcription_dry_run", True):
            return self._mock_transcript(duration=duration, model=model_name, language=language)

        # Attempt to run the chosen backend. If anything fails we fall back to the mock
        try:
            if backend == "faster-whisper":
                return self._transcribe_with_faster_whisper(audio_path, model_name, language, duration)
            elif backend == "whisperx":
                return self._transcribe_with_whisperx(audio_path, model_name, language, duration)
            else:
                logger.warning("Unknown transcription backend '%s', using mock result", backend)
                return self._mock_transcript(duration=duration, model=model_name, language=language)
        except Exception:
            logger.exception("Transcription with backend '%s' failed; returning mock result", backend)
            return self._mock_transcript(duration=duration, model=model_name, language=language)

    def _mock_transcript(self, duration: float, model: str, language: Optional[str]) -> Dict[str, Any]:
        """Return the same deterministic mocked transcription used previously."""
        dummy_text = (
            "This is a mocked transcription produced by LocalEngine. "
            "Replace this with a real local-model transcription later."
        )
        segments = [
            {
                "start": 0.0,
                "end": round(duration, 3),
                "text": dummy_text,
                "confidence": 0.98,
            }
        ]
        result = {
            "text": dummy_text,
            "segments": segments,
            "model": model,
            "language": language or "en",
            "duration": duration,
            "mock": True,
        }
        logger.debug("Mock transcription result prepared: %s", result)
        return result

    def _detect_cuda(self) -> bool:
        """Return True if a CUDA-capable torch is available, False otherwise."""
        try:
            import torch

            return torch.cuda.is_available()
        except Exception:
            return False

    def _transcribe_with_faster_whisper(self, audio_path: Path, model_name: str, language: Optional[str], duration: float) -> Dict[str, Any]:
        """Attempt transcription using faster-whisper. Raises on failure so caller can fall back."""
        # Import inside the function to avoid hard dependency during import-time
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except Exception as e:
            logger.exception("faster-whisper import failed: %s", e)
            raise

        device = "cuda" if (self.use_gpu and self._detect_cuda()) else "cpu"
        # Lazy-load the model
        if self._fw_model is None:
            logger.info("Loading faster-whisper model '%s' on device=%s", model_name, device)
            self._fw_model = WhisperModel(model_name, device=device, compute_type="int8_float16" if device == "cuda" else "float32")

        # The WhisperModel.transcribe API yields segments and info; adapt to our expected shape
        segments_out = []
        text_parts = []
        for segment in self._fw_model.transcribe(str(audio_path), beam_size=5):
            # faster-whisper segments typically have start, end, and text
            seg = {"start": float(getattr(segment, "start", 0.0)), "end": float(getattr(segment, "end", 0.0)), "text": getattr(segment, "text", ""), "confidence": getattr(segment, "confidence", 0.0)}
            segments_out.append(seg)
            text_parts.append(seg["text"])

        full_text = "\n".join(text_parts)
        return {"text": full_text, "segments": segments_out, "model": model_name, "language": language or "en", "duration": duration, "mock": False}

    def _transcribe_with_whisperx(self, audio_path: Path, model_name: str, language: Optional[str], duration: float) -> Dict[str, Any]:
        """Attempt transcription using whisperx. This is a thin adapter and may
        need refinement depending on the installed whisperx version."""
        try:
            import whisperx  # type: ignore
        except Exception as e:
            logger.exception("whisperx import failed: %s", e)
            raise

        device = "cuda" if (self.use_gpu and self._detect_cuda()) else "cpu"
        logger.info("Loading whisperx model '%s' on device=%s", model_name, device)
        model = whisperx.load_model(model_name, device=device)
        result = model.transcribe(str(audio_path))
        # The shape of `result` depends on whisperx; adapt conservatively
        segments_out = []
        text = ""
        for seg in getattr(result, "segments", []) or result.get("segments", []):
            s = {"start": float(seg.get("start", 0.0)), "end": float(seg.get("end", 0.0)), "text": seg.get("text", ""), "confidence": seg.get("confidence", 0.0)}
            segments_out.append(s)
            text += s["text"] + "\n"

        return {"text": text.strip(), "segments": segments_out, "model": model_name, "language": language or "en", "duration": duration, "mock": False}

    def _create_silent_wav(self, path: Path, duration_seconds: int = 1, sample_rate: int = 16000) -> None:
        """Create a mono, 16-bit PCM WAV file containing silence."""
        path.parent.mkdir(parents=True, exist_ok=True)
        n_frames = int(duration_seconds * sample_rate)
        with wave.open(str(path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            silent_frame = struct.pack("<h", 0)
            wf.writeframes(silent_frame * n_frames)

    def _get_wav_duration(self, path: Path) -> float:
        """Return the duration in seconds for a WAV file, or 0.0 on error."""
        try:
            with contextlib.closing(wave.open(str(path), "r")) as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except Exception:
            return 0.0


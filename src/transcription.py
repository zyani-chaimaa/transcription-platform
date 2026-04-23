import os
import tempfile
import streamlit as st
from faster_whisper import WhisperModel
from typing import Optional

SUPPORTED_LANGUAGES: dict[str, Optional[str]] = {
    "Auto-detect": None,
    "Arabic": "ar",
    "Chinese (Simplified)": "zh",
    "Dutch": "nl",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Polish": "pl",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Turkish": "tr",
    "Ukrainian": "uk",
}

SUPPORTED_FORMATS = ["mp3", "mp4", "m4a", "wav", "ogg", "flac", "webm", "opus"]


@st.cache_resource(show_spinner="Loading Whisper model — this only happens once…")
def load_model(model_size: str = "medium") -> WhisperModel:
    device = _best_device()
    compute_type = "float16" if device == "cuda" else "int8"
    cpu_threads = os.cpu_count() or 4
    return WhisperModel(model_size, device=device, compute_type=compute_type, cpu_threads=cpu_threads, num_workers=2)


def transcribe(
    audio_bytes: bytes,
    language: Optional[str],
    model_size: str = "medium",
) -> dict:
    """
    Transcribe raw audio bytes.

    Returns:
        {
            "text": str,
            "segments": [{"start": float, "end": float, "text": str}],
            "language": str,
            "language_probability": float,
            "duration": float,
        }
    """
    model = load_model(model_size)
    device = _best_device()
    beam_size = 5 if device == "cuda" else 1

    suffix = ".audio"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(audio_bytes)
        tmp.flush()

        segments_iter, info = model.transcribe(
            tmp.name,
            language=language,
            task="transcribe",
            beam_size=beam_size,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )

        segments: list[dict] = []
        text_parts: list[str] = []

        for seg in segments_iter:
            clean = seg.text.strip()
            segments.append({"start": seg.start, "end": seg.end, "text": clean})
            text_parts.append(clean)

    return {
        "text": " ".join(text_parts),
        "segments": segments,
        "language": info.language,
        "language_probability": round(info.language_probability * 100, 1),
        "duration": round(info.duration, 2),
    }


def _best_device() -> str:
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"

import os
import io
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Transcription Platform",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from src.auth import authenticate, logout
from src.transcription import SUPPORTED_LANGUAGES, SUPPORTED_FORMATS, transcribe
from src.utils import download_section, result_metadata

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Remove top padding */
    .block-container { padding-top: 1.5rem; }

    /* Header bar */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 0 1rem 0;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 1.5rem;
    }
    .app-title { font-size: 1.5rem; font-weight: 700; color: #111827; margin: 0; }
    .app-subtitle { font-size: 0.85rem; color: #6b7280; margin: 0; }

    /* Info banner */
    .info-banner {
        background: #eff6ff;
        border-left: 4px solid #1a56db;
        border-radius: 0 6px 6px 0;
        padding: 0.6rem 1rem;
        font-size: 0.88rem;
        color: #1e40af;
        margin-bottom: 1.25rem;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; }
    .stTabs [data-baseweb="tab"] { font-size: 1rem; font-weight: 500; }

    /* Result box */
    .transcript-box {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.25rem;
        line-height: 1.75;
        white-space: pre-wrap;
        font-size: 0.95rem;
        max-height: 420px;
        overflow-y: auto;
    }

    /* Segment table */
    .seg-row { display: flex; gap: 1rem; padding: 0.35rem 0; border-bottom: 1px solid #f3f4f6; }
    .seg-time { font-size: 0.78rem; color: #6b7280; min-width: 120px; font-family: monospace; }
    .seg-text { font-size: 0.9rem; color: #111827; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
user = authenticate()
if user is None:
    st.stop()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
col_title, col_user = st.columns([4, 1])
with col_title:
    st.markdown(
        '<div class="app-title">🎙️ Transcription Platform</div>'
        '<div class="app-subtitle">Powered by Whisper · No data stored · Files are processed in memory only</div>',
        unsafe_allow_html=True,
    )
with col_user:
    if user.get("picture"):
        st.markdown(
            f'<img src="{user["picture"]}" style="width:36px;height:36px;border-radius:50%;float:right;margin-top:4px;">',
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div style="text-align:right;font-size:0.82rem;color:#374151;margin-top:4px;">'
        f'<strong>{user["name"]}</strong><br>{user["email"]}</div>',
        unsafe_allow_html=True,
    )
    if st.button("Sign out", use_container_width=True):
        logout()

st.markdown("---")

# ---------------------------------------------------------------------------
# Sidebar — model settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    model_env = os.getenv("WHISPER_MODEL", "medium")
    allow_model_choice = os.getenv("ALLOW_MODEL_CHOICE", "true").lower() == "true"

    if allow_model_choice:
        model_options = ["tiny", "base", "small", "medium", "large-v3"]
        default_idx = model_options.index(model_env) if model_env in model_options else 3
        model_size = st.selectbox(
            "Whisper model",
            model_options,
            index=default_idx,
            help=(
                "tiny/base: fastest, less accurate  \n"
                "small/medium: balanced  \n"
                "large-v3: most accurate, slowest"
            ),
        )
    else:
        model_size = model_env
        st.info(f"Model: **{model_size}** (set by admin)")

    st.markdown("---")
    st.markdown(
        "**Privacy notice**\n\n"
        "Audio and transcripts are never written to disk or stored on any server. "
        "All processing happens in memory and is discarded when your session ends.",
        help=None,
    )


# ---------------------------------------------------------------------------
# Shared language selector helper
# ---------------------------------------------------------------------------
def language_selector(key: str) -> str | None:
    lang_label = st.selectbox(
        "Language",
        list(SUPPORTED_LANGUAGES.keys()),
        key=key,
        help="Select the spoken language or let Whisper detect it automatically.",
    )
    return SUPPORTED_LANGUAGES[lang_label]


# ---------------------------------------------------------------------------
# Transcription result renderer
# ---------------------------------------------------------------------------
def render_result(result: dict, stem: str, audio_bytes: bytes | None, audio_ext: str = "wav") -> None:
    st.success("Transcription complete.")
    result_metadata(result)
    st.markdown("---")

    view = st.radio("View", ["Full text", "With timestamps"], horizontal=True, key=f"view_{stem}")

    if view == "Full text":
        st.markdown(
            f'<div class="transcript-box">{result["text"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        for seg in result["segments"]:
            st.markdown(
                f'<div class="seg-row">'
                f'<span class="seg-time">{_fmt_ts(seg["start"])} → {_fmt_ts(seg["end"])}</span>'
                f'<span class="seg-text">{seg["text"]}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("")
    download_section(result, stem)

    if audio_bytes:
        st.markdown("#### Download audio")
        st.download_button(
            f"Download audio (.{audio_ext})",
            data=audio_bytes,
            file_name=f"{stem}.{audio_ext}",
            mime=f"audio/{audio_ext}",
            use_container_width=False,
        )


def _fmt_ts(s: float) -> str:
    m, sec = divmod(int(s), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_upload, tab_record = st.tabs(["📁  Upload & Transcribe", "🎤  Record & Transcribe"])


# ── Upload tab ──────────────────────────────────────────────────────────────
with tab_upload:
    st.markdown(
        '<div class="info-banner">'
        "Upload an audio file and click <strong>Transcribe</strong>. "
        "Recommended formats: MP3, M4A, OGG (keep files under 200 MB). "
        "No file is retained after your session ends."
        "</div>",
        unsafe_allow_html=True,
    )

    uploaded = st.file_uploader(
        "Choose an audio file",
        type=SUPPORTED_FORMATS,
        label_visibility="collapsed",
    )

    lang_upload = language_selector("lang_upload")

    transcribe_btn = st.button(
        "Transcribe",
        type="primary",
        disabled=uploaded is None,
        key="btn_upload",
    )

    if transcribe_btn and uploaded:
        audio_bytes = uploaded.read()
        ext = uploaded.name.rsplit(".", 1)[-1].lower()
        stem = uploaded.name.rsplit(".", 1)[0]

        with st.spinner("Transcribing… this may take a moment for longer recordings."):
            result = transcribe(audio_bytes, language=lang_upload, model_size=model_size)

        st.session_state["upload_result"] = result
        st.session_state["upload_audio"] = audio_bytes
        st.session_state["upload_stem"] = stem
        st.session_state["upload_ext"] = ext

    if "upload_result" in st.session_state:
        render_result(
            st.session_state["upload_result"],
            st.session_state["upload_stem"],
            st.session_state["upload_audio"],
            st.session_state["upload_ext"],
        )


# ── Record tab ───────────────────────────────────────────────────────────────
with tab_record:
    st.markdown(
        '<div class="info-banner">'
        "Record directly from your microphone. Press the button to start, press again to stop. "
        "The recording stays in your browser until you transcribe — nothing is uploaded until you click <strong>Transcribe</strong>."
        "</div>",
        unsafe_allow_html=True,
    )

    try:
        from audio_recorder_streamlit import audio_recorder

        recorded_bytes = audio_recorder(
            text="Click to record",
            recording_color="#1a56db",
            neutral_color="#6b7280",
            icon_name="microphone",
            icon_size="2x",
            pause_threshold=3.0,
            sample_rate=16_000,
        )
    except ImportError:
        st.error(
            "`audio-recorder-streamlit` is not installed. "
            "Run `pip install audio-recorder-streamlit` and restart."
        )
        recorded_bytes = None

    lang_record = language_selector("lang_record")

    if recorded_bytes:
        st.audio(recorded_bytes, format="audio/wav")
        st.caption(f"Recording size: {len(recorded_bytes) / 1024:.1f} KB")

    transcribe_rec_btn = st.button(
        "Transcribe recording",
        type="primary",
        disabled=not recorded_bytes,
        key="btn_record",
    )

    if transcribe_rec_btn and recorded_bytes:
        from datetime import datetime

        stem = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with st.spinner("Transcribing…"):
            result = transcribe(recorded_bytes, language=lang_record, model_size=model_size)

        st.session_state["record_result"] = result
        st.session_state["record_audio"] = recorded_bytes
        st.session_state["record_stem"] = stem

    if "record_result" in st.session_state:
        render_result(
            st.session_state["record_result"],
            st.session_state["record_stem"],
            st.session_state["record_audio"],
            "wav",
        )

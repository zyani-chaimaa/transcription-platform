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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
    }

    #MainMenu, footer { visibility: hidden; }

    .block-container {
        padding-top: 2rem;
        max-width: 860px;
    }

    /* Header */
    .app-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #111827;
        letter-spacing: -0.02em;
        margin: 0;
    }
    .app-subtitle {
        font-size: 0.8rem;
        color: #9ca3af;
        margin: 3px 0 0;
        font-weight: 400;
    }
    .user-block {
        text-align: right;
        font-size: 0.82rem;
        color: #374151;
        line-height: 1.5;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 0;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 0.9rem;
        font-weight: 500;
        color: #6b7280;
        padding: 0.6rem 1.1rem;
        border-bottom: 2px solid transparent;
        margin-bottom: -1px;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #111827 !important;
        border-bottom: 2px solid #111827 !important;
        background: transparent !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
    .stTabs [data-baseweb="tab-border"] { display: none; }

    /* Info banner */
    .info-banner {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.65rem 1rem;
        font-size: 0.82rem;
        color: #64748b;
        margin-bottom: 1.25rem;
    }

    /* Transcript box */
    .transcript-box {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.25rem 1.5rem;
        line-height: 1.8;
        white-space: pre-wrap;
        font-size: 0.9rem;
        color: #1f2937;
        max-height: 400px;
        overflow-y: auto;
    }
    .transcript-box::-webkit-scrollbar { width: 5px; }
    .transcript-box::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }

    /* Segment rows */
    .seg-row {
        display: flex; gap: 1rem; padding: 0.45rem 0;
        border-bottom: 1px solid #f3f4f6; align-items: baseline;
    }
    .seg-row:last-child { border-bottom: none; }
    .seg-time {
        font-size: 0.72rem; color: #9ca3af; min-width: 115px;
        font-family: 'Menlo', monospace;
        background: #f3f4f6; border-radius: 4px;
        padding: 1px 6px; flex-shrink: 0;
    }
    .seg-text { font-size: 0.88rem; color: #111827; line-height: 1.6; }

    /* Metrics */
    [data-testid="metric-container"] {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.75rem 1rem;
    }
    [data-testid="metric-container"] label {
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #9ca3af !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #111827 !important;
    }
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
col_title, col_user = st.columns([5, 2])
with col_title:
    st.markdown(
        '<p class="app-title">Transcription Platform</p>'
        '<p class="app-subtitle">Powered by Whisper &nbsp;·&nbsp; Processed in memory &nbsp;·&nbsp; No data stored</p>',
        unsafe_allow_html=True,
    )
with col_user:
    avatar = (
        f'<img src="{user["picture"]}" style="width:28px;height:28px;border-radius:50%;vertical-align:middle;margin-right:6px;">'
        if user.get("picture") else ""
    )
    st.markdown(
        f'<div class="user-block" style="padding-top:4px;">'
        f'{avatar}<strong>{user["name"]}</strong><br>'
        f'<span style="color:#9ca3af;font-size:0.75rem;">{user["email"]}</span></div>',
        unsafe_allow_html=True,
    )
    if st.button("Sign out", use_container_width=True):
        logout()

st.markdown('<hr style="border:none;border-top:1px solid #e5e7eb;margin:0.75rem 0 1.5rem;">', unsafe_allow_html=True)

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
        rows = "".join(
            f'<div class="seg-row">'
            f'<span class="seg-time">{_fmt_ts(seg["start"])} → {_fmt_ts(seg["end"])}</span>'
            f'<span class="seg-text">{seg["text"].strip()}</span>'
            f'</div>'
            for seg in result["segments"]
        )
        st.markdown(f'<div class="transcript-box">{rows}</div>', unsafe_allow_html=True)

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
tab_upload, tab_record = st.tabs(["Upload file", "Record audio"])


# ── Upload tab ──────────────────────────────────────────────────────────────
with tab_upload:
    st.markdown(
        '<div class="info-banner">'
        "Supported formats: MP3, M4A, WAV, OGG, FLAC · Max recommended size: 200 MB · Files are not stored after your session ends."
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
        "Press the button to start recording, press again to stop. Nothing is uploaded until you click Transcribe."
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

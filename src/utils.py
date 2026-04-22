import json
import math
import streamlit as st


def format_txt(result: dict) -> str:
    return result["text"]


def format_srt(result: dict) -> str:
    lines: list[str] = []
    for i, seg in enumerate(result["segments"], 1):
        lines += [
            str(i),
            f"{_ts_srt(seg['start'])} --> {_ts_srt(seg['end'])}",
            seg["text"],
            "",
        ]
    return "\n".join(lines)


def format_vtt(result: dict) -> str:
    lines = ["WEBVTT", ""]
    for i, seg in enumerate(result["segments"], 1):
        lines += [
            str(i),
            f"{_ts_vtt(seg['start'])} --> {_ts_vtt(seg['end'])}",
            seg["text"],
            "",
        ]
    return "\n".join(lines)


def format_json(result: dict) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)


def download_section(result: dict, stem: str) -> None:
    """Render four download buttons for all transcript formats."""
    st.markdown("#### Download transcript")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button(
            "TXT",
            data=format_txt(result).encode("utf-8"),
            file_name=f"{stem}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            "SRT",
            data=format_srt(result).encode("utf-8"),
            file_name=f"{stem}.srt",
            mime="text/plain",
            use_container_width=True,
        )
    with col3:
        st.download_button(
            "VTT",
            data=format_vtt(result).encode("utf-8"),
            file_name=f"{stem}.vtt",
            mime="text/vtt",
            use_container_width=True,
        )
    with col4:
        st.download_button(
            "JSON",
            data=format_json(result).encode("utf-8"),
            file_name=f"{stem}.json",
            mime="application/json",
            use_container_width=True,
        )


def result_metadata(result: dict) -> None:
    duration = result.get("duration", 0)
    mins, secs = divmod(math.floor(duration), 60)
    hours, mins = divmod(mins, 60)

    duration_str = (
        f"{hours}h {mins}m {secs}s"
        if hours
        else f"{mins}m {secs}s"
        if mins
        else f"{secs}s"
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Duration", duration_str)
    col2.metric("Language detected", result.get("language", "—").upper())
    col3.metric("Confidence", f"{result.get('language_probability', 0):.1f}%")


# ---------------------------------------------------------------------------
# Timestamp helpers
# ---------------------------------------------------------------------------

def _ts_srt(s: float) -> str:
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    ms = round((sec % 1) * 1000)
    return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{ms:03d}"


def _ts_vtt(s: float) -> str:
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    ms = round((sec % 1) * 1000)
    return f"{int(h):02d}:{int(m):02d}:{int(sec):02d}.{ms:03d}"

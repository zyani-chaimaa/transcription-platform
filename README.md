# Multilingual AI Transcription Platform

**Speech-to-Text | Faster-Whisper | Python | Streamlit | Multilingual AI**

A multilingual speech-to-text application developed with **Python, Faster-Whisper, and Streamlit**. The platform converts uploaded audio/video files and microphone recordings into structured transcripts, supporting automatic language detection, timestamped transcription, and multiple export formats.

The project demonstrates the integration of an open-source speech recognition model into an interactive Python web application, with configurable inference, authentication, and transcript processing.

## Key Features

### 1. Multilingual Speech Recognition

- Speech-to-text transcription using Faster-Whisper.
- Automatic language detection or manual language selection.
- 15 selectable languages, including Arabic, English, French, Spanish, German, and Chinese.
- Configurable Whisper models: `tiny`, `base`, `small`, `medium`, and `large-v3`.
- Model caching with Streamlit to avoid unnecessary model reinitialization.

### 2. Audio Upload and Recording

Two input methods are implemented:

- **Upload:** Process supported audio and video files.
- **Record:** Capture audio directly through the browser using `audio-recorder-streamlit`.

Supported file formats: MP3, MP4, M4A, WAV, OGG, FLAC, WebM, and Opus.

The Streamlit application is configured with a 200 MB upload limit.

### 3. Hardware-Aware Model Inference

The transcription engine includes:

- CUDA detection when PyTorch is available.
- `float16` inference on CUDA-enabled devices and `int8` inference on CPU.
- Beam search configuration based on the selected device.
- Voice Activity Detection (VAD) with a 500 ms minimum silence duration.
- Segment-level timestamps.
- Cached model initialization using `st.cache_resource`.

The default model is `medium`. Actual performance depends on the runtime environment and selected model.

### 4. Transcript Visualization and Export

Users can review transcripts in two formats:

- **Full Text:** Complete transcription.
- **With Timestamps:** Individual speech segments with start and end times.

The interface also displays recording duration, detected language, and the language-detection probability returned by the model.

Available downloads:

| Format | Description |
|---|---|
| TXT | Plain-text transcription |
| SRT | Timestamped subtitles |
| VTT | WebVTT subtitles |
| JSON | Structured transcription data |

### 5. Google Authentication

The application includes a custom Google OAuth 2.0 sign-in flow with:

- Google authorization-code authentication.
- Retrieval of user profile information.
- Streamlit session-based authentication state.
- Sign-in and sign-out interface elements.

The code also retains a Google Cloud IAP integration path from an earlier deployment design.

**Current limitation:** Google sign-in is not currently functioning successfully in the hosted application and requires further configuration or debugging.

## Application Architecture

```text
                   USER
                     |
                     v
             Streamlit Web App
                 (app.py)
                     |
              Authentication
                (auth.py)
                     |
             +-------+-------+
             |               |
             v               v
         Upload File     Record Audio
             |               |
             +-------+-------+
                     |
                     v
           Language Selection
          Auto-detect / Manual
                     |
                     v
          Faster-Whisper Engine
           (transcription.py)
                     |
             +-------+-------+
             |               |
       Model Loading     Audio Processing
       & Caching         VAD / Inference
             |               |
             +-------+-------+
                     |
                     v
          Transcript + Timestamps
                     |
                     v
           Results & Formatting
                (utils.py)
                     |
                     v
           TXT / SRT / VTT / JSON
```

The application runs transcription within the Streamlit Python process rather than through a separate backend API.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Web application | Streamlit |
| Speech recognition | Faster-Whisper |
| Audio recording | audio-recorder-streamlit |
| Audio decoding | FFmpeg |
| Language detection | Whisper |
| Authentication | Google OAuth 2.0 |
| Transcript processing | Python, JSON |
| Application configuration | Streamlit configuration, python-dotenv |

## Project Structure

```text
transcription-platform/
├── .streamlit/
│   └── config.toml
├── src/
│   ├── __init__.py
│   ├── auth.py
│   ├── transcription.py
│   └── utils.py
├── app.py
├── requirements.txt
├── packages.txt
├── .gitignore
└── README.md
```

**Main components**

- `app.py`: Streamlit interface, audio upload, browser recording, and transcription results.
- `src/auth.py`: Google OAuth flow and authentication state.
- `src/transcription.py`: Faster-Whisper model initialization, device selection, and speech recognition.
- `src/utils.py`: Transcript formatting, timestamp conversion, and downloads.
- `.streamlit/config.toml`: Interface theme and server settings.
- `requirements.txt`: Python dependencies.
- `packages.txt`: FFmpeg installation requirement for compatible hosting environments.

## Getting Started

### Prerequisites

- Python 3.10 or newer
- pip
- Google OAuth credentials
- Internet access for the initial Whisper model download

### 1. Clone the Repository

```bash
git clone https://github.com/zyani-chaimaa/transcription-platform.git
cd transcription-platform
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Ensure the runtime has the necessary audio-decoding support. The repository includes `packages.txt` containing `ffmpeg` for supported hosting environments.

### 4. Configure Google Authentication

Create a `.env` file in the project root:

```dotenv
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
REDIRECT_URI=http://localhost:8501
WHISPER_MODEL=medium
ALLOW_MODEL_CHOICE=true
```

Configure the matching redirect URI in the Google OAuth client settings.

Do not commit real credentials or your `.env` file.

### 5. Run the Application

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

A successful Google sign-in is required before accessing the transcription interface.

## Implementation Details

The application loads a Faster-Whisper model using `WhisperModel` and caches it with Streamlit.

For each transcription request:

1. Audio bytes are received from the uploader or browser recorder.
2. A temporary audio file is created for inference.
3. The model processes the audio using the selected language and VAD settings.
4. Recognized segments are collected with timestamps.
5. The application constructs the complete transcription and result metadata.
6. Results are retained in Streamlit session state for display and download.

The repository does not implement a persistent transcript database. Audio is temporarily written to disk during inference, so the application should not be characterized as exclusively in-memory processing.

## Current Status and Future Improvements

The Streamlit application and transcription workflows are implemented in the repository. However, the hosted Google sign-in flow currently returns a 403 error, so end-to-end hosted transcription is not presently verified.

Future improvements include:

- Fixing and validating Google OAuth authentication.
- Adding automated tests for transcription and export utilities.
- Evaluating speech recognition accuracy across supported languages.
- Improving error handling and input validation.
- Reviewing privacy messaging and authentication security.
- Benchmarking inference performance across different Whisper models.

## Author

**Chaimaa Zyani**

AI Engineer | Generative AI & Agentic AI | RAG | Azure AI

[Portfolio](https://zyanichaimaa.netlify.app/) · [GitHub](https://github.com/zyani-chaimaa)

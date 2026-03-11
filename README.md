<div align="center">

<img src="frontend/app/static/img/video-placeholder.svg" width="80" alt="SpeechCraft Logo"/>

# 🎙️ SpeechCraft

### Open-Source AI-Powered Speech Transcription Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![Whisper](https://img.shields.io/badge/OpenAI-Whisper-412991?logo=openai&logoColor=white)](https://github.com/openai/whisper)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**SpeechCraft** is a free, open-source platform that transcribes audio and video files into editable, timestamped text : then lets you embed styled subtitles back into your videos.
No SaaS fees. No data leaving your infrastructure. Fully self-hosted.

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [Configuration](#-configuration) · [Roadmap](#-roadmap) · [Contributing](#-contributing)

---

</div>

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎵 **Multi-format Upload** | MP3, WAV, OGG, M4A, FLAC, AAC, WebM, MP4, AVI, MOV, MKV |
| 🎙️ **Live Recording** | Record directly in the browser and transcribe instantly |
| 🤖 **AI Transcription** | Powered by [OpenAI Whisper](https://github.com/openai/whisper) : runs entirely on your hardware; model selectable from the UI (`tiny` → `large`) |
| ⚡ **Async Processing** | Celery + Redis task queue; uploads return immediately while transcription runs in background |
| ✏️ **Interactive Editor** | Click any segment to edit text, jump to that timestamp in the media player |
| 🎬 **Subtitle Embedding** | Burn styled SRT subtitles into video via FFmpeg (font, size, color, outline) |
| 🔐 **Authentication** | Email/password + Google OAuth 2.0 |
| ☁️ **Flexible Storage** | AWS S3 with automatic local-disk fallback |
| 📊 **Service Health Panel** | Live status of Frontend, Backend API, and Celery Worker in the sidebar |
| 🐳 **One-command Deploy** | Full stack via Docker Compose |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│          Flask Frontend  (port 5000)                        │
│   Auth · Workspace · Media Player · Transcript Editor       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP
           ┌───────────▼────────────┐
           │   FastAPI Backend      │  (port 8000)
           │   POST /stt            │
           └───────────┬────────────┘
                       │ enqueue task
           ┌───────────▼────────────┐      ┌──────────────────┐
           │       Redis            │◄─────►  Celery Worker   │
           │  (broker + results)    │      │  OpenAI Whisper  │
           └────────────────────────┘      └────────┬─────────┘
                                                    │ POST /callback
                                          ┌─────────▼─────────┐
                                          │  Flask /callback   │
                                          │  Save segments     │
                                          └───────────────────┘
```

**Services:**

| Service | Tech | Port | Role |
|---------|------|------|------|
| `frontend` | Flask + Gunicorn | `5000` | Web UI, auth, file management |
| `backend` | FastAPI + Uvicorn | `8000` | STT API, task scheduling |
| `celery` | Celery Worker | : | Runs Whisper transcription |
| `redis` | Redis Alpine | `6379` | Message broker + task results |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) v2+
- Git

### 1 : Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/SpeechCraft.git
cd SpeechCraft
```

### 2 : Configure environment

Copy and edit the environment file:

```bash
cp .env.example .env
```

Minimum required variables (edit `.env`):

```env
# Flask session secret : change this to a random string
SESSION_SECRET=your-secret-key-here

# Optional: Google OAuth (leave blank to disable Google login)
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=

# Optional: AWS S3 (leave blank to use local disk storage)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
S3_BUCKET_NAME=

# Optional: PostgreSQL (leave blank to use SQLite)
DATABASE_URL=
```

### 3 : Build and run

```bash
docker compose up --build
```

> First run downloads the Whisper model (~140 MB for `base`). Subsequent starts are fast.

### 4 : Open in your browser

| URL | Description |
|-----|-------------|
| http://localhost:5000 | Web application |
| http://localhost:5000/workspace | Transcription workspace |
| http://localhost:8000/docs | FastAPI interactive API docs |

### 5 : Create an account

Navigate to `http://localhost:5000`, click **Sign Up**, and register with your email.

---

## 🗂️ Project Structure

```
SpeechCraft/
├── backend/                    # FastAPI microservice
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/stt/         # POST /stt endpoint
│   │   │   ├── tasks.py        # Celery STT task
│   │   │   └── worker.py       # Celery configuration
│   │   ├── src/
│   │   │   └── stt_main/
│   │   │       ├── base.py     # Abstract STT interface
│   │   │       ├── factory.py  # STT provider factory
│   │   │       └── whisperSTT/ # OpenAI Whisper implementation
│   │   └── utils/
│   │       └── callbackhandler.py
│   ├── main.py                 # FastAPI app + health endpoints
│   └── Dockerfile
│
├── frontend/                   # Flask web UI
│   ├── app/
│   │   ├── auth/               # Email + Google OAuth blueprints
│   │   ├── main/               # Routes, FFmpeg subtitle utils
│   │   ├── static/
│   │   │   ├── css/style.css
│   │   │   └── js/
│   │   │       ├── app.js              # Global utilities
│   │   │       ├── media-player.js     # In-browser media player
│   │   │       ├── media-processor.js  # Client-side audio extraction
│   │   │       ├── transcript-editor.js
│   │   │       ├── recorder.js         # Live audio recorder (AudioRecorder class)
│   │   │       └── waveform-visualizer.js  # Canvas frequency visualizer
│   │   ├── templates/          # Jinja2 HTML templates
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── storage.py          # S3 / local storage manager
│   │   └── utils.py            # File processing, FFmpeg, API calls
│   ├── main.py
│   └── Dockerfile
│
├── docker-compose.yaml         # Full-stack orchestration
└── README.md
```

---

## ⚙️ Configuration

### Environment Variables

#### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `SESSION_SECRET` | `change-me-in-production` | Flask session signing key |
| `FLASK_CONFIG` | `development` | `development` / `production` / `testing` |
| `DATABASE_URL` | SQLite | PostgreSQL connection string for production |
| `BACKEND_URL` | `http://localhost:8000` | Internal URL of the FastAPI backend |
| `CALLBACK_URL` | `http://frontend:5000` | URL Celery posts results back to |
| `GOOGLE_OAUTH_CLIENT_ID` | : | Google OAuth app client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | : | Google OAuth app secret |
| `AWS_ACCESS_KEY_ID` | : | S3 credentials |
| `AWS_SECRET_ACCESS_KEY` | : | S3 credentials |
| `AWS_REGION` | `us-east-1` | S3 bucket region |
| `S3_BUCKET_NAME` | : | S3 bucket name |

#### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Redis broker URL |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | Redis result backend |

### Whisper Model Size

The Whisper model is selected **directly from the workspace UI** before transcribing : no code changes needed.

| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | ~1 GB | ⚡⚡⚡⚡ | ★★☆☆ |
| `base` | ~1 GB | ⚡⚡⚡ | ★★★☆ *(default)* |
| `small` | ~2 GB | ⚡⚡ | ★★★★ |
| `medium` | ~5 GB | ⚡ | ★★★★ |
| `large` | ~10 GB | 🐢 | ★★★★★ |

> CPU is supported. GPU (CUDA) is used automatically when available. Models are cached after first load : switching models only re-downloads once.

---

## 🔄 Internal Data Flow

Three input paths all converge on the same Whisper transcription pipeline.

---

### 🎵 Path 1 : Audio File Upload

```
┌─────────────────────────────────────────────────────────────────────────┐
│  BROWSER                                                                 │
│                                                                          │
│  User picks file + selects Whisper model from dropdown                  │
│  FormData { file, model_name }  ──POST /upload──►  Flask Frontend       │
└─────────────────────────────────────────────────────────────────────────┘
                                        │
                              ┌─────────▼──────────────────────────────┐
                              │  FLASK  /upload                         │
                              │                                          │
                              │  1. validate extension (whitelist)       │
                              │  2. upload original file                 │
                              │     └─► S3 bucket  (or  /local_storage) │
                              │  3. read file bytes → base64 encode      │
                              │  4. INSERT TranscriptionJob              │
                              │     status = "processing"                │
                              │  5. POST /stt  ──────────────────────►  │
                              │     { audio_data, callback_url,          │
                              │       model_name }                       │
                              └──────────────────────────────────────────┘
                                        │
                              ┌─────────▼──────────────────────────────┐
                              │  FASTAPI  /stt                           │
                              │                                          │
                              │  6. stt_task.apply_async(kwargs)         │
                              │  7. return { task_id }  immediately      │
                              └───────────┬────────────────────────────┘
                                          │ enqueue
                              ┌───────────▼────────┐
                              │      REDIS          │
                              │  (message broker)   │
                              └───────────┬─────────┘
                                          │ dequeue
                              ┌───────────▼────────────────────────────┐
                              │  CELERY WORKER                           │
                              │                                          │
                              │  8.  main_driver.main(**kwargs)          │
                              │      └─ stt_type = "whisper" (default)   │
                              │  9.  STTFactory → WhisperSTT(model_name) │
                              │      └─ load_model(model_name) [cached]  │
                              │  10. base64 decode → temp .wav file      │
                              │  11. model.transcribe(                   │
                              │        audio_file,                       │
                              │        condition_on_previous_text=False, │
                              │        no_speech_threshold=0.6           │
                              │      )                                   │
                              │  12. POST /callback                      │
                              │      { task_id, status, segments[] }     │
                              └───────────┬────────────────────────────┘
                                          │
                              ┌───────────▼────────────────────────────┐
                              │  FLASK  /callback                        │
                              │                                          │
                              │  13. lookup job by api_task_id           │
                              │  14. INSERT TranscriptSegment rows       │
                              │      { segment_id, start, end, text }    │
                              │  15. job.status = "completed"            │
                              └───────────┬────────────────────────────┘
                                          │
                              ┌───────────▼────────────────────────────┐
                              │  BROWSER  (polling /job_status every 3s) │
                              │                                          │
                              │  16. status == "completed"               │
                              │      → redirect to /job/<id>             │
                              │  17. Media Player + Transcript Editor    │
                              └──────────────────────────────────────────┘
```

---

### 🎬 Path 2 : Video File Upload

Identical to Path 1 except Flask performs **server-side audio extraction** before encoding:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  BROWSER                                                                 │
│  FormData { video_file, model_name }  ──POST /upload──►  Flask          │
└─────────────────────────────────────────────────────────────────────────┘
                                        │
                              ┌─────────▼──────────────────────────────┐
                              │  FLASK  /upload  (video branch)          │
                              │                                          │
                              │  1. upload original video ──► Storage   │
                              │  2. write video to temp file             │
                              │  3. ffmpeg -i video.mp4 \                │
                              │          -q:a 0 -map a  audio.mp3        │
                              │     (server-side subprocess)             │
                              │  4. upload extracted MP3 ──► Storage    │
                              │  5. base64 encode MP3 bytes              │
                              │  6. INSERT TranscriptionJob              │
                              │     original_file_url  = video URL       │
                              │     audio_file_url     = MP3 URL         │
                              │  7. POST /stt { audio_data, model_name } │
                              └─────────┬──────────────────────────────┘
                                        │
                                   (same pipeline as Path 1 from step 6)
                                        │
                              ┌─────────▼──────────────────────────────┐
                              │  Workspace : video result view           │
                              │                                          │
                              │  Media Player plays original video       │
                              │  Transcript synced to video timeline     │
                              │  "Embed SRT" burns subtitles via FFmpeg  │
                              └──────────────────────────────────────────┘
```

---

### 🎙️ Path 3 : Live Browser Recording

Audio never leaves the browser until the user clicks **Transcribe Recording**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  BROWSER                                                                 │
│                                                                          │
│  1. getUserMedia({ audio: true })                                        │
│     └─► MediaStream                                                      │
│                                                                          │
│  2. WaveformVisualizer                                                   │
│     └─► Web Audio API AnalyserNode                                       │
│         └─► canvas frequency bars (real-time)                            │
│                                                                          │
│  3. AudioRecorder (MediaRecorder API)                                    │
│     └─► accumulates chunks [ Blob(webm) … ]                              │
│                                                                          │
│  4. User clicks Stop                                                      │
│     └─► Blob assembled → object URL → <audio> preview                   │
│                                                                          │
│  5. User clicks "Transcribe Recording"                                   │
│     └─► recorder.getFile()                                               │
│         returns  File("recording_<timestamp>.webm", "audio/webm")        │
│                                                                          │
│  6. handleFileUpload(file)  ◄─── same function used by file upload      │
│     └─► uploadFile(file)                                                 │
│         FormData { file: recording.webm, model_name }                   │
│         POST /upload                                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                        │
                              ┌─────────▼──────────────────────────────┐
                              │  FLASK  /upload  (audio branch)          │
                              │  webm treated as audio : no extraction   │
                              │  base64 encode → POST /stt               │
                              └─────────┬──────────────────────────────┘
                                        │
                                   (same pipeline as Path 1 from step 6)
```

---

### 📦 Storage Layer

```
StorageManager.upload_file()
        │
        ├─ AWS_ACCESS_KEY_ID set?
        │        YES ──► boto3  → S3 bucket  (returns public URL)
        │        NO  ──► write to  frontend/app/static/uploads/
        │                         (returns /static/uploads/<path>)
        │
        └─ Both paths return { success, url, key, storage_type }
```

---

### 🗄️ Database Schema (key tables)

```
TranscriptionJob
  id, user_id, filename, file_type
  status          ← "processing" | "completed" | "error"
  original_file_url, audio_file_url, storage_key
  api_task_id     ← links to Celery task / callback lookup
  created_at

TranscriptSegment
  id, transcription_job_id
  segment_id, start_time, end_time
  original_text   ← raw Whisper output
  edited_text     ← user edits (NULL until edited)
```

---

## 🛠️ Development Setup

Running services individually without Docker:

```bash
# 1. Start Redis
docker run -d -p 6379:6379 redis:alpine

# 2. Backend
cd backend
uv sync
uv run uvicorn main:app --reload --port 8000

# 3. Celery worker (separate terminal)
cd backend
uv run celery -A app.api.worker.celery worker --loglevel=info

# 4. Frontend
cd frontend
uv sync
uv run python main.py
```

---

## 🗺️ Roadmap

### ✅ Done
- [x] Multi-format audio & video upload
- [x] Async transcription with Celery + Redis
- [x] Interactive transcript editor with timeline
- [x] Subtitle embedding via FFmpeg
- [x] Email + Google OAuth authentication
- [x] AWS S3 + local storage
- [x] Live browser audio recording
- [x] Service health dashboard
- [x] Docker Compose full-stack deployment
- [x] UI-selectable Whisper model (tiny → large) per transcription

### 🔜 Coming Soon

- [ ] **🌍Subtitle Translation** : Translate transcribed subtitles into any language using an LLM 
- [ ] **🌍QnA with Transcript** : Plan to add RAG system to do QnA with generated transcripts
---

## 🤝 Contributing

Contributions are what make open source great. All PRs are welcome!

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/amazing-feature`
3. Commit your changes: `git commit -m "feat: add amazing feature"`
4. Push to the branch: `git push origin feat/amazing-feature`
5. Open a Pull Request

Please open an issue first for large changes so we can discuss the approach.

---

## 🐛 Reporting Issues

Found a bug or have a feature request?
→ [Open an issue](https://github.com/YOUR_USERNAME/SpeechCraft/issues)

---

## 📄 License

This project is licensed under the **MIT License** : see the [LICENSE](LICENSE) file for details.
Free to use, modify, and distribute.

---

## 🙏 Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) : the STT engine that powers transcription
- [FastAPI](https://fastapi.tiangolo.com) : modern Python web framework
- [Flask](https://flask.palletsprojects.com) : lightweight WSGI web application framework
- [Celery](https://docs.celeryq.dev) : distributed task queue
- [FFmpeg](https://ffmpeg.org) : audio/video processing

---

<div align="center">

Made with ❤️ · Open Source Forever

⭐ **Star this repo if SpeechCraft is useful to you!** ⭐

</div>

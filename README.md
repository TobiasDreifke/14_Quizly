# Quizly – AI-Powered Quiz Generator from YouTube Videos

Quizly is a Django REST API backend that turns any YouTube video into an interactive quiz. It extracts audio, transcribes it with Whisper AI, and generates 10 multiple-choice questions using Google Gemini Flash: all automatically.

---

## Tech Stack

- **Backend**: Django + Django REST Framework
- **Authentication**: JWT via `djangorestframework-simplejwt` with HTTP-Only Cookies
- **YouTube Download**: `yt-dlp`
- **Audio Extraction**: `ffmpeg` (called internally by yt-dlp)
- **Transcription**: OpenAI Whisper (runs locally, GPU-accelerated)
- **Quiz Generation**: Google Gemini Flash API
- **Frontend**: [Quizly Frontend](https://github.com/Developer-Akademie-Backendkurs/project.Quizly) (Vanilla JS, provided separately)

---

## Requirements

Before you start, make sure you have the following installed **globally** on your system:

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/download.html) - must be accessible in your system PATH
- [Deno](https://deno.land/) - required by yt-dlp for YouTube extraction
- A **NVIDIA GPU** is strongly recommended for Whisper transcription (CPU works but is significantly slower)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/TobiasDreifke/14_Quizly.git
cd 14_Quizly
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install PyTorch with CUDA support (for GPU-accelerated Whisper)

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

> If you don't have an NVIDIA GPU, skip this step. Whisper will fall back to CPU automatically.

### 5. Set up environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True
GEMINI_API_KEY=your_gemini_api_key
ALLOWED_HOSTS=127.0.0.1,localhost
```

Get your free Gemini API key at [Google AI Studio](https://aistudio.google.com/).

### 6. Run migrations

```bash
python manage.py migrate
```

### 7. Start the development server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000`.

---

## Frontend Setup

Clone and open the frontend separately:

```bash
git clone https://github.com/Developer-Akademie-Backendkurs/project.Quizly quizly_frontend
```

Open the `quizly_frontend` folder directly in VS Code and start Live Server from there. Make sure the URL is `http://127.0.0.1:5500/index.html` - not a subfolder path.

---

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register/` | Register a new user |
| POST | `/api/login/` | Login and receive JWT cookies |
| POST | `/api/logout/` | Logout and blacklist tokens |
| GET | `/api/quizzes/` | Get all quizzes for the current user |
| POST | `/api/quizzes/` | Create a new quiz from a YouTube URL |
| GET | `/api/quizzes/{id}/` | Get a specific quiz |
| PATCH | `/api/quizzes/{id}/` | Update quiz title or description |
| DELETE | `/api/quizzes/{id}/` | Delete a quiz |

### Example: Create a Quiz

```bash
POST /api/quizzes/
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=your_video_id"
}
```

Authentication is handled via HTTP-Only cookies set at login: no Authorization header needed.

---

## How It Works

```
YouTube URL
    ↓
Check for existing YouTube subtitles (fast path)
    ↓ if none available
Download audio via yt-dlp + ffmpeg
    ↓
Transcribe audio with Whisper AI (local, GPU-accelerated)
    ↓
Send transcript to Google Gemini Flash
    ↓
Save Quiz + 10 Questions to database
    ↓
Return JSON response
```

---

## Project Structure

```
14_Quizly/
├── auth_app/           # JWT authentication (register, login, logout)
├── quizzes_app/
│   ├── API/
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── serializers.py
│   ├── models.py       # Quiz and Question models
│   ├── services.py     # Gemini AI quiz generation
│   └── utils.py        # yt-dlp, Whisper transcription
├── core/               # Django project settings
├── manage.py
└── requirements.txt
```

---

## Notes

- On first run, Whisper will download the `small` model (~460 MB). This is cached locally after the first download.
- Gemini Flash has a free tier daily quota. If you hit the limit, the app automatically falls back to other available Gemini models.
- ffmpeg must be installed and available in your system PATH for audio extraction to work.
- Only public YouTube videos are supported.

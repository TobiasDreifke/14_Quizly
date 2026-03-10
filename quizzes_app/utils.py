import whisper
import yt_dlp
import tempfile
import os
import requests
import json

# Modell einmal laden, nicht bei jedem Aufruf
_whisper_model = None


def _get_whisper_model():
    """Lädt das Whisper-Modell einmalig und cached es."""
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("small", device="cuda")
    return _whisper_model


def _extract_caption_url(captions: dict) -> str:
    """Gibt die URL der bevorzugten Untertitelsprache zurück."""
    for lang in ["en", "de"]:
        if lang in captions:
            return captions[lang][0]["url"]
    first_lang = list(captions.keys())[0]
    return captions[first_lang][0]["url"]


def _parse_caption_response(response_text: str) -> str:
    """Parst die JSON-Untertitel und gibt einen bereinigten Text zurück."""
    data = json.loads(response_text)
    words = [
        seg.get("utf8", "").strip()
        for event in data.get("events", [])
        for seg in event.get("segs", [])
        if seg.get("utf8", "").strip()
    ]
    return " ".join(dict.fromkeys(words))


def get_youtube_transcript(url: str) -> str | None:
    """Versucht vorhandene YouTube-Untertitel abzurufen."""
    with yt_dlp.YoutubeDL({"skip_download": True, "quiet": True}) as ydl:
        info = ydl.extract_info(url, download=False)

    captions = info.get("subtitles") or info.get("automatic_captions")
    if not captions:
        return None

    subtitle_url = _extract_caption_url(captions)
    response = requests.get(subtitle_url)

    if response.status_code != 200:
        return None

    return _parse_caption_response(response.text)


def download_youtube_audio(url: str) -> str:
    """Lädt Audio eines YouTube-Videos herunter und gibt den Dateipfad zurück."""
    tmp_dir = tempfile.mkdtemp()
    tmp_filename = os.path.join(tmp_dir, "audio")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": tmp_filename,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return f"{tmp_filename}.mp3"


def transcribe_audio(audio_path: str) -> str:
    """Transkribiert eine Audiodatei lokal mit Whisper AI."""
    model = _get_whisper_model()
    result = model.transcribe(audio_path)
    return result["text"]


def get_video_transcript(url: str) -> str:
    """
    Hauptfunktion: Gibt Transkript eines YouTube-Videos zurück.
    Nutzt zuerst vorhandene Untertitel, sonst Whisper AI als Fallback.
    """
    print("Suche nach vorhandenen YouTube Untertiteln...")
    transcript = get_youtube_transcript(url)

    if transcript:
        print("YouTube Transcript gefunden!")
        return transcript

    print("Keine Untertitel gefunden -> Whisper wird genutzt")
    audio_path = download_youtube_audio(url)
    return transcribe_audio(audio_path)
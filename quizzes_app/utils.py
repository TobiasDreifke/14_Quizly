import whisper
import yt_dlp
import tempfile
import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()
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


def _build_quiz_prompt(transcript: str) -> str:
    """
    Builds the prompt sent to Gemini for quiz generation.

    Instructs Gemini to respond with a strictly structured JSON object only —
    no markdown, no preamble. The transcript is truncated to 8000 characters
    to stay within token limits.

    The prompt enforces:
        - Exactly 10 questions.
        - Exactly 4 answer options per question.
        - The correct answer must exactly match one of the options.
        - Questions are generated in the language of the transcript.

    Args:
        transcript: The full or truncated transcript text from the YouTube video.

    Returns:
        A formatted prompt string ready to be sent to the Gemini API.
    """
    return f"""
    You are a quiz generator. Create a quiz with exactly 10 questions based on the following transcript.

    IMPORTANT: Respond ONLY with a JSON object. No text before or after, no markdown backticks.

    Format:
    {{
      "title": "Short quiz title",
      "description": "Brief description of what the quiz is about",
      "questions": [
        {{
          "question_title": "The question?",
          "question_options": ["Option A", "Option B", "Option C", "Option D"],
          "answer": "Option A"
        }}
      ]
    }}

    Rules:
    - Exactly 10 questions
    - Exactly 4 answer options per question
    - "answer" must exactly match one of the "question_options"
    - Generate questions in the same language as the transcript

    Transcript:
    {transcript[:8000]}
    """


def _parse_gemini_response(raw: str) -> dict:
    """
    Safely parses the raw Gemini response text into a Python dictionary.

    Strips potential markdown code fences (```json ... ```) that Gemini may
    include despite being instructed not to, then parses the cleaned string as JSON.

    Args:
        raw: The raw response string from the Gemini API.

    Returns:
        A dictionary containing the quiz title, description, and list of questions.

    Raises:
        json.JSONDecodeError: If the response cannot be parsed as valid JSON.
    """
    cleaned = raw.strip().removeprefix("```json").removeprefix(
        "```").removesuffix("```").strip()
    return json.loads(cleaned)


def _is_quota_error(error_str: str) -> bool:
    """
    Returns True if the error indicates a free tier quota has been exhausted
    or the model is not found.

    Handles:
        429 RESOURCE_EXHAUSTED – Daily or per-minute free tier limit reached.
        404 NOT_FOUND          – Model name not available for this API version.

    Args:
        error_str: String representation of the caught exception.

    Returns:
        True if the error is quota- or availability-related, False otherwise.
    """
    return "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "404" in error_str


def _is_billing_error(error_str: str) -> bool:
    """
    Returns True only if the error indicates a paid quota would be charged.
    Gemini returns 402 PAYMENT_REQUIRED when free tier is exhausted and
    the request would incur costs.
    Note: 429 RESOURCE_EXHAUSTED messages may contain the word 'billing'
    in their description but are NOT billing errors — they are quota errors.
    """
    return "402" in error_str or "PAYMENT_REQUIRED" in error_str

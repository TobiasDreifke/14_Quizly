import os
from google import genai
from dotenv import load_dotenv
import json
from .utils import _is_billing_error, _is_quota_error, _build_quiz_prompt, _parse_gemini_response

load_dotenv()


def generate_quiz_from_transcript(transcript: str) -> dict:
    """
    Sends a transcript to the Gemini API and returns a generated quiz as a dictionary.

    Tries multiple Gemini models in order of preference. Free tier models are
    tried first. gemini-2.5-pro is included as a last resort but is skipped
    if a billing error is returned — ensuring no unexpected costs are incurred.

    If a model returns a quota (429), availability (404), or billing (402) error,
    the next model in the list is tried. Any other exception is re-raised immediately.

    Model fallback order:
        1. gemini-2.5-flash      – Best free quality, 500 requests/day.
        2. gemini-2.5-flash-lite – Lighter 2.5 variant, 1500 requests/day.
        3. gemini-2.0-flash      – Reliable and fast, 1500 requests/day.
        4. gemini-2.0-flash-lite – Most conservative free option, 1500 requests/day.
        5. gemini-flash-latest   – Alias for latest flash, used as safety net.
        6. gemini-2.5-pro        – Highest quality, free tier only (50 requests/day).
                                   Skipped automatically if billing would be triggered.

    Args:
        transcript: The transcript text to generate a quiz from.

    Returns:
        A dictionary with keys: 'title', 'description', and 'questions'.

    Raises:
        Exception: If all models have exhausted their quota or are unavailable.
    """
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = _build_quiz_prompt(transcript)

    models = [
        # Best quality, 50 free requests/day — skipped if billing triggers
        "gemini-2.5-pro",
        "gemini-2.5-flash",       # Best free quality, 500 requests/day
        "gemini-2.5-flash-lite",  # Lighter 2.5 variant, 1500 requests/day
        "gemini-2.0-flash",       # Reliable and fast, 1500 requests/day
        "gemini-2.0-flash-lite",  # Most conservative free option, 1500 requests/day
        "gemini-flash-latest",    # Alias for latest flash, last resort
    ]

    for model in models:
        try:
            print(f"Trying model: {model}")
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            print(f"Model {model} succeeded.")
            return _parse_gemini_response(response.text)

        except Exception as e:
            error_str = str(e)

            if _is_billing_error(error_str):
                print(
                    f"Model {model} requires payment — skipping to avoid charges.")
                continue

            if _is_quota_error(error_str):
                print(f"Model {model} unavailable: {error_str[:100]}")
                continue

            raise e

    raise Exception(
        "All Gemini models have exhausted their quota or are unavailable.")

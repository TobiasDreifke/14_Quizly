import os
from google import genai
from dotenv import load_dotenv
import json

load_dotenv()


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
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)


def generate_quiz_from_transcript(transcript: str) -> dict:
    """
    Sends a transcript to the Gemini API and returns a generated quiz as a dictionary.

    Tries multiple Gemini models in order of preference. If a model returns a 429
    (quota exhausted) or 404 (model not found), the next model in the list is tried.
    Any other exception is re-raised immediately.

    Model fallback order:
        1. gemini-2.0-flash       – Preferred, fast and free tier.
        2. gemini-2.0-flash-lite  – Lighter variant, separate quota.
        3. gemini-2.5-flash       – Next generation, higher quality.
        4. gemini-2.5-flash-lite  – Lighter 2.5 variant.
        5. gemini-2.5-pro         – Highest quality, used as last resort.
        6. gemini-flash-latest    – Alias for the latest flash model.

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
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-flash-latest",
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
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "404" in error_str:
                print(f"Model {model} unavailable: {error_str[:100]}")
                continue
            raise e

    raise Exception("All Gemini models have exhausted their quota or are unavailable.")
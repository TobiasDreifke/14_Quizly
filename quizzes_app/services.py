import os
from google import genai
from dotenv import load_dotenv

load_dotenv()


def _build_quiz_prompt(transcript: str) -> str:
    """Baut den Gemini-Prompt mit Transkript auf."""
    return f"""
    Du bist ein Quiz-Generator. Erstelle ein Quiz mit genau 10 Fragen basierend auf dem folgenden Transkript.
    
    WICHTIG: Antworte NUR mit einem JSON-Objekt. Kein Text davor oder danach, keine Markdown-Backticks.
    
    Format:
    {{
      "title": "Kurzer Titel des Quiz",
      "description": "Kurze Beschreibung worum es geht",
      "questions": [
        {{
          "question_title": "Die Frage?",
          "question_options": ["Option A", "Option B", "Option C", "Option D"],
          "answer": "Option A"
        }}
      ]
    }}
    
    Regeln:
    - Genau 10 Fragen
    - Genau 4 Antwortmöglichkeiten pro Frage
    - "answer" muss exakt einer der "question_options" entsprechen
    - Fragen auf Deutsch wenn das Transkript auf Deutsch ist
    
    Transkript:
    {transcript[:8000]}
    """


def _parse_gemini_response(raw: str) -> dict:
    """Parst die Gemini-Antwort sicher zu einem Dict."""
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)


def generate_quiz_from_transcript(transcript: str) -> dict:
    """Sendet Transkript an Gemini Flash und gibt Quiz als Dict zurück."""
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = _build_quiz_prompt(transcript)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    return _parse_gemini_response(response.text)
from quizzes_app.utils import get_video_transcript
from quizzes_app.services import generate_quiz_from_transcript

url = "https://www.youtube.com/watch?v=9WYxwYvFP2g"

print("Transcript wird geladen...")

transcript = get_video_transcript(url)

print("\nTRANSCRIPT:\n")
print(transcript[:1000])


transcript = get_video_transcript(url)
print(f"✅ Transkript: {transcript[:200]}")

print("⏳ Generiere Quiz mit Gemini...")
quiz = generate_quiz_from_transcript(transcript)
print(f"✅ Titel: {quiz['title']}")
print(f"✅ Fragen: {len(quiz['questions'])}")
print(f"✅ Erste Frage: {quiz['questions'][0]['question_title']}")

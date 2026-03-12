from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..models import Quiz, Question
from .serializers import QuizSerializer
from ..services import generate_quiz_from_transcript
from ..utils import get_video_transcript


class QuizListCreateView(APIView):
    """
    Handles listing and creating quizzes for the authenticated user.

    GET  /api/quizzes/  – Returns all quizzes belonging to the current user.
    POST /api/quizzes/  – Creates a new quiz from a YouTube URL.
                          The pipeline fetches a transcript (via subtitles or Whisper AI),
                          generates 10 questions using Gemini Flash, and saves the result.

    Permissions: Authentication required.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns a list of all quizzes created by the authenticated user,
        including all associated questions.
        """
        quizzes = Quiz.objects.filter(user=request.user)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Creates a new quiz from a YouTube URL.

        Expected request body:
            { "url": "https://www.youtube.com/watch?v=..." }

        Pipeline:
            1. Fetch transcript via YouTube subtitles or Whisper AI fallback.
            2. Send transcript to Gemini Flash to generate title, description, and 10 questions.
            3. Save Quiz and related Question objects to the database.

        Returns the full quiz object including all generated questions.
        """
        url = request.data.get("url")
        if not url:
            return Response({"error": "URL is required."}, status=status.HTTP_400_BAD_REQUEST)

        transcript = get_video_transcript(url)
        quiz_data = generate_quiz_from_transcript(transcript)

        quiz = Quiz.objects.create(
            user=request.user,
            title=quiz_data["title"],
            description=quiz_data["description"],
            video_url=url,
        )
        for q in quiz_data["questions"]:
            Question.objects.create(quiz=quiz, **q)

        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuizDetailView(APIView):
    """
    Handles retrieving, updating, and deleting a specific quiz.

    GET    /api/quizzes/{id}/  – Returns the quiz with all questions.
    PATCH  /api/quizzes/{id}/  – Partially updates title and/or description.
    DELETE /api/quizzes/{id}/  – Permanently deletes the quiz and all its questions.

    Permissions: Authentication required. Users can only access their own quizzes.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        """
        Retrieves a quiz by primary key and verifies ownership.
        Returns None if the quiz does not exist or belongs to a different user.
        Combining existence and ownership checks prevents leaking quiz IDs.
        """
        try:
            return Quiz.objects.get(pk=pk, user=user)
        except Quiz.DoesNotExist:
            return None

    def get(self, request, pk):
        """
        Returns a single quiz including all associated questions.
        Responds with 404 if the quiz does not exist or does not belong to the user.
        """
        quiz = self.get_object(pk, request.user)
        if not quiz:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """
        Partially updates a quiz. Only 'title' and 'description' are editable.

        Expected request body (all fields optional):
            { "title": "New Title", "description": "New Description" }

        Uses partial=True so only provided fields are updated.
        Responds with 404 if the quiz does not exist or does not belong to the user.
        """
        quiz = self.get_object(pk, request.user)
        if not quiz:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = QuizSerializer(quiz, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Permanently deletes a quiz and all its associated questions (CASCADE).
        This action cannot be undone.
        Responds with 404 if the quiz does not exist or does not belong to the user.
        """
        quiz = self.get_obj

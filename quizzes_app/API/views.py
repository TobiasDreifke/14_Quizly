from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from ..models import Quiz, Question
from .serializers import QuizSerializer
from ..services import generate_quiz_from_transcript
from ..utils import get_video_transcript


class QuizListCreateView(APIView):
    """GET alle Quizze des Users / POST neues Quiz aus YouTube-URL."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        quizzes = Quiz.objects.filter(user=request.user)
        serializer = QuizSerializer(quizzes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        url = request.data.get("url")
        if not url:
            return Response({"error": "URL fehlt."}, status=status.HTTP_400_BAD_REQUEST)

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
    """GET / PATCH / DELETE für ein spezifisches Quiz."""

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        """Holt Quiz und prüft ob es dem User gehört."""
        try:
            return Quiz.objects.get(pk=pk, user=user)
        except Quiz.DoesNotExist:
            return None

    def get(self, request, pk):
        quiz = self.get_object(pk, request.user)
        if not quiz:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = QuizSerializer(quiz)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        quiz = self.get_object(pk, request.user)
        if not quiz:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = QuizSerializer(quiz, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        quiz = self.get_object(pk, request.user)
        if not quiz:
            return Response(status=status.HTTP_404_NOT_FOUND)
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

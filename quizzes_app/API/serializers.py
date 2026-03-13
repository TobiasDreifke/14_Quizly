from rest_framework import serializers
from ..models import Quiz, Question


class QuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for individual quiz questions.

    Serializes all question fields including the list of answer options (stored as JSON)
    and the correct answer. Used as a nested serializer inside QuizSerializer.

    Fields:
        id              - Primary key.
        question_title  - The question text.
        question_options - List of 4 answer choices (JSON array).
        answer          - The correct answer (must match one of question_options).
        created_at      - Timestamp of creation (auto-set).
        updated_at      - Timestamp of last update (auto-set).
    """

    class Meta:
        model = Question
        fields = [
            "id",
            "question_title",
            "question_options",
            "answer",
            "created_at",
            "updated_at",
        ]


class QuizSerializer(serializers.ModelSerializer):
    """
    Serializer for a quiz including all associated questions.

    The 'questions' field is a nested read-only list of QuestionSerializer instances,
    populated via the reverse relation defined by related_name='questions' on the
    Question model. Questions are never written through this serializer — they are
    created internally by the quiz generation pipeline.

    Fields:
        id          - Primary key.
        title       - Quiz title (AI-generated, editable via PATCH).
        description - Short description (AI-generated, editable via PATCH).
        created_at  - Timestamp of creation (auto-set).
        updated_at  - Timestamp of last update (auto-set).
        video_url   - The original YouTube URL used to generate the quiz.
        questions   - Nested list of all associated questions (read-only).
    """

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]

from django.contrib import admin
from .models import Quiz, Question


class QuestionInline(admin.TabularInline):
    """Shows questions directly inside the Quiz admin view."""
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Admin view for Quiz — shows questions inline."""
    list_display = ["title", "user", "created_at", "updated_at"]
    list_filter = ["user", "created_at"]
    search_fields = ["title", "description"]
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin view for individual questions."""
    list_display = ["question_title", "quiz", "answer"]
    search_fields = ["question_title", "quiz__title"]
    list_filter = ["quiz"]
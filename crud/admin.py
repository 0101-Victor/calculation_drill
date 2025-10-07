from django.contrib import admin
from .models import ProblemMistake, ScoreHistory, Feedback

@admin.register(ProblemMistake)
class ProblemMistakeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "drill", "a", "b", "correct_answer", "created_at")
    list_filter = ("drill", "created_at")
    search_fields = ("user__username", "a", "b")

@admin.register(ScoreHistory)
class ScoreHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "drill", "round_index", "score", "total_after_round", "created_at")
    list_filter = ("drill", "created_at")
    search_fields = ("user__username",)
    
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "email", "created_at")
    search_fields = ("user__username", "email", "message")
    list_filter = ("created_at",)
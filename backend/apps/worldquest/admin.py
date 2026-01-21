from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
	AttemptAnswer,
	Category,
	Country,
	CountryEdge,
	Fact,
	FriendRequest,
	Friendship,
	Progress,
	Question,
	QuizAttempt,
	UserStats,
)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
	list_display = ("name",)
	search_fields = ("name",)


@admin.register(Country)
class CountryAdmin(ModelAdmin):
	list_display = ("iso2", "name", "region", "order_index")
	search_fields = ("iso2", "name", "region")
	list_filter = ("region",)
	ordering = ("order_index", "name")


@admin.register(CountryEdge)
class CountryEdgeAdmin(ModelAdmin):
	list_display = ("from_country", "to_country")
	search_fields = ("from_country__name", "to_country__name", "from_country__iso2", "to_country__iso2")


@admin.register(Fact)
class FactAdmin(ModelAdmin):
	list_display = ("country", "category", "title", "created_at")
	search_fields = ("country__name", "country__iso2", "title", "content")
	list_filter = ("category",)


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
	list_display = ("country", "category", "difficulty", "source", "created_at")
	search_fields = ("country__name", "country__iso2", "prompt")
	list_filter = ("category", "difficulty", "source")


@admin.register(UserStats)
class UserStatsAdmin(ModelAdmin):
	list_display = ("user", "xp", "total_correct", "total_answered", "streak_days")
	search_fields = ("user__username", "user__email")


@admin.register(Progress)
class ProgressAdmin(ModelAdmin):
	list_display = ("user", "country", "status", "unlocked_at", "completed_at")
	search_fields = ("user__username", "country__name", "country__iso2")
	list_filter = ("status",)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(ModelAdmin):
	list_display = ("user", "country", "category", "total_questions", "correct_count", "score", "completed_at")
	search_fields = ("user__username", "country__name", "country__iso2")
	list_filter = ("category",)


@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(ModelAdmin):
	list_display = ("attempt", "question", "selected_index", "is_correct")
	list_filter = ("is_correct",)


@admin.register(FriendRequest)
class FriendRequestAdmin(ModelAdmin):
	list_display = ("from_user", "to_user", "status", "responded_at", "created_at")
	search_fields = ("from_user__username", "to_user__username", "from_user__email", "to_user__email")
	list_filter = ("status",)


@admin.register(Friendship)
class FriendshipAdmin(ModelAdmin):
	list_display = ("user", "friend", "created_at")
	search_fields = ("user__username", "friend__username", "user__email", "friend__email")

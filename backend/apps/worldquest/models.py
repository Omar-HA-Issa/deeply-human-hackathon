from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.utils import timezone


User = settings.AUTH_USER_MODEL


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(models.Model):
    """
    Physical / Mental / Economic / Environmental
    """
    class Names(models.TextChoices):
        PHYSICAL = "physical", "Physical"
        MENTAL = "mental", "Mental"
        ECONOMIC = "economic", "Economic"
        ENVIRONMENTAL = "environmental", "Environmental"

    name = models.CharField(max_length=32, choices=Names.choices, unique=True)

    def __str__(self):
        return self.get_name_display()


class Country(models.Model):
    """
    Store only what's needed for map + ordering/unlock.
    """
    iso2 = models.CharField(max_length=2, unique=True)  # e.g., "ES"
    name = models.CharField(max_length=128)
    region = models.CharField(max_length=64, blank=True)

    # Map display helpers (optional; you can also derive from GeoJSON on FE)
    lat = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    lng = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)

    # Roadmap unlock option A: linear path
    order_index = models.PositiveIntegerField(null=True, blank=True, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.iso2})"

    class Meta:
        verbose_name_plural = "Countries"


class CountryEdge(models.Model):
    """
    Roadmap unlock option B: graph.
    If you want *only* linear order, you can skip this model.
    """
    from_country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="edges_out")
    to_country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="edges_in")

    class Meta:
        constraints = [
            UniqueConstraint(fields=["from_country", "to_country"], name="uniq_country_edge"),
            models.CheckConstraint(condition=~Q(from_country=models.F("to_country")), name="no_self_edge"),
        ]

    def __str__(self):
        return f"{self.from_country.iso2} -> {self.to_country.iso2}"


class Fact(TimeStampedModel):
    """
    Optional: store provided dataset “facts” per country/category.
    Helpful for AI generation + deterministic fallback questions.
    """
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="facts")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="facts")
    title = models.CharField(max_length=200, blank=True)
    content = models.TextField()

    class Meta:
        indexes = [models.Index(fields=["country", "category"])]

    def __str__(self):
        return f"{self.country.iso2} - {self.category.name}"


class Question(TimeStampedModel):
    class Difficulty(models.IntegerChoices):
        EASY = 1, "Easy"
        MEDIUM = 2, "Medium"
        HARD = 3, "Hard"

    class Source(models.TextChoices):
        DATASET = "dataset", "Dataset"
        AI = "ai", "AI"
        MANUAL = "manual", "Manual"

    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="questions")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="questions")

    prompt = models.TextField()
    choices = models.JSONField(default=list)  # ["A", "B", "C", "D"]
    correct_index = models.PositiveSmallIntegerField()  # 0..len(choices)-1

    difficulty = models.PositiveSmallIntegerField(choices=Difficulty.choices, default=Difficulty.EASY)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.DATASET)

    # Optional metadata
    explanation = models.TextField(blank=True)
    fact = models.ForeignKey(Fact, null=True, blank=True, on_delete=models.SET_NULL, related_name="questions")

    class Meta:
        indexes = [
            models.Index(fields=["country", "category", "difficulty"]),
        ]

    def __str__(self):
        return f"Q({self.country.iso2}/{self.category.name})"


class UserStats(TimeStampedModel):
    """
    Leaderboard can be computed live, but storing totals makes hackathon queries fast.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="stats")
    xp = models.PositiveIntegerField(default=0)
    total_correct = models.PositiveIntegerField(default=0)
    total_answered = models.PositiveIntegerField(default=0)
    streak_days = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Stats({self.user_id})"

    class Meta:
        verbose_name_plural = "User stats"


class Progress(models.Model):
    class Status(models.TextChoices):
        LOCKED = "locked", "Locked"
        AVAILABLE = "available", "Available"
        COMPLETED = "completed", "Completed"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="progress")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="progress")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.LOCKED)

    unlocked_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["user", "country"], name="uniq_user_country_progress"),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["country", "status"]),
        ]
        verbose_name_plural = "Progress"

    def __str__(self):
        return f"{self.user_id}:{self.country.iso2}:{self.status}"


class QuizAttempt(TimeStampedModel):
    """
    One attempt = one quiz run for a country (optionally category-specific).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_attempts")
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="quiz_attempts")
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name="quiz_attempts")

    total_questions = models.PositiveSmallIntegerField(default=5)
    correct_count = models.PositiveSmallIntegerField(default=0)

    score = models.IntegerField(default=0)  # points/xp gained for the attempt
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["country", "created_at"]),
        ]

    def __str__(self):
        return f"Attempt({self.user_id}, {self.country.iso2})"


class AttemptAnswer(models.Model):
    """
    Store exactly what the user chose for each question.
    """
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="attempt_answers")
    selected_index = models.PositiveSmallIntegerField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["attempt", "question"], name="uniq_attempt_question"),
        ]


class FriendRequest(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friend_requests_sent")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friend_requests_received")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)

    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["from_user", "to_user"], name="uniq_friend_request_pair"),
            models.CheckConstraint(condition=~Q(from_user=models.F("to_user")), name="no_self_friend_request"),
        ]
        indexes = [
            models.Index(fields=["to_user", "status"]),
            models.Index(fields=["from_user", "status"]),
        ]

    def __str__(self):
        return f"FR({self.from_user_id}->{self.to_user_id}:{self.status})"


class Friendship(models.Model):
    """
    Simple symmetrical friendship table (created when request accepted).
    Store two directed rows for fast queries: (A->B) and (B->A).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friends")
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friends_of")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            UniqueConstraint(fields=["user", "friend"], name="uniq_friendship"),
            models.CheckConstraint(condition=~Q(user=models.F("friend")), name="no_self_friendship"),
        ]
        indexes = [
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user_id} -> {self.friend_id}"

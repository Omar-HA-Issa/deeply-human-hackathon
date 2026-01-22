import json
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import (
	Country,
	Question,
	QuizAttempt,
	AttemptAnswer,
	UserStats,
	Progress,
	FriendRequest,
	Friendship,
)
from .services import get_question_generator


User = get_user_model()

_dataset_country_names: set[str] | None = None


def _json_error(message: str, status: int = 400):
	return JsonResponse({"ok": False, "error": message}, status=status)


def _parse_json(request):
	if not request.body:
		return {}
	try:
		return json.loads(request.body.decode("utf-8"))
	except (json.JSONDecodeError, UnicodeDecodeError):
		return None


def _require_authenticated(request):
	if not request.user.is_authenticated:
		return _json_error("Not authenticated.", status=401)
	return None


def _get_dataset_country_names() -> set[str]:
	global _dataset_country_names
	if _dataset_country_names is not None:
		return _dataset_country_names
	try:
		dataset_path = Path(settings.DATASET_PATH)
		with dataset_path.open("r", encoding="utf-8") as file:
			data = json.load(file)
		_dataset_country_names = set(data.keys())
	except Exception:
		_dataset_country_names = set()
	return _dataset_country_names


@csrf_exempt
@require_POST
def register(request):
	payload = _parse_json(request)
	if payload is None:
		return _json_error("Invalid JSON payload.")

	username = (payload.get("username") or "").strip()
	email = (payload.get("email") or "").strip()
	password = payload.get("password") or ""

	if not username or not password:
		return _json_error("Username and password are required.")

	if User.objects.filter(username=username).exists():
		return _json_error("Username already taken.")

	user = User.objects.create_user(username=username, email=email, password=password)
	login(request, user)

	return JsonResponse({
		"ok": True,
		"user": {
			"id": user.id,
			"username": user.username,
			"email": user.email,
		},
	})


@csrf_exempt
@require_POST
def login_view(request):
	payload = _parse_json(request)
	if payload is None:
		return _json_error("Invalid JSON payload.")

	username = (payload.get("username") or "").strip()
	password = payload.get("password") or ""

	if not username or not password:
		return _json_error("Username and password are required.")

	user = authenticate(request, username=username, password=password)
	if user is None:
		return _json_error("Invalid credentials.", status=401)

	login(request, user)
	return JsonResponse({
		"ok": True,
		"user": {
			"id": user.id,
			"username": user.username,
			"email": user.email,
		},
	})


@require_GET
def me(request):
	if not request.user.is_authenticated:
		return _json_error("Not authenticated.", status=401)

	user = request.user
	return JsonResponse({
		"ok": True,
		"user": {
			"id": user.id,
			"username": user.username,
			"email": user.email,
		},
	})


@csrf_exempt
@require_POST
def logout_view(request):
	logout(request)
	return JsonResponse({"ok": True})


# ─────────────────────────────────────────────────────────────
# Quiz Endpoints
# ─────────────────────────────────────────────────────────────

@csrf_exempt
@require_GET
def get_quiz(request, country_code):
	"""
	GET /api/quiz/{country_code}/
	Returns questions for a country (cached or generated on-demand).
	"""
	# Get or generate questions
	generator = get_question_generator()
	questions, error = generator.get_questions_for_country(country_code)

	if error:
		return _json_error(error, status=404)

	if not questions:
		return _json_error("No questions available for this country", status=404)

	# Get country name
	try:
		country = Country.objects.get(iso2=country_code.upper())
		country_name = country.name
	except Country.DoesNotExist:
		country_name = country_code

	# Format response
	response_questions = []
	for q in questions:
		fallback_fact = q.surprising_fact or q.did_you_know or q.explanation
		response_questions.append({
			"id": q.id,
			"prompt": q.prompt,
			"choices": q.choices,
			"correct_index": q.correct_index,
			"difficulty": q.difficulty,
			"category": q.category.get_name_display() if q.category else "General",
			"did_you_know": q.did_you_know or fallback_fact,
			"surprising_fact": q.surprising_fact or fallback_fact,
			"insight": q.insight,
		})

	return JsonResponse({
		"ok": True,
		"country": country_name,
		"country_code": country_code.upper(),
		"questions": response_questions,
	})


@csrf_exempt
@require_POST
def submit_quiz(request, country_code):
	"""
	POST /api/quiz/{country_code}/submit/
	Submit answers and get results.

	Body: { "answers": [{ "question_id": 1, "selected_index": 2 }, ...] }
	"""
	payload = _parse_json(request)
	if payload is None:
		return _json_error("Invalid JSON payload.")

	answers = payload.get("answers", [])
	if not answers:
		return _json_error("No answers provided.")

	# Get country
	try:
		country = Country.objects.get(iso2=country_code.upper())
	except Country.DoesNotExist:
		return _json_error(f"Country not found: {country_code}", status=404)

	# Process answers
	results = []
	correct_count = 0
	question_ids = [a.get("question_id") for a in answers]

	# Fetch all questions at once
	questions_map = {
		q.id: q for q in Question.objects.filter(id__in=question_ids)
	}

	for answer in answers:
		question_id = answer.get("question_id")
		selected_index = answer.get("selected_index")

		if question_id is None or selected_index is None:
			continue

		question = questions_map.get(question_id)
		if not question:
			results.append({
				"question_id": question_id,
				"correct": False,
				"error": "Question not found",
			})
			continue

		is_correct = (selected_index == question.correct_index)
		if is_correct:
			correct_count += 1

		results.append({
			"question_id": question_id,
			"correct": is_correct,
			"correct_index": question.correct_index,
			"explanation": question.explanation,
			"surprising_fact": question.surprising_fact,
			"insight": question.insight,
		})

	total = len(results)
	score = correct_count * 10  # 10 points per correct answer

	# Save attempt if user is authenticated
	if request.user.is_authenticated:
		attempt = QuizAttempt.objects.create(
			user=request.user,
			country=country,
			total_questions=total,
			correct_count=correct_count,
			score=score,
			completed_at=timezone.now(),
		)

		# Save individual answers
		for answer, result in zip(answers, results):
			question_id = answer.get("question_id")
			selected_index = answer.get("selected_index")
			question = questions_map.get(question_id)

			if question and selected_index is not None:
				AttemptAnswer.objects.create(
					attempt=attempt,
					question=question,
					selected_index=selected_index,
					is_correct=result.get("correct", False),
				)

		# Update user stats
		stats, _ = UserStats.objects.get_or_create(user=request.user)
		stats.total_answered += total
		stats.total_correct += correct_count
		stats.xp += score
		stats.save()

		# Update progress if user completed quiz successfully
		if correct_count >= (total * 0.6):  # 60% threshold
			progress, created = Progress.objects.get_or_create(
				user=request.user,
				country=country,
				defaults={"status": Progress.Status.COMPLETED}
			)
			if not created and progress.status != Progress.Status.COMPLETED:
				progress.status = Progress.Status.COMPLETED
				progress.completed_at = timezone.now()
				progress.save()

	return JsonResponse({
		"ok": True,
		"score": score,
		"total": total,
		"correct_count": correct_count,
		"results": results,
	})


@require_GET
def list_countries(request):
	"""
	GET /api/countries/
	List all countries available for quizzes.
	Optional: ?search=japan to filter by name
	"""
	countries = Country.objects.all()

	# Optional search filter
	search = request.GET.get("search", "").strip()
	if search:
		countries = countries.filter(name__icontains=search)

	countries = countries.order_by("order_index", "name")

	country_list = []
	for c in countries:
		country_list.append({
			"iso2": c.iso2,
			"name": c.name,
			"region": c.region,
			"lat": float(c.lat) if c.lat else None,
			"lng": float(c.lng) if c.lng else None,
		})

	return JsonResponse({
		"ok": True,
		"countries": country_list,
		"count": len(country_list),
	})


@require_GET
def list_available_countries(request):
	"""
	GET /api/countries/available/
	List countries that have dataset-backed quiz data.
	"""
	available_names = _get_dataset_country_names()
	if not available_names:
		return JsonResponse({"ok": True, "countries": [], "count": 0})

	qs = Country.objects.filter(name__in=available_names).order_by("name")
	return JsonResponse({
		"ok": True,
		"countries": [country.iso2 for country in qs],
		"count": qs.count(),
	})


# ─────────────────────────────────────────────────────────────
# Stats + Leaderboard Endpoints
# ─────────────────────────────────────────────────────────────

@require_GET
def user_stats(request):
	"""
	GET /api/stats/
	Return stats for the authenticated user.
	"""
	auth_error = _require_authenticated(request)
	if auth_error:
		return auth_error

	stats, _ = UserStats.objects.get_or_create(user=request.user)
	total_answered = stats.total_answered
	accuracy = (stats.total_correct / total_answered) if total_answered else 0
	completed_count = Progress.objects.filter(
		user=request.user,
		status=Progress.Status.COMPLETED,
	).count()
	attempts_count = QuizAttempt.objects.filter(user=request.user).count()

	return JsonResponse({
		"ok": True,
		"stats": {
			"xp": stats.xp,
			"total_correct": stats.total_correct,
			"total_answered": total_answered,
			"accuracy": accuracy,
			"streak_days": stats.streak_days,
			"countries_completed": completed_count,
			"total_attempts": attempts_count,
		},
	})


@require_GET
def leaderboard(request):
	"""
	GET /api/leaderboard/?limit=20
	Return top users by XP.
	"""
	limit_raw = request.GET.get("limit", "20")
	try:
		limit = int(limit_raw)
	except (TypeError, ValueError):
		limit = 20
	limit = max(1, min(limit, 100))

	stats_qs = UserStats.objects.select_related("user").order_by(
		"-xp",
		"-total_correct",
		"-total_answered",
		"user__username",
	)[:limit]

	entries = []
	for index, stats in enumerate(stats_qs, start=1):
		total_answered = stats.total_answered
		accuracy = (stats.total_correct / total_answered) if total_answered else 0
		entries.append({
			"rank": index,
			"user": {
				"id": stats.user_id,
				"username": stats.user.username,
			},
			"xp": stats.xp,
			"total_correct": stats.total_correct,
			"total_answered": total_answered,
			"accuracy": accuracy,
			"streak_days": stats.streak_days,
			"is_me": request.user.is_authenticated and stats.user_id == request.user.id,
		})

	return JsonResponse({
		"ok": True,
		"leaderboard": entries,
		"count": len(entries),
	})


# ─────────────────────────────────────────────────────────────
# Social Endpoints
# ─────────────────────────────────────────────────────────────

@require_GET
def list_friends(request):
	"""
	GET /api/friends/
	List all friends for the authenticated user.
	"""
	auth_error = _require_authenticated(request)
	if auth_error:
		return auth_error

	friendships = Friendship.objects.filter(user=request.user).select_related(
		"friend",
		"friend__stats",
	).order_by("friend__username")

	friends = []
	for relation in friendships:
		friend = relation.friend
		stats = getattr(friend, "stats", None)
		total_answered = stats.total_answered if stats else 0
		accuracy = (stats.total_correct / total_answered) if stats and total_answered else 0
		friends.append({
			"id": friend.id,
			"username": friend.username,
			"xp": stats.xp if stats else 0,
			"accuracy": accuracy,
			"streak_days": stats.streak_days if stats else 0,
		})

	return JsonResponse({
		"ok": True,
		"friends": friends,
		"count": len(friends),
	})


@require_GET
def list_friend_requests(request):
	"""
	GET /api/friends/requests/
	List pending friend requests (incoming/outgoing).
	"""
	auth_error = _require_authenticated(request)
	if auth_error:
		return auth_error

	incoming_qs = FriendRequest.objects.filter(
		to_user=request.user,
		status=FriendRequest.Status.PENDING,
	).select_related("from_user").order_by("-created_at")

	outgoing_qs = FriendRequest.objects.filter(
		from_user=request.user,
		status=FriendRequest.Status.PENDING,
	).select_related("to_user").order_by("-created_at")

	incoming = [{
		"id": fr.id,
		"from_user": {
			"id": fr.from_user_id,
			"username": fr.from_user.username,
		},
		"created_at": fr.created_at.isoformat(),
	} for fr in incoming_qs]

	outgoing = [{
		"id": fr.id,
		"to_user": {
			"id": fr.to_user_id,
			"username": fr.to_user.username,
		},
		"created_at": fr.created_at.isoformat(),
	} for fr in outgoing_qs]

	return JsonResponse({
		"ok": True,
		"incoming": incoming,
		"outgoing": outgoing,
	})


@csrf_exempt
@require_POST
def send_friend_request(request):
	"""
	POST /api/friends/requests/
	Body: { "username": "alice" } or { "user_id": 123 }
	"""
	auth_error = _require_authenticated(request)
	if auth_error:
		return auth_error

	payload = _parse_json(request)
	if payload is None:
		return _json_error("Invalid JSON payload.")

	username = (payload.get("username") or "").strip()
	user_id = payload.get("user_id")

	target = None
	if user_id is not None:
		target = User.objects.filter(id=user_id).first()
	elif username:
		target = User.objects.filter(username__iexact=username).first()

	if not target:
		return _json_error("User not found.", status=404)

	if target.id == request.user.id:
		return _json_error("You cannot add yourself.")

	if Friendship.objects.filter(user=request.user, friend=target).exists():
		return _json_error("You are already friends.")

	existing = FriendRequest.objects.filter(
		from_user=request.user,
		to_user=target,
	).first()
	if existing:
		if existing.status == FriendRequest.Status.PENDING:
			return _json_error("Friend request already sent.")
		existing.status = FriendRequest.Status.PENDING
		existing.responded_at = None
		existing.save(update_fields=["status", "responded_at"])
		return JsonResponse({"ok": True, "request_id": existing.id})

	reverse_request = FriendRequest.objects.filter(
		from_user=target,
		to_user=request.user,
		status=FriendRequest.Status.PENDING,
	).first()
	if reverse_request:
		reverse_request.status = FriendRequest.Status.ACCEPTED
		reverse_request.responded_at = timezone.now()
		reverse_request.save(update_fields=["status", "responded_at"])
		Friendship.objects.get_or_create(user=request.user, friend=target)
		Friendship.objects.get_or_create(user=target, friend=request.user)
		return JsonResponse({
			"ok": True,
			"friends": True,
			"request_id": reverse_request.id,
		})

	friend_request = FriendRequest.objects.create(
		from_user=request.user,
		to_user=target,
		status=FriendRequest.Status.PENDING,
	)
	return JsonResponse({"ok": True, "request_id": friend_request.id})


@csrf_exempt
@require_POST
def accept_friend_request(request, request_id):
	"""
	POST /api/friends/requests/<id>/accept/
	"""
	auth_error = _require_authenticated(request)
	if auth_error:
		return auth_error

	friend_request = FriendRequest.objects.filter(
		id=request_id,
		to_user=request.user,
		status=FriendRequest.Status.PENDING,
	).select_related("from_user").first()
	if not friend_request:
		return _json_error("Friend request not found.", status=404)

	friend_request.status = FriendRequest.Status.ACCEPTED
	friend_request.responded_at = timezone.now()
	friend_request.save(update_fields=["status", "responded_at"])

	Friendship.objects.get_or_create(user=request.user, friend=friend_request.from_user)
	Friendship.objects.get_or_create(user=friend_request.from_user, friend=request.user)

	return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def decline_friend_request(request, request_id):
	"""
	POST /api/friends/requests/<id>/decline/
	"""
	auth_error = _require_authenticated(request)
	if auth_error:
		return auth_error

	friend_request = FriendRequest.objects.filter(
		id=request_id,
		to_user=request.user,
		status=FriendRequest.Status.PENDING,
	).first()
	if not friend_request:
		return _json_error("Friend request not found.", status=404)

	friend_request.status = FriendRequest.Status.DECLINED
	friend_request.responded_at = timezone.now()
	friend_request.save(update_fields=["status", "responded_at"])
	return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def cancel_friend_request(request, request_id):
	"""
	POST /api/friends/requests/<id>/cancel/
	"""
	auth_error = _require_authenticated(request)
	if auth_error:
		return auth_error

	friend_request = FriendRequest.objects.filter(
		id=request_id,
		from_user=request.user,
		status=FriendRequest.Status.PENDING,
	).first()
	if not friend_request:
		return _json_error("Friend request not found.", status=404)

	friend_request.delete()
	return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
def remove_friend(request, user_id):
	"""
	POST /api/friends/<user_id>/remove/
	"""
	auth_error = _require_authenticated(request)
	if auth_error:
		return auth_error

	if user_id == request.user.id:
		return _json_error("You cannot remove yourself.")

	deleted_count, _ = Friendship.objects.filter(
		user=request.user,
		friend_id=user_id,
	).delete()
	deleted_count += Friendship.objects.filter(
		user_id=user_id,
		friend=request.user,
	).delete()[0]

	if deleted_count == 0:
		return _json_error("Friend not found.", status=404)

	return JsonResponse({"ok": True})

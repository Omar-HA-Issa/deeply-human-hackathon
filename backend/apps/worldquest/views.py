import json

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Country, Question, QuizAttempt, AttemptAnswer, UserStats, Progress
from .services import get_question_generator


User = get_user_model()


def _json_error(message: str, status: int = 400):
	return JsonResponse({"ok": False, "error": message}, status=status)


def _parse_json(request):
	if not request.body:
		return {}
	try:
		return json.loads(request.body.decode("utf-8"))
	except (json.JSONDecodeError, UnicodeDecodeError):
		return None


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
	questions, fun_fact, error = generator.get_questions_for_country(country_code)

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
		response_questions.append({
			"id": q.id,
			"prompt": q.prompt,
			"choices": q.choices,
			"difficulty": q.difficulty,
			"category": q.category.get_name_display() if q.category else "General",
		})

	return JsonResponse({
		"ok": True,
		"country": country_name,
		"country_code": country_code.upper(),
		"questions": response_questions,
		"fun_fact": fun_fact,
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
	"""
	countries = Country.objects.all().order_by("order_index", "name")

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

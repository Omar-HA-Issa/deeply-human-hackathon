import json

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Country, CountryEdge, Progress

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


@csrf_exempt
@require_POST
def complete_quiz(request):
	if not request.user.is_authenticated:
		return _json_error("Not authenticated.", status=401)

	payload = _parse_json(request)
	if payload is None:
		return _json_error("Invalid JSON payload.")

	country_code = (payload.get("country") or "").strip().upper()
	if not country_code:
		return _json_error("Country code is required.")

	try:
		country = Country.objects.get(iso2=country_code)
	except Country.DoesNotExist:
		return _json_error("Country not found.", status=404)

	with transaction.atomic():
		progress, created = Progress.objects.select_for_update().get_or_create(
			user=request.user,
			country=country,
			defaults={
				"status": Progress.Status.AVAILABLE,
				"unlocked_at": timezone.now(),
			},
		)

		if progress.status == Progress.Status.LOCKED:
			return _json_error("Country is locked.", status=403)

		progress.status = Progress.Status.COMPLETED
		progress.completed_at = timezone.now()
		if not progress.unlocked_at:
			progress.unlocked_at = timezone.now()
		progress.save(update_fields=["status", "completed_at", "unlocked_at"])

		neighbor_ids = set(
			CountryEdge.objects.filter(from_country=country).values_list("to_country_id", flat=True)
		) | set(
			CountryEdge.objects.filter(to_country=country).values_list("from_country_id", flat=True)
		)

		unlocked_codes = []
		if neighbor_ids:
			neighbors = Country.objects.filter(id__in=neighbor_ids)
			for neighbor in neighbors:
				neighbor_progress, _ = Progress.objects.get_or_create(
					user=request.user,
					country=neighbor,
					defaults={
						"status": Progress.Status.AVAILABLE,
						"unlocked_at": timezone.now(),
					},
				)
				if neighbor_progress.status == Progress.Status.LOCKED:
					neighbor_progress.status = Progress.Status.AVAILABLE
					neighbor_progress.unlocked_at = neighbor_progress.unlocked_at or timezone.now()
					neighbor_progress.save(update_fields=["status", "unlocked_at"])
					unlocked_codes.append(neighbor.iso2)

	return JsonResponse({
		"ok": True,
		"completed": country.iso2,
		"unlocked": unlocked_codes,
	})


import json

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST


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

# Create your views here.

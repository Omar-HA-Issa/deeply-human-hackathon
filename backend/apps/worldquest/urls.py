from django.urls import path

from . import views

urlpatterns = [
    # Auth endpoints
    path("auth/register", views.register, name="auth-register"),
    path("auth/login", views.login_view, name="auth-login"),
    path("auth/logout", views.logout_view, name="auth-logout"),
    path("auth/me", views.me, name="auth-me"),

    # Quiz endpoints
    path("quiz/<str:country_code>/", views.get_quiz, name="quiz-get"),
    path("quiz/<str:country_code>/submit/", views.submit_quiz, name="quiz-submit"),

    # Country listing
    path("countries/", views.list_countries, name="countries-list"),
]

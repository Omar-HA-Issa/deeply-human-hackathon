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
    path("countries/available/", views.list_available_countries, name="countries-available"),

    # Progress
    path("progress/", views.list_progress, name="progress-list"),

    # Stats + leaderboard
    path("stats/", views.user_stats, name="user-stats"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),

    # Social
    path("friends/", views.list_friends, name="friends-list"),
    path("friends/requests/", views.list_friend_requests, name="friend-requests-list"),
    path("friends/requests/send/", views.send_friend_request, name="friend-request-send"),
    path("friends/requests/<int:request_id>/accept/", views.accept_friend_request, name="friend-request-accept"),
    path("friends/requests/<int:request_id>/decline/", views.decline_friend_request, name="friend-request-decline"),
    path("friends/requests/<int:request_id>/cancel/", views.cancel_friend_request, name="friend-request-cancel"),
    path("friends/<int:user_id>/remove/", views.remove_friend, name="friend-remove"),
]

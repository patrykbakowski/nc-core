from django.urls import path
from .views import AccessContextView, LoginView, LogoutView, MeView

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("access-context/", AccessContextView.as_view(), name="access-context"),
]

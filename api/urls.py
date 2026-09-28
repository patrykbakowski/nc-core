from django.urls import path
from .views import (
    AccessContextView,
    InvitationProvisionView,
    LoginView,
    LogoutView,
    MeView,
    ServiceAccessContextView,
)

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("access-context/", AccessContextView.as_view(), name="access-context"),
    path(
        "service/access-context/",
        ServiceAccessContextView.as_view(),
        name="service-access-context",
    ),
    path(
        "accounts/invitations/",
        InvitationProvisionView.as_view(),
        name="account-invitations",
    ),
]

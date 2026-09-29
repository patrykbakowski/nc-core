from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from api.views import HealthView
from users.forms import QMPasswordResetForm
from users.views import QMLoginView, QMPasswordResetView, accept_invitation, invitation_complete

urlpatterns = [
    path("healthz/", HealthView.as_view(), name="healthz"),
    path("admin/", admin.site.urls),
    path(
        "accounts/login/",
        QMLoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "accounts/password-reset/",
        QMPasswordResetView.as_view(
            form_class=QMPasswordResetForm,
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.txt",
            subject_template_name="registration/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "accounts/password-reset/sent/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path(
        "accounts/invite/<uidb64>/<token>/",
        accept_invitation,
        name="accept-invitation",
    ),
    path(
        "accounts/invite/complete/",
        invitation_complete,
        name="invitation-complete",
    ),
    path("o/", include("oauth2_provider.urls")),
    path("api/v1/", include("api.urls")),
]

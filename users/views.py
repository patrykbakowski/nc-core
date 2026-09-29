from django.conf import settings
from django.contrib.auth import get_user_model, views as auth_views
from django.contrib.auth.forms import SetPasswordForm
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .invitations import invitation_tokens
from .security import consume_auth_attempt

User = get_user_model()


@never_cache
@require_http_methods(["GET", "POST"])
def accept_invitation(request, uidb64, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=user_id)
    except (ValueError, TypeError, OverflowError, User.DoesNotExist):
        raise Http404

    valid = (
        user.status == User.Status.ACTIVE
        and not user.is_active
        and invitation_tokens.check_token(user, token)
    )

    form = SetPasswordForm(user, request.POST or None) if valid else None
    if request.method == "POST" and valid and form.is_valid():
        form.save()
        user.is_active = True
        user.save(update_fields=["is_active"])
        return redirect("invitation-complete")

    return render(
        request,
        "registration/invitation_accept.html",
        {"form": form, "validlink": valid},
        status=200 if valid else 400,
    )


def invitation_complete(request):
    return render(
        request,
        "registration/invitation_complete.html",
        {"login_url": settings.LOGIN_URL},
    )



def _rate_limited_response(retry_after):
    response = HttpResponse(
        "Too many requests. Try again later.",
        status=429,
        content_type="text/plain; charset=utf-8",
    )
    response["Retry-After"] = str(retry_after)
    return response


class QMLoginView(auth_views.LoginView):
    def post(self, request, *args, **kwargs):
        identifier = (
            request.POST.get("username")
            or request.POST.get("email")
            or ""
        )
        result = consume_auth_attempt(
            request,
            "login",
            identifier,
            limit=settings.QM_LOGIN_RATE_LIMIT,
            window_seconds=settings.QM_LOGIN_RATE_WINDOW_SECONDS,
        )
        if not result.allowed:
            return _rate_limited_response(result.retry_after)
        return super().post(request, *args, **kwargs)


class QMPasswordResetView(auth_views.PasswordResetView):
    def post(self, request, *args, **kwargs):
        identifier = request.POST.get("email") or ""
        result = consume_auth_attempt(
            request,
            "password_reset",
            identifier,
            limit=settings.QM_PASSWORD_RESET_RATE_LIMIT,
            window_seconds=settings.QM_PASSWORD_RESET_RATE_WINDOW_SECONDS,
        )
        if not result.allowed:
            return _rate_limited_response(result.retry_after)
        return super().post(request, *args, **kwargs)

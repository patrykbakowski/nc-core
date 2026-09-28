from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.mail import send_mail
from django.db import connection, transaction
from django.shortcuts import get_object_or_404
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from entitlements.models import ProductEntitlement
from organizations.models import Membership, Organization
from users.invitations import invitation_path
from .permissions import (
    HasQMAccessScopeOrSession,
    HasQMProvisionScope,
    HasQMServiceAccessScope,
    IsActiveQMUser,
)
from .serializers import (
    AccessContextQuerySerializer,
    InvitationSerializer,
    LoginSerializer,
    ServiceAccessContextQuerySerializer,
)

User = get_user_model()


def user_payload(user):
    return {
        "id": str(user.pk),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


def _resolve_access_context(user, organization_id, product):
    membership = get_object_or_404(
        Membership.objects.select_related("organization"),
        user=user,
        organization_id=organization_id,
        status=Membership.Status.ACTIVE,
        organization__status=Organization.Status.ACTIVE,
    )

    entitlement = (
        ProductEntitlement.objects
        .filter(organization=membership.organization, product_id=product)
        .first()
    )
    if not entitlement or not entitlement.is_active_at():
        raise PermissionDenied("Organization has no active entitlement for this product.")
    return membership, entitlement


def _access_context_payload(user, membership, entitlement):
    return {
        "user": user_payload(user),
        "organization": {
            "id": str(membership.organization_id),
            "name": membership.organization.name,
            "slug": membership.organization.slug,
        },
        "membership": {
            "id": str(membership.pk),
            "role": membership.role,
        },
        "entitlement": {
            "id": str(entitlement.pk),
            "product": entitlement.product_id,
            "plan": entitlement.plan,
            "valid_from": entitlement.valid_from,
            "valid_until": entitlement.valid_until,
        },
    }


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            return Response({"status": "error"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"status": "ok"})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        password = serializer.validated_data["password"]

        authenticated = authenticate(request, email=email, password=password)
        if not authenticated:
            raise AuthenticationFailed("Invalid credentials.")

        login(request, authenticated)
        return Response({"user": user_payload(authenticated)})


class LogoutView(APIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        memberships = (
            Membership.objects
            .filter(
                user=request.user,
                status=Membership.Status.ACTIVE,
                organization__status=Organization.Status.ACTIVE,
            )
            .select_related("organization")
            .order_by("organization__name")
        )
        return Response(
            {
                "user": user_payload(request.user),
                "memberships": [
                    {
                        "id": str(m.pk),
                        "organization": {
                            "id": str(m.organization_id),
                            "name": m.organization.name,
                            "slug": m.organization.slug,
                        },
                        "role": m.role,
                    }
                    for m in memberships
                ],
            }
        )


class AccessContextView(APIView):
    permission_classes = [IsActiveQMUser, HasQMAccessScopeOrSession]

    def get(self, request):
        serializer = AccessContextQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        membership, entitlement = _resolve_access_context(
            request.user,
            serializer.validated_data["organization_id"],
            serializer.validated_data["product"],
        )
        return Response(_access_context_payload(request.user, membership, entitlement))


class ServiceAccessContextView(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [HasQMServiceAccessScope]

    def get(self, request):
        serializer = ServiceAccessContextQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = get_object_or_404(
            User,
            pk=serializer.validated_data["user_id"],
            is_active=True,
            status=User.Status.ACTIVE,
        )
        membership, entitlement = _resolve_access_context(
            user,
            serializer.validated_data["organization_id"],
            serializer.validated_data["product"],
        )
        return Response(_access_context_payload(user, membership, entitlement))


class InvitationProvisionView(APIView):
    authentication_classes = [OAuth2Authentication]
    permission_classes = [HasQMProvisionScope]

    def post(self, request):
        serializer = InvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = User.objects.normalize_email(
            serializer.validated_data["email"]
        ).strip().lower()

        with transaction.atomic():
            user = User.objects.select_for_update().filter(email=email).first()
            created = user is None

            if user is not None:
                if user.status != User.Status.ACTIVE:
                    return Response(
                        {"detail": "account_unavailable"},
                        status=status.HTTP_409_CONFLICT,
                    )
                if user.is_active:
                    return Response(
                        {
                            "user": user_payload(user),
                            "state": "active",
                            "invitation_sent": False,
                        }
                    )
                user.set_unusable_password()
                user.save(update_fields=["password"])
            else:
                user = User.objects.create_user(
                    email=email,
                    password=None,
                    is_active=False,
                    status=User.Status.ACTIVE,
                )

            activation_url = settings.QM_ACCOUNT_PUBLIC_ORIGIN + invitation_path(user)
            send_mail(
                "Aktywacja konta QM Identity",
                (
                    "Utworzono lub ponowiono zaproszenie do wspólnego konta "
                    "QManufacture. Ustaw hasło korzystając z linku:\n\n"
                    + activation_url
                    + "\n\nLink jest jednorazowy i wygasa po 24 godzinach."
                ),
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )

        return Response(
            {
                "user": user_payload(user),
                "state": "pending",
                "invitation_sent": True,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

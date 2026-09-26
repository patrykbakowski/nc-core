from django.contrib.auth import authenticate, get_user_model, login, logout
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from entitlements.models import ProductEntitlement
from organizations.models import Membership, Organization
from .serializers import AccessContextQuerySerializer, LoginSerializer

User = get_user_model()


def user_payload(user):
    return {
        "id": str(user.pk),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        password = serializer.validated_data["password"]

        authenticated = authenticate(request, email=email, password=password)
        if not authenticated or not authenticated.is_active or authenticated.status != User.Status.ACTIVE:
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
    def get(self, request):
        serializer = AccessContextQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        organization_id = serializer.validated_data["organization_id"]
        product = serializer.validated_data["product"]

        membership = get_object_or_404(
            Membership.objects.select_related("organization"),
            user=request.user,
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

        return Response(
            {
                "user": user_payload(request.user),
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
        )

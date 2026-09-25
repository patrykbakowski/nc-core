# QM Core / QM Identity — Project State

**Updated:** 2026-09-25  
**Repository:** `patrykbakowski/nc-core` (legacy repository name)  
**Status:** ACTIVE / Stage 1 identity-access implementation started

## Purpose

Provide shared identity/access capabilities owned by QManufacture and usable by independent products plus Neuroconnect NC Platform.

## Naming decision

- **QManufacture** owns the shared technical foundation.
- **QM Core** is that shared foundation.
- **QM Identity** is the identity/authentication module inside QM Core.
- **NC Platform** means only the Neuroconnect training application.
- **NC Core** and **NC ID** are deprecated names. The repository name `nc-core` remains unchanged for continuity.

## First real consumer

**Zgodomat** is the first real consumer. The minimal contract is documented in `docs/API.md`.

The first slice intentionally exposes only:
- email/password session authentication;
- current user and active organization memberships;
- coarse organization role;
- product entitlement lookup for a requested organization/product.

Zgodomat still owns documents, versions, requests, acceptance evidence, product audit trail and fine-grained authorization.

## Implemented in Stage 1 slice

- Django project package `qm_core`;
- custom Django User from the first migration;
- Organization and Membership with fail-closed coarse roles;
- ProductEntitlement with status and validity window;
- `POST /api/v1/auth/login/`;
- `POST /api/v1/auth/logout/`;
- `GET /api/v1/auth/me/`;
- `GET /api/v1/access-context/`;
- tenant-isolation and entitlement tests;
- PostgreSQL GitHub Actions CI;
- no Google Cloud, social login, billing or product-domain models.

## Boundaries preserved

- Fine-grained product authorization stays in each product.
- Product-specific audit trails stay in each product.
- Course, CourseSession, Enrollment and Material remain outside QM Core.
- Account linking must use a verified flow, never email-match-only.
- Cross-domain SSO/service auth is deferred. The current Django session contract is a first staging slice, not the final multi-domain identity design.

## Next steps

1. Get the Stage 1 branch through CI and merge after review.
2. Integrate the existing Zgodomat pilot against the minimal access-context contract without moving Zgodomat domain data into QM Core.
3. Add the smallest missing account lifecycle pieces required by that integration, likely password reset/invitation before public pilot use.
4. Add service authentication/OIDC only when separate product deployment makes it necessary.
5. Keep VerifyTest and Booking queued until their real use cases justify implementation.

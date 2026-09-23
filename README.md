# NC Core

Shared identity and access foundation (NC ID) for independent Neuroconnect/QManufacture applications.

## Goal

Provide a small stable identity/access core without becoming a catch-all business backend.

## Stack

- Django
- PostgreSQL
- REST
- one deployable modular application
- no microservices for MVP
- no Google Cloud dependency

Use Django's mature authentication/session machinery. Do not implement password hashing, token crypto or OAuth/OIDC protocols from scratch.

## Owned by NC Core

- custom Django User from the first migration,
- organizations,
- memberships,
- coarse roles/permissions,
- product entitlements,
- authentication / later service auth,
- audit identity/correlation.

## Owned by products

- consent/document acceptance -> Zgodomat,
- tests/sessions/answers/scoring -> VerifyTest,
- appointments/availability -> Booking,
- invoices/payments -> billing,
- Course/Enrollment/Material and BUR training workflow -> Neuroconnect / NC Platform.

Fine-grained product authorization and product-specific audit trails stay in the product.

## Architecture

The reviewed architecture is in `docs/ARCHITECTURE.md`.

Independent products can work alone while using NC Core for shared identity and access. Social login/SSO is prepared for later but not implemented now.

See `PROJECT_STATE.md` for current status.

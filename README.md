# QM Core / QM Identity

Shared identity and access foundation owned by the QManufacture product family.

> Repository note: the repository is still named `patrykbakowski/nc-core` for continuity. `NC Core` and `NC ID` are deprecated architecture names. The current names are **QM Core** and **QM Identity**.

## Goal

Provide a small stable identity/access core for independent QManufacture products and external clients such as Neuroconnect, without becoming a catch-all business backend.

## Stack

- Django
- PostgreSQL
- REST
- one deployable modular application
- no microservices for MVP
- no Google Cloud dependency

Use Django's mature authentication/session machinery. Do not implement password hashing, token crypto or OAuth/OIDC protocols from scratch.

## Owned by QM Core / QM Identity

- custom Django User from the first migration,
- organizations,
- memberships,
- coarse roles/permissions,
- product entitlements,
- authentication / later service auth,
- audit identity/correlation.

## Consumers

- Zgodomat,
- VerifyTest,
- Booking,
- Neuroconnect **NC Platform** (training application).

## Owned by products / clients

- consent/document acceptance -> Zgodomat,
- tests/sessions/answers/scoring -> VerifyTest,
- appointments/availability -> Booking,
- invoices/payments -> billing,
- Course/CourseSession/Enrollment/Material and BUR training workflow -> Neuroconnect / NC Platform.

Fine-grained product authorization and product-specific audit trails stay in the product.

## Architecture

The reviewed architecture is in `docs/ARCHITECTURE.md`.

Independent products can work alone while using QM Core/QM Identity for shared identity and access. Social login/SSO is prepared for later but not implemented now.

See `PROJECT_STATE.md` for current status.


## Current implementation slice

Zgodomat is the first real consumer. The first executable Stage 1 slice now lives in this repository and includes custom User, Organization, Membership, coarse roles, ProductEntitlement and the minimal REST contract in `docs/API.md`.

The current auth mechanism is Django session + email/password for staging validation. It is not the final cross-domain SSO design.

### Local development

Use PostgreSQL by default. For a deliberately local-only smoke test, set `QM_DATABASE_ENGINE=sqlite`.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py test
```

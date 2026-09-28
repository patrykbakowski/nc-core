# QM Core / QM Identity

Shared identity and access foundation owned by the QManufacture product family.

> Repository note: the repository is still named `patrykbakowski/nc-core` for continuity. `NC Core` and `NC ID` are deprecated architecture names. The current names are **QM Core** and **QM Identity**.

## Goal

Provide one stable identity/access core for independent QManufacture products and external clients without becoming a catch-all business backend.

## Stack

- Django
- PostgreSQL
- REST
- standards-based OAuth 2.0 / OpenID Connect provider
- one deployable modular application
- no microservices for MVP
- no Google Cloud dependency

Use Django's mature authentication/session machinery and Django OAuth Toolkit. Do not implement password hashing, token crypto or OAuth/OIDC protocols from scratch.

## Owned by QM Core / QM Identity

- custom Django User from the first migration,
- organizations,
- memberships,
- coarse organization roles,
- product entitlements,
- authentication and OIDC,
- later service authentication,
- audit identity/correlation.

## Consumers

Primary QManufacture consumers:

- Zgodomat,
- VerifiTest,
- Booking,
- future QManufacture products.

External clients such as Neuroconnect may use the same identity contract without moving their business data into QM Core.

## Owned by products / clients

- consent/document acceptance -> Zgodomat,
- tests/sessions/answers/scoring -> VerifiTest,
- appointments/availability -> Booking,
- invoices/payments -> billing,
- training courses/enrollments/materials -> external training platforms.

Fine-grained product authorization and product-specific audit trails stay in the product.

## Authentication contract

For separate product domains, the canonical flow is:

1. product redirects the browser to QM Identity,
2. QM Identity authenticates the user,
3. product uses **OIDC Authorization Code + PKCE (S256)**,
4. product identifies the user by OIDC `sub` (the QM UUID), never by email matching,
5. product creates its own local session,
6. product may query QM Identity with the bearer token for current user/membership information,
7. organization/product access is checked at runtime via `/api/v1/access-context/` with scope `qm.access`.

Roles and entitlements deliberately stay out of long-lived ID-token claims so revoked access can take effect through the authoritative runtime check.

Django session login remains available for the central account UI, admin and same-origin validation. It is not the cross-domain integration mechanism.

External Google/Facebook/Microsoft login is still deferred. Adding OIDC here means **QM Identity is the provider for our products**, not that an external social provider is enabled.

## Documentation

- architecture: `docs/ARCHITECTURE.md`
- API: `docs/API.md`
- product integration recipe: `docs/IDENTITY_INTEGRATION.md`
- current state: `PROJECT_STATE.md`

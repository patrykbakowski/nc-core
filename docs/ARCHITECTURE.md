# QM Core / QM Identity Architecture

## Naming

QManufacture owns the shared technical foundation.

- **QM Core** — shared identity/access foundation.
- **QM Identity** — identity/authentication module inside QM Core.
- **NC Core** and **NC ID** — deprecated architecture names. The repository remains named `patrykbakowski/nc-core` for continuity only.

## Purpose

QM Core is shared identity and access infrastructure for QManufacture products and optional external clients. It owns users, verified external identity links, organizations, memberships, coarse roles, product entitlements, authentication and audit identity correlation.

**QM Core is infrastructure, not a product backend.** It does not own product business logic or product-domain data.

## Implementation stack

- Django + PostgreSQL;
- REST;
- Django sessions for central/same-origin use;
- Django OAuth Toolkit for standards-based OAuth2/OIDC;
- Gunicorn container runtime;
- one deployable modular application;
- no GraphQL or microservices without a concrete requirement;
- no Google Cloud dependency.

## Domain model

### User

- UUID primary key;
- unique normalized email as native Django `USERNAME_FIELD`;
- first/last name and optional profile fields;
- account state: active, suspended, deleted;
- Django password/session machinery.

The stable cross-product identifier is the OIDC `sub`, equal to the QM User UUID.

### ExternalIdentity

A verified mapping from a QM User to a legacy or external provider identity:

- UUID;
- QM User;
- provider;
- provider subject;
- optional metadata;
- unique provider + subject.

This table is the future linking boundary for systems such as Google, Microsoft or legacy WordPress identities. A row is created only after a verified linking flow. Matching email addresses alone never create a link.

### Organization

- UUID;
- name and slug;
- active/suspended/deleted state;
- tenant isolation boundary.

### Membership

A user belongs to an organization with one coarse role:

- `org:owner`;
- `org:admin`;
- `org:member`;
- `org:viewer`.

Membership has its own lifecycle and fails closed unless active.

### Product entitlement

An organization may have a current entitlement to a product slug such as `zgodomat`, `verifitest` or `booking`.

Entitlement contains status, plan and optional validity interval.

An entitlement answers whether the organization can use the product. It does not replace product-level fine authorization.

## Authentication architecture

### Central Identity Provider

QM Identity is the OpenID Provider / Authorization Server for QManufacture products.

Separate product domains use:

- OIDC Authorization Code;
- PKCE S256;
- exact HTTPS redirect URIs;
- discovery/JWKS;
- product-local sessions after callback.

Shared cross-domain cookies are explicitly not the architecture.

### Stable claims

OIDC tokens expose stable identity claims such as:

- `sub`;
- email;
- name/given/family name when requested by standard scopes.

Current organization roles and product entitlements are not copied into long-lived ID tokens. Products query current access when they need an authorization decision.

### Runtime access context

`GET /api/v1/access-context/` returns the current active user, organization membership/coarse role and active entitlement for a requested product.

OAuth calls require scope `qm.access`.

This makes suspension and entitlement revocation authoritative at runtime instead of waiting for an ID token to expire.

### Central sessions

Django sessions remain valid for:

- central login UI;
- Django admin;
- same-origin testing.

A middleware drops existing central sessions when the QM account becomes inactive.

## Authorization boundary

QM Core owns:

- identity;
- verified external identity links;
- organizations;
- memberships;
- coarse roles;
- product entitlements;
- shared authentication;
- identity/access audit correlation.

Products own:

- product entities and workflows;
- product-specific authorization;
- product-specific audit evidence.

Examples:

- Zgodomat owns documents, versions, requests and acceptance evidence;
- VerifiTest owns tests, sessions, answers and scoring;
- Booking owns appointments and availability.

## User without organization entitlement

Not every authenticated user must belong to an entitled organization.

A recipient or customer can authenticate through QM Identity and be authorized by a product-domain relationship. Products should not manufacture placeholder organizations for such users.

## Account linking

Never link identities solely because email addresses match.

If a legacy or external account is linked, the linking flow must prove control of both identities or otherwise provide equivalent verified evidence. Only then is an `ExternalIdentity` record created.

## Security requirements

- production HTTPS;
- OIDC RSA private key stored only as a deployment secret;
- exact production redirect URIs;
- PKCE S256;
- no hand-written OAuth/JWT crypto;
- tenant isolation tests;
- fail closed on inactive user/membership/organization/entitlement;
- audit privilege changes;
- no secrets in the repository.

## Deployment and cutover

QM Identity deploys into its own PostgreSQL database.

The former mixed QManufacture staging may be used only as a migration source/rollback reference. It must not remain a second authoritative identity store after cutover.

A one-time snapshot importer preserves:

- UUIDs;
- password hashes;
- organizations;
- mapped coarse roles;
- product entitlements;
- verified external identity links.

The importer refuses a non-empty target database. Full procedure and rollback checks are documented in `docs/DEPLOYMENT.md`.

## External identity providers

Google/Facebook/Microsoft login is a separate future capability.

QM Identity becoming an OIDC provider for our products does **not** require Google Cloud and does not enable social login.

## Delivery sequence

### Stage 1 — identity/access data model

Implemented:

- UUID email-native User;
- Organization/Membership;
- coarse roles;
- ProductEntitlement;
- session login;
- `me` and runtime access-context;
- tenant isolation tests.

### Stage 2 — cross-domain Identity

Current implementation:

- OAuth2/OIDC provider;
- Authorization Code + PKCE;
- central browser login;
- bearer authentication on REST endpoints;
- `qm.access` scope;
- stable identity claims;
- RP-initiated logout;
- verified `ExternalIdentity` model;
- product integration contract;
- clean deployment/cutover procedure;
- one-time UUID/password-hash preserving legacy identity importer.

### Stage 3 — account lifecycle and hardening

Next:

- password reset;
- invitations;
- identity/access audit records;
- login throttling/lockout;
- operational key rotation procedure.

### Stage 4 — service provisioning

Add when a concrete product flow needs it:

- service-to-service credentials;
- scoped provisioning APIs;
- entitlement changes from commerce/billing events.

### Stage 5 — external IdP / enterprise auth

Only when justified:

- social login;
- SAML;
- verified provider linking UI;
- MFA.

## Canonical product integration

See `docs/IDENTITY_INTEGRATION.md`.

New products must integrate against that contract rather than create another password store or private interpretation of roles.

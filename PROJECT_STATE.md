# QM Core / QM Identity — Project State

**Updated:** 2026-09-28  
**Repository:** `patrykbakowski/nc-core` (legacy repository name)  
**Status:** ACTIVE / cross-domain Identity foundation in implementation

## Purpose

Provide shared identity/access capabilities owned by QManufacture and usable by independent products without moving their business domains into the core.

## Naming decision

- **QManufacture** owns the shared technical foundation.
- **QM Core** is that shared foundation.
- **QM Identity** is the identity/authentication module inside QM Core.
- **NC Core** and **NC ID** are deprecated names. The repository name remains unchanged for continuity.

## Implemented on main before this slice

- Django + PostgreSQL project;
- custom User with UUID primary key and email as `USERNAME_FIELD`;
- Organization and Membership;
- coarse roles `org:owner`, `org:admin`, `org:member`, `org:viewer`;
- ProductEntitlement with status and validity window;
- email/password session login/logout/me;
- generic `GET /api/v1/access-context/`;
- fail-closed tenant and entitlement tests;
- PostgreSQL CI;
- no Google Cloud and no social-login dependency.

## Current Identity slice

The previous session-only contract is insufficient for independent products on different registrable domains. The active implementation therefore adds the cross-domain foundation now rather than postponing it.

Current branch: `feature/qm-identity-oidc-foundation`.

Included:

- Django OAuth Toolkit as the standards-based OAuth2/OIDC provider;
- OIDC Authorization Code + PKCE;
- RSA-signed ID tokens when `QM_OIDC_RSA_PRIVATE_KEY` is configured;
- central browser login at `/accounts/login/`;
- OIDC discovery/JWKS/UserInfo through the provider routes under `/o/`;
- OAuth2 bearer authentication for the existing REST API;
- scope `qm.access` for runtime organization/product access checks;
- stable identity claims only in OIDC; roles/entitlements remain runtime data;
- central account-status enforcement for both new authentication and existing sessions;
- RP-initiated logout support;
- product integration contract in `docs/IDENTITY_INTEGRATION.md`.

## Boundary that remains unchanged

QM Identity answers:

- who is the user?
- which organizations is the user an active member of?
- what coarse organization role do they have?
- does the organization currently have an entitlement to product X?

Each product still answers its own domain questions, for example whether a particular document may be edited, a test may be scored or an appointment may be changed.

## Deployment requirements for OIDC

Production OIDC requires:

- `QM_OIDC_RSA_PRIVATE_KEY` supplied as a secret, never committed;
- `QM_OIDC_ISSUER=https://account.qmanufacture.com/o` (planned production issuer);
- HTTPS;
- exact registered redirect URIs for every client;
- a registered OAuth/OIDC Application per product deployment.

No external social provider is required.

## Next after this slice

1. pass repository CI and merge the OIDC foundation;
2. deploy QM Identity to staging with a generated RSA key;
3. register the first real OIDC client (Zgodomat) and perform end-to-end browser login;
4. add the smallest account-lifecycle features required by the pilot: password reset and invitations;
5. then integrate VerifiTest and Booking against the same contract, without creating new identity stores.

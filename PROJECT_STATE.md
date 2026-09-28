# QM Core / QM Identity — Project State

**Updated:** 2026-09-28  
**Repository:** `patrykbakowski/nc-core` (legacy repository name)  
**Status:** ACTIVE / cross-domain Identity deployed to staging; central account lifecycle in implementation

## Purpose

Provide one shared identity/access authority owned by QManufacture and usable by independent products without moving their business domains into the core.

## Canonical identity model

QM Identity owns:

- UUID/email-native User;
- verified ExternalIdentity links;
- Organization;
- Membership with coarse role;
- ProductEntitlement;
- authentication/OIDC;
- identity/access correlation.

Products own fine-grained authorization and product audit evidence.

## Main before PR #4

Already implemented:

- UUID User with email as native Django login identifier;
- Organization/Membership;
- roles `org:owner`, `org:admin`, `org:member`, `org:viewer`;
- ProductEntitlement;
- session login/logout/me;
- runtime `GET /api/v1/access-context/`;
- tenant/entitlement tests;
- PostgreSQL CI.

## PR #4 — cross-domain QM Identity

Branch: `feature/qm-identity-oidc-foundation`.

Implemented:

- standards-based OAuth2/OIDC provider through Django OAuth Toolkit;
- Authorization Code + PKCE;
- central browser login;
- OIDC discovery/JWKS/UserInfo;
- RSA-signed ID tokens when a deployment key is supplied;
- OAuth2 bearer authentication for the REST API;
- `qm.access` scope for current organization/product access;
- stable identity claims only; roles and entitlements stay runtime-authoritative;
- suspended/deleted accounts cannot create a new session and existing central sessions are dropped;
- RP-initiated logout support;
- verified `ExternalIdentity` model for future/legacy account linking;
- non-root Gunicorn Docker image;
- database-backed `/healthz/`;
- proxy/secure-cookie deployment settings;
- product integration contract;
- clean deployment/cutover procedure;
- one-time legacy snapshot importer preserving UUIDs and password hashes;
- CI generates an ephemeral RSA key and verifies live OIDC discovery/JWKS.

## Legacy state to migrate

The former mixed QManufacture staging is not the target architecture. It currently contains the compatibility identity source:

- 2 users;
- 1 organization;
- 1 membership;
- 2 product accesses;
- 0 external identity links.

Its UUID/email-native user model is close enough to the new QM Identity model for a lossless one-time mapping.

The old mixed staging remains unchanged until clean QM Identity staging is verified. After cutover it must not remain a second authoritative identity store.

## OIDC deployment requirements

Production target issuer:

```text
https://account.qmanufacture.com/o
```

A staging issuer may use an environment-specific technical HTTPS hostname.

Required:

- generated RSA signing key stored only as a deployment secret;
- HTTPS;
- exact redirect URIs;
- separate OIDC Application per independently deployed client;
- product integrations identify users by `sub`, never email matching.

No Google Cloud or external social provider is required.

## Current next sequence

1. final CI for PR #4;
2. merge PR #4;
3. deploy clean QM Identity staging with its own PostgreSQL database;
4. export the legacy identity source and run importer dry-run;
5. import and verify counts/UUIDs/password authentication;
6. publish staging OIDC issuer over HTTPS;
7. register Zgodomat as first real client and run browser Authorization Code + PKCE end to end;
8. then add central password reset/invitations and onboard VerifiTest/Booking to the same contract.

See:

- `docs/ARCHITECTURE.md`;
- `docs/API.md`;
- `docs/IDENTITY_INTEGRATION.md`;
- `docs/DEPLOYMENT.md`.


## Account lifecycle follow-up — 2026-09-28

The first product integration exposed one remaining identity-boundary problem: products such as Zgodomat must be able to invite a recipient without creating a second password store.

The current lifecycle branch adds:

- central password reset UI;
- central invitation activation UI;
- purpose-scoped invitation tokens;
- OAuth scope `qm.provision`;
- Client-Credentials-only `POST /api/v1/accounts/invitations/`;
- account creation/invitation without membership, role or entitlement grants;
- hard refusal to reactivate suspended/deleted accounts;
- invitation resend invalidates the previous link by rotating the unusable password hash.

Product integration rule: products may keep local profile/domain rows keyed by QM UUID, but passwords and activation live only in QM Identity.

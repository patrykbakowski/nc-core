# QM Core / QM Identity — Project State

**Updated:** 2026-09-29  
**Repository:** `patrykbakowski/nc-core` (legacy repository name)  
**Status:** ACTIVE / CENTRAL IDENTITY AUTHORITY / LEAST-PRIVILEGE CLIENT POLICIES DEPLOYED TO STAGING

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

## Current deployment\n\nClean staging runs at `https://identity-staging.neuroconnect.pl/` with OIDC issuer `https://identity-staging.neuroconnect.pl/o`. Current deployed source is `62286a2e2d9a142ac4fb895960de8a7d9c4c79f7`. Zgodomat and NC Platform are live staging consumers. VerifyTest and Booking reuse the same contract when implementation starts.\n\nSee:\n\n- `docs/ARCHITECTURE.md`;\n- `docs/API.md`;\n- `docs/IDENTITY_INTEGRATION.md`;\n- `docs/DEPLOYMENT.md`.\n

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


## Service authorization follow-up — 2026-09-28

Zgodomat exposed a second backend requirement: a product may need to verify that a known QM user still has current organization/product access when that user is not the caller, for example when validating whether the issuer of a pending acceptance request still has authority.

The current branch adds:

- `GET /api/v1/service/access-context/`;
- Client Credentials authentication;
- mandatory `qm.access` scope;
- lookup by immutable QM `user_id`;
- the same active user/membership/organization/entitlement checks as browser/user access-context;
- no impersonation and no user session issuance.

This becomes the canonical backend authorization check for product jobs and server-side workflows.

## OAuth client least-privilege hardening — 2026-09-29

PR #7 merged as `62286a2e2d9a142ac4fb895960de8a7d9c4c79f7` and is deployed to clean staging.

Added:

- `OAuthClientPolicy` and `OAuthClientProductGrant`;
- exact per-client product allowlists;
- explicit `can_provision_accounts`;
- fail-closed behavior when client policy is missing/inactive;
- product-policy enforcement on user and service access-context;
- OAuth `/auth/me/` membership filtering;
- provisioning requires both `qm.provision` and policy permission;
- Django admin registration for identity/access models.

Active staging policy:

- Zgodomat web/service -> `zgodomat`; provisioning only on service client;
- NC Platform web/service -> `neuroconnect`; provisioning only on service client;
- old unused OAuth applications have no policy and therefore fail closed.

Live verification:

- NC Platform own-product access allowed; `zgodomat` cross-product access denied;
- Zgodomat own-product access allowed; `neuroconnect` cross-product access returns 403;
- provisioning an existing active account succeeds for both service clients without sending an invitation;
- Identity public health remains 200.

Pre-change staging backup: `/srv/qmanufacture/identity/staging/backups/qm_identity_staging-pre-client-policy-20260929.sql.gz`.

# QM Core API v1 — minimal Zgodomat contract

**Status:** first implementation slice, not production SSO.

Zgodomat is the first real consumer of QM Core / QM Identity. This contract deliberately covers only identity, organization membership and product entitlement. Zgodomat continues to own documents, document versions, acceptance requests, acceptance evidence and all product-specific authorization.

## Authentication model for this slice

QM Identity uses Django sessions and email/password login. User and organization identifiers are UUIDs, and email is the native Django authentication identifier (there is no separate username field). This is suitable for the first same-origin/staging integration and automated contract tests.

It is **not** the final cross-domain SSO design. Separate product domains will later use standards-based OIDC/service authentication. Do not share cookies across unrelated registrable domains and do not link accounts by matching email alone.

## Endpoints

### POST /api/v1/auth/login/

Request:

```json
{"email":"person@example.com","password":"..."}
```

Creates a Django session for an active QM Identity user.

### POST /api/v1/auth/logout/

Ends the current session.

### GET /api/v1/auth/me/

Returns the authenticated user and active memberships in active organizations. It does not expose product-domain data.

### GET /api/v1/access-context/?organization_id=<uuid>&product=zgodomat

Returns the minimum context Zgodomat needs before applying its own authorization:

```json
{
  "user": {"id":"...","email":"person@example.com"},
  "organization": {"id":"...","name":"Example","slug":"example"},
  "membership": {"id":"...","role":"org:admin"},
  "entitlement": {"id":"...","product":"zgodomat","plan":"pilot","valid_from":null,"valid_until":null}
}
```

The request fails closed when the user is unauthenticated, the membership or organization is inactive, or the product entitlement is unavailable or outside its validity window.

Cross-tenant membership failures return 404 to avoid confirming another tenant's membership relationship. Missing/inactive entitlement returns 403.

## Ownership boundary

QM Core owns user identity, organization, membership/coarse role and product entitlement.

Zgodomat owns documents and versions, acceptance requests, acceptance/withdrawal records, evidence/audit trail and fine-grained product authorization.

## Deferred intentionally

Public registration, invitations, password-reset UI, service API keys, OAuth/OIDC/SAML, social login, MFA, billing and product-specific permission catalogues remain deferred until a real integration requires them.

# QM Core API v1

QM Core / QM Identity exposes two authentication modes:

- Django session authentication for the central account UI, admin and same-origin testing;
- OAuth2 bearer authentication for product integrations.

For separate product domains, use OIDC Authorization Code + PKCE and bearer tokens. Do not share cookies across unrelated registrable domains.

## OIDC provider

Provider routes are mounted under `/o/`.

When production is configured with `QM_OIDC_ISSUER=https://account.qmanufacture.com/o`, clients use OIDC discovery and should not hard-code endpoint details.

Product clients request:

```text
openid profile email qm.access
```

`qm.access` is required only when the client needs the QM organization/product access endpoint. Backend service clients that provision central accounts use a separate `qm.provision` scope and Client Credentials; they do not receive user identity through that token.

The stable user identifier is the OIDC `sub`, which is the QM User UUID. Never link accounts solely because email addresses match.

## Session endpoints

### POST /api/v1/auth/login/

Request:

```json
{"email":"person@example.com","password":"..."}
```

Creates a Django session for an active QM Identity user.

### POST /api/v1/auth/logout/

Ends the current Django session.

### GET /api/v1/auth/me/

Returns the authenticated user and active memberships in active organizations.

It accepts either a valid Django session or an OAuth2 bearer token.

Example response:

```json
{
  "user": {
    "id": "uuid",
    "email": "person@example.com",
    "first_name": "Pat",
    "last_name": "Example"
  },
  "memberships": [
    {
      "id": "uuid",
      "organization": {
        "id": "uuid",
        "name": "Example Org",
        "slug": "example"
      },
      "role": "org:admin"
    }
  ]
}
```

## Runtime access context

### GET /api/v1/access-context/?organization_id=<uuid>&product=<product-id>

Returns the minimum context a product needs before applying its own fine-grained authorization.

OAuth bearer calls require scope `qm.access`.

Example:

```json
{
  "user": {"id":"...","email":"person@example.com"},
  "organization": {"id":"...","name":"Example","slug":"example"},
  "membership": {"id":"...","role":"org:admin"},
  "entitlement": {
    "id":"...",
    "product":"zgodomat",
    "plan":"pilot",
    "valid_from":null,
    "valid_until":null
  }
}
```

The request fails closed when:

- the user is not authenticated or the QM account is inactive;
- membership is inactive;
- organization is inactive;
- the entitlement is missing, inactive or outside its validity window;
- an OAuth token lacks `qm.access`.

Cross-tenant membership failures return 404. Missing/inactive entitlement returns 403.

## Service access context

### GET /api/v1/service/access-context/?user_id=<uuid>&organization_id=<uuid>&product=<product-id>

This endpoint is for trusted product backends and background jobs that need a current authorization decision for a known QM user UUID when that user is not the caller.

It requires a Client Credentials OAuth token with the `qm.access` scope.

It applies the same authoritative checks as the user-facing access-context:

- QM user must be active;
- membership must be active;
- organization must be active;
- entitlement for the requested product must be current.

It returns the same user/organization/membership/entitlement payload. Cross-tenant or inactive user/membership relationships fail closed with 404; missing/inactive entitlement returns 403.

This is **not impersonation**. The service receives only access context and does not receive a user session or user token.

## Authorization boundary

QM Core owns identity, organization, membership/coarse role and product entitlement.

Products own their business data and fine-grained permissions. The presence of an entitlement means the organization can use the product; it does not answer whether the current user can perform every action inside that product.

## Deliberately not encoded in ID tokens

Do not put current roles or product entitlements into long-lived ID-token claims. Products query current access when they need an authorization decision so suspension or entitlement revocation is not delayed until token renewal.

## Central account provisioning

### POST /api/v1/accounts/invitations/

This endpoint is for trusted product backends, not browsers. It requires an OAuth2 access token issued with the Client Credentials grant and the `qm.provision` scope.

Request:

```json
{"email":"person@example.com"}
```

Behavior:

- if no account exists, QM Identity creates an inactive UUID account with an unusable password and sends a central activation link;
- if the account is already active, no invitation is sent and the existing UUID is returned;
- if the account is pending, the invitation is reissued and the previous invitation token becomes invalid;
- suspended/deleted accounts are never reactivated by a product service;
- creating/inviting an account grants no organization membership, role or product entitlement.

A successful response contains the central user UUID and state (`active` or `pending`). Product code may create a local shadow/profile keyed by that UUID, but QM Identity remains the credential authority.

## Central account UI

QM Identity owns:

- `/accounts/login/`;
- `/accounts/password-reset/`;
- `/accounts/invite/<uid>/<token>/`.

Password reset deliberately sends mail only for active QM accounts and does not reveal whether an account exists.

## Still deferred

- external social login (Google/Facebook/Microsoft),
- SAML,
- public self-registration,
- invitation workflow,
- password-reset UI,
- MFA,
- billing integration,
- product-specific permission catalogues.

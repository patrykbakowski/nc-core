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

`qm.access` is required only when the client needs the QM organization/product access endpoint.

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

## Authorization boundary

QM Core owns identity, organization, membership/coarse role and product entitlement.

Products own their business data and fine-grained permissions. The presence of an entitlement means the organization can use the product; it does not answer whether the current user can perform every action inside that product.

## Deliberately not encoded in ID tokens

Do not put current roles or product entitlements into long-lived ID-token claims. Products query current access when they need an authorization decision so suspension or entitlement revocation is not delayed until token renewal.

## Still deferred

- external social login (Google/Facebook/Microsoft),
- SAML,
- public self-registration,
- invitation workflow,
- password-reset UI,
- MFA,
- billing integration,
- product-specific permission catalogues.

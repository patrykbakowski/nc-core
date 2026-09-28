# QM Identity — product integration contract

This is the default authentication recipe for Zgodomat, VerifiTest, Booking and future QManufacture products.

## 1. One identity, local product session

Each product is an OIDC Relying Party.

The product must **not** store a second QM password database. It may keep a local product user/profile keyed by the immutable QM OIDC `sub` when product-specific data needs a local owner.

Canonical sequence:

```text
browser
  -> product
  -> QM Identity /authorize
  -> central login
  -> product callback with authorization code
  -> token exchange with PKCE
  -> validate ID token
  -> create product-local session
```

Use an established OIDC client library in the product. Do not implement JWT/OAuth validation by hand.

## 2. Flow and scopes

Use:

- Authorization Code flow;
- PKCE with `S256`;
- HTTPS redirect URIs;
- state and nonce validation;
- exact redirect URI registration.

Request scopes:

```text
openid profile email qm.access
```

If the product only needs identity and never checks QM organization/product access, it may omit `qm.access`.

## 3. Stable identity mapping

Use:

```text
OIDC sub == QM User UUID
```

Store this UUID as the external identity key in the product.

Email is profile data and a login identifier. It is **not** an account-linking key because addresses can change and matching email alone is not a verified linking flow.

## 4. Runtime authorization

Authentication answers "who is this?".

For organization workspaces, the product calls:

```http
GET /api/v1/access-context/?organization_id=<uuid>&product=<product-id>
Authorization: Bearer <access-token>
```

The bearer token must have `qm.access`.

The response gives:

- current QM user,
- active organization,
- active membership,
- coarse role,
- current product entitlement.

The product then applies its own fine-grained rules.

Examples:

- Zgodomat decides who may edit or accept a specific document;
- VerifiTest decides who may administer or score a specific test;
- Booking decides who may edit a particular appointment.

Those rules do not belong in QM Identity.

## 5. User without an organization entitlement

A product may still authenticate an ordinary end user who has no organization membership or entitlement.

Examples include a document recipient or a customer invited into a product-specific workflow. In that case use OIDC identity and product-domain relations. Do not invent a fake organization merely to satisfy the access-context endpoint.

## 6. Client registration

Register one OAuth/OIDC Application per independently deployed product client.

Server-side web applications should normally be confidential clients. Browser-only or native apps are public clients and still use PKCE.

Redirect URIs must be exact. Do not use wildcard production redirects.

Client secrets and the QM OIDC RSA signing key are deployment secrets and must never be committed.

## 7. Provider configuration

Planned production issuer:

```text
https://account.qmanufacture.com/o
```

Corresponding discovery document:

```text
https://account.qmanufacture.com/o/.well-known/openid-configuration
```

Products should consume discovery metadata rather than hard-code authorize/token/JWKS/UserInfo URLs.

## 8. Logout

Product logout ends the product-local session first.

QM Identity exposes RP-initiated OIDC logout for clients that also need to end the central SSO session. A product should not assume that logging out of one product must always log the user out of every other product.

## 9. What is intentionally absent

The current shared contract does not require:

- Google Cloud;
- Google/Facebook/Microsoft login;
- shared cross-domain cookies;
- duplicated user tables with passwords;
- product business models inside QM Core;
- roles or entitlements embedded permanently in ID tokens.

## 10. Definition of ready for a new product

A new product is correctly attached to QM Identity when:

1. it has its own registered OIDC client;
2. login uses Authorization Code + PKCE;
3. local identity is keyed by `sub`;
4. it creates its own session after the callback;
5. organization workspaces use runtime `access-context` when applicable;
6. product-specific permissions remain in the product;
7. logout and suspended-user behavior are tested;
8. no password or email-match account linking is duplicated locally.

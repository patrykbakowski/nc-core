# QM Identity deployment and legacy cutover

## Goal

Deploy QM Identity as the single identity/access authority for QManufacture products without creating long-lived parallel user stores.

The old mixed QManufacture staging is a migration source and rollback reference only. It must not remain a second authoritative Identity after cutover.

## Staging topology

Recommended staging shape:

- public issuer: environment-specific HTTPS hostname;
- Django/Gunicorn app behind the existing local Nginx + Cloudflare Tunnel pattern;
- PostgreSQL on a private Docker network, no published database port;
- application bound to localhost only;
- RSA signing key and Django secret stored outside the repository in root-only environment files.

Production target issuer remains:

```text
https://account.qmanufacture.com/o
```

A temporary staging issuer may use a technical hostname. Products must obtain endpoints through OIDC discovery, so issuer/host is environment configuration rather than application code.

## Required environment

```text
DJANGO_SECRET_KEY=...
DJANGO_ALLOWED_HOSTS=identity-staging.example
DJANGO_CSRF_TRUSTED_ORIGINS=https://identity-staging.example
POSTGRES_DB=...
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
QM_OIDC_RSA_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
QM_OIDC_ISSUER=https://identity-staging.example/o
QM_SECURE_COOKIES=1
QM_SECURE_SSL_REDIRECT=0
```

The RSA private key, Django secret and database credentials are secrets. Prefer a root-owned key file mounted read-only into the container via `QM_OIDC_RSA_PRIVATE_KEY_FILE`; never commit or print them.

`QM_SECURE_SSL_REDIRECT=0` is appropriate when HTTPS is terminated by the trusted Cloudflare/Nginx edge and the application receives the forwarded scheme. The app honors `X-Forwarded-Proto`.

## Initial deployment

1. Create an empty PostgreSQL database dedicated to QM Identity.
2. Build the repository Docker image.
3. Run migrations.
4. Verify `/healthz/`.
5. Verify OIDC discovery and JWKS.
6. Only then import the legacy identity snapshot.
7. Validate login with an existing account.
8. Register product OIDC clients.
9. Keep the old source deployment unchanged until the first product completes end-to-end login.

## Legacy snapshot contract

The one-time importer is:

```bash
python manage.py import_identity_snapshot /secure/path/identity.json --dry-run
python manage.py import_identity_snapshot /secure/path/identity.json
```

The importer refuses to run against a non-empty target Identity database.

Snapshot shape:

```json
{
  "users": [],
  "organizations": [],
  "memberships": [],
  "entitlements": [],
  "external_identities": []
}
```

The migration preserves:

- User UUID;
- password hash, so a user does not need a forced password reset;
- organization UUID;
- membership UUID and mapped coarse role;
- entitlement UUID and validity window;
- verified external identity links.

Legacy role mapping:

- `owner` -> `org:owner`
- `admin` -> `org:admin`
- `member` -> `org:member`
- `viewer` -> `org:viewer`

Legacy inactive organizations/users/memberships/entitlements map to a suspended state.

The snapshot contains identity data and password hashes. Store it with root-only permissions, do not expose it over HTTP, and remove it only under an explicit retention decision after cutover.

## Cutover checks

Before treating QM Identity as authoritative:

- target counts match the snapshot;
- sampled UUIDs match source UUIDs;
- existing passwords still authenticate;
- suspended users cannot authenticate;
- memberships and roles match;
- product entitlements match and validity windows are preserved;
- `/api/v1/access-context/` returns the expected role/entitlement;
- OIDC discovery/JWKS are publicly reachable over HTTPS;
- one real product completes Authorization Code + PKCE login and creates its local session;
- revoking a membership or entitlement removes access on the runtime access-context check.

## Rollback

Before a real product cutover, rollback is simply to point that product back to its prior authentication path; the legacy source remains unchanged.

Do not perform bidirectional identity writes. Once QM Identity is declared authoritative, new identity/access changes must be made there only. If rollback after that point is required, reconcile changes explicitly rather than copying databases blindly.

## Product onboarding

For each product:

1. register a separate OIDC client;
2. set exact redirect/logout URIs;
3. configure issuer discovery;
4. identify the user by OIDC `sub`;
5. create a product-local session;
6. use `qm.access` and runtime access-context for organization workspaces;
7. leave fine-grained product permissions in the product.

See `IDENTITY_INTEGRATION.md` for the application-side contract.


## OIDC signing-key rotation

QM Identity supports an overlap window during RSA signing-key rotation.

Environment:

```text
QM_OIDC_RSA_PRIVATE_KEY_FILE=/run/secrets/qm_oidc_active.pem
QM_OIDC_RSA_PRIVATE_KEYS_INACTIVE_FILES=/run/secrets/qm_oidc_previous.pem
```

The active key signs new ID tokens. Keys listed in `QM_OIDC_RSA_PRIVATE_KEYS_INACTIVE_FILES` are not used for signing, but remain published in JWKS so clients can verify tokens issued before the cutover.

Safe rotation procedure:

1. Generate a new RSA private key outside the repository.
2. Keep the current active key unchanged as the rollback copy.
3. Deploy the new key as `QM_OIDC_RSA_PRIVATE_KEY_FILE`.
4. Move the former active key path into `QM_OIDC_RSA_PRIVATE_KEYS_INACTIVE_FILES`.
5. Restart QM Identity.
6. Verify health, OIDC discovery and that JWKS exposes both keys.
7. Complete a fresh Authorization Code + PKCE login from at least one product.
8. Keep the former key in the inactive list for at least the maximum lifetime of previously issued ID tokens plus JWKS cache overlap.
9. Remove the former key from the inactive list only after that overlap window.
10. Restart and verify JWKS again.

Do not rotate the issuer URL, OAuth client IDs or client secrets as part of signing-key rotation unless separately required. Access tokens stored/validated by the authorization server are a separate concern from ID-token signature verification.

Emergency key compromise is different: replace the active key immediately, remove the compromised key from JWKS instead of honoring an overlap, and force reauthentication where needed.

## Identity/access audit

QM Identity keeps a dedicated `AuditEvent` stream for central identity/access mutations that happen through service APIs or the QM admin surface.

Current coverage:

- central account invitation creation/resend performed by OAuth service clients;
- creation/change/deletion of identity/access objects through Django admin;
- actor type and actor user or OAuth client ID;
- target model and ID;
- organization/product context when applicable;
- structured metadata for the mutation.

The audit table is append-only through the admin UI: add/change/delete are disabled for `AuditEvent` itself.

Django's own `django_admin_log` remains available as a second admin-level trace. Product-domain events still belong to each product and must not be copied wholesale into QM Identity.


## Authentication throttling

QM Identity uses a PostgreSQL-backed fixed-window throttle for public credential-entry endpoints. It is shared across Gunicorn workers and does not depend on per-process memory.

Covered endpoints:

- central browser login;
- REST login endpoint;
- central password-reset request.

The throttle key stores no raw IP address or e-mail. It stores an HMAC fingerprint derived from client IP + normalized identifier using the Django secret key.

Default environment values:

```text
QM_LOGIN_RATE_LIMIT=10
QM_LOGIN_RATE_WINDOW_SECONDS=300
QM_PASSWORD_RESET_RATE_LIMIT=5
QM_PASSWORD_RESET_RATE_WINDOW_SECONDS=900
```

The browser and REST login endpoints intentionally share the same `login` scope, so switching endpoints does not reset the attempt budget.

Client IP resolution prefers Cloudflare `CF-Connecting-IP`, then the first `X-Forwarded-For` value, then `REMOTE_ADDR`. This assumes the application remains reachable only through the trusted local Nginx/Cloudflare path or localhost binding. Do not expose the Gunicorn origin directly to untrusted networks while trusting forwarded headers.

A throttled request returns HTTP 429 and a `Retry-After` header.

This is deliberately throttling rather than permanent account lockout. A global account-only lockout would let an attacker deny service to a known e-mail address.

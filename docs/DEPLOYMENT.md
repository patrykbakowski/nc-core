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

The RSA private key, Django secret and database credentials are secrets. Never commit or print them.

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

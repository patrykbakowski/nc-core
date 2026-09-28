# AGENTS.md

## Purpose

This repository implements **QM Core / QM Identity**, the shared identity/access foundation owned by QManufacture.

The repository name `nc-core` is legacy. Do not introduce new architecture terminology based on “NC Core” or “NC ID”.

Read `docs/ARCHITECTURE.md`, `docs/IDENTITY_INTEGRATION.md` and `PROJECT_STATE.md` before implementation changes.

## Hard boundaries

QM Core owns:

- custom user identity,
- organizations,
- memberships,
- coarse roles,
- product entitlements,
- authentication and OIDC,
- future service authentication,
- audit identity/correlation.

Keep outside QM Core:

- consent/document acceptance logic,
- test/session/scoring data,
- booking/calendar logic,
- invoices and billing records,
- training/course domain data,
- fine-grained product authorization,
- product-specific audit trails.

Primary QManufacture consumers include Zgodomat, VerifiTest, Booking and future products. External clients may consume the same contract without becoming part of QM Core.

## Engineering decisions

- Django + PostgreSQL + REST.
- One deployable modular Django application initially.
- Custom Django User model from the first migration.
- UUID + email-native identity.
- Use Django auth and standards-compliant libraries; never implement auth/crypto protocols from scratch.
- Cross-domain products use OIDC Authorization Code + PKCE, not shared cookies.
- Products key local external identity by OIDC `sub`, never email matching.
- Runtime roles/entitlements remain authoritative via API; do not freeze them into long-lived token claims.
- Minimal coarse roles exist from the start; fail closed without valid membership/role.
- No microservices or GraphQL without a concrete requirement.
- No Google Cloud dependency.
- Social login remains optional future work.
- Account linking requires a verified flow, never email matching alone.

## Security and data

- Enforce tenant/organization boundaries consistently and test cross-tenant isolation.
- Use least privilege and explicit OAuth scopes.
- Store only identity/access data necessary for this core.
- Never log or commit secrets, tokens, credentials, RSA private keys or local environment data.
- Keep authorization decisions deterministic and testable.

## Documentation

Changes to identity model, tenant boundaries, public API contracts, OIDC behavior or domain ownership must update `README.md`, `PROJECT_STATE.md`, `docs/ARCHITECTURE.md` and, when product integration changes, `docs/IDENTITY_INTEGRATION.md`.

## Validation

Run only real repository test/lint commands. Do not invent tooling that has not been added.

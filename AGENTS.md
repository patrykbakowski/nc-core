# AGENTS.md

## Purpose

This repository is NC Core / NC ID, the shared identity/access foundation for independent applications.

Read `docs/ARCHITECTURE.md` and `PROJECT_STATE.md` before implementation changes.

## Hard boundaries

NC Core owns:

- custom user identity,
- organizations,
- memberships,
- coarse roles/permissions,
- product entitlements,
- authentication/service authentication,
- audit identity/correlation.

Keep outside NC Core:

- consent/document acceptance logic,
- test/session/scoring data,
- booking/calendar logic,
- invoices and billing records,
- Course/Enrollment/Material,
- BUR workflow logic,
- fine-grained product authorization,
- product-specific audit trails.

## Engineering decisions

- Django + PostgreSQL + REST.
- One deployable modular Django application initially.
- Custom Django User model from the first migration.
- Use Django authentication/session primitives; do not implement auth/crypto protocols from scratch.
- Minimal coarse roles exist from the start; fail closed without valid membership/role.
- No microservices or GraphQL without a concrete requirement.
- Social login/SSO is later work; do not add a Google Cloud dependency.
- Account linking requires a verified flow, never email matching alone.

## Security and data

- Enforce tenant/organization boundaries consistently and test cross-tenant isolation.
- Use least privilege.
- Store only identity/access data necessary for this core.
- Never log or commit secrets, tokens, credentials or local environment data.
- Keep authorization decisions deterministic and testable.

## Documentation

Changes to identity model, tenant boundaries, public API contracts or domain ownership must update `README.md`, `PROJECT_STATE.md` and `docs/ARCHITECTURE.md`.

## Validation

Run only real repository test/lint commands. Do not invent tooling that has not been added.

# NC Core — Project State

**Updated:** 2026-09-23  
**Status:** READY / NC ID architecture approved; implementation gated by a real consumer

## Purpose

Provide shared NC ID identity/access capabilities for independent products.

## Current decisions

- Stack: Django + PostgreSQL + REST.
- One deployable modular Django application; no microservices for MVP.
- Custom Django User model from the first migration.
- Minimal roles exist from Stage 1 and access fails closed without a valid role.
- NC Core owns users, organizations, memberships, coarse roles, product entitlements, auth and audit identity/correlation.
- Fine-grained product authorization stays in each product.
- Product-specific audit trails stay in each product.
- Course, Enrollment and Material are explicitly outside NC Core.
- Social login/SSO is later work; no Google Cloud dependency.
- Account linking must use a verified flow, never email-match-only.
- `docs/ARCHITECTURE.md` was reviewed and merged to `main`.
- Preferred development flow: `ai-orchestrator` → Cursor → PR → review/CI.

## Outside the core

- Zgodomat consent/document records
- VerifyTest test data and scoring
- Booking appointments/availability
- billing/accounting
- Neuroconnect Course/Enrollment/Material and BUR workflows

## Portfolio priority

The project is separated organizationally, but coding should not start just because the repository exists. Start implementation when a real consuming product and minimal API contract are identified.

## Next steps

1. Choose the first real consumer and define the minimal REST contract.
2. Scaffold the Django project with custom User + PostgreSQL.
3. Implement Organization, Membership and coarse roles from the start.
4. Add migrations and tenant-isolation tests.
5. Integrate one real consumer without rewriting the existing Neuroconnect staging from scratch.

# NC Core

Shared identity and access foundation for the Neuroconnect application ecosystem.

## Goal

Provide a small, stable core that lets independent applications work together without turning them into one monolith.

The core is intended to own identity and access concepts such as:

- users
- organizations
- memberships
- roles and permissions
- product access / entitlements
- API authentication
- audit identity

## Product boundaries

NC Core should answer questions such as:

- Who is this user?
- Which organization do they belong to?
- What role do they have?
- Which products may they access?
- Which identity performed an audited action?

NC Core should NOT own product-specific business data.

Examples that belong elsewhere:

- consent records and document acceptance -> Zgodomat
- tests, sessions, answers and scoring -> VerifyTest
- appointments and availability -> Booking
- invoices and payment accounting -> billing
- BUR training operations -> Neuroconnect & BUR

## Architecture principle

Independent products may be sold and deployed separately, but should be able to participate in one shared ecosystem through stable identity and authorization contracts.

Do not turn NC Core into a catch-all backend.

## Status

Repository initialized. Implementation stack and API contract are not frozen yet.

See `PROJECT_STATE.md` for current status.

# NC Core — Project State

## Status

Initialized. Architecture boundaries defined; implementation not started.

## Purpose

Provide shared identity, organization, role, entitlement and audit-identity capabilities for Neuroconnect-related applications.

## Current domain

NC Core should own:

- users
- organizations
- memberships
- roles / permissions
- product entitlements
- API authentication
- audit identity

## Explicitly outside the core

- Zgodomat consent/document records
- VerifyTest test definitions, sessions, answers and scoring
- Booking appointments and availability
- billing/accounting
- BUR operational workflows

## Architectural intent

Zgodomat, VerifyTest and Booking should remain independent products that can work alone or participate in a shared ecosystem through NC Core.

## Open decisions

- implementation stack
- authentication mechanism
- external API contract
- tenant model details
- entitlement model
- deployment topology

## Next steps

1. Define domain model and boundaries in more detail.
2. Decide the smallest viable authentication/authorization architecture.
3. Define API contracts required by the first consuming product.
4. Only then create the implementation scaffold.

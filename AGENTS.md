# AGENTS.md

## Purpose

This repository is the shared identity/access core for the Neuroconnect application ecosystem.

## Hard boundaries

NC Core owns identity and access concerns only.

Allowed core concepts include:

- user identity
- organizations
- memberships
- roles and permissions
- product entitlements
- API authentication
- audit identity

Do not move product-specific business logic into this repository.

In particular, keep these outside NC Core:

- consent/document acceptance logic
- psychological or assessment test data
- booking/calendar logic
- invoices and billing records
- BUR workflow logic

## Engineering principles

- Prefer KISS and minimal architecture.
- Do not introduce microservices unless a real boundary requires them.
- Keep public contracts stable and explicit.
- Prefer additive changes over breaking changes.
- Enforce tenant/organization boundaries consistently.
- Use least-privilege authorization.
- Treat authentication, authorization and audit identity as security-sensitive code.
- Never log or expose secrets or credentials.
- Never commit secrets, tokens, passwords or local environment data.

## Data and privacy

- Store only data necessary for identity/access responsibilities.
- Do not duplicate product-owned sensitive data into the core for convenience.
- Audit security-relevant actions without logging secret material.
- Keep authorization decisions deterministic and testable.

## Validation

No canonical implementation stack or test command is defined yet.

Before adding tooling, inspect the current repository and use only real project commands. Do not invent framework conventions or test commands before the stack is chosen.

## Documentation

Any change to domain boundaries, identity model, authorization model or external API contract must be reflected in `README.md` and `PROJECT_STATE.md`.

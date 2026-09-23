# NC Core Architecture

## Purpose

NC Core is the shared identity and access infrastructure for the Neuroconnect ecosystem. It provides a stable foundation for independent products (Zgodomat, VerifyTest, Booking) to authenticate users, enforce organization boundaries, manage roles and permissions, and audit security-relevant actions.

## Core Principle

**NC Core is infrastructure, not a product backend.**

It answers identity and access questions. It does NOT own product business logic or data.

## Domain Model

### User

- **UserId** (primary identifier)
- Basic profile: email, name, phone (optional)
- Authentication credentials (hashed passwords, OAuth tokens, MFA secrets)
- Account status: active, suspended, deleted
- Created/updated timestamps

**Owned by NC Core.** Product-specific profile data (consent history, test results, booking preferences) stays in respective products.

### Organization

- **OrganizationId** (primary identifier)
- Name, display name
- Organization type: clinic, practice, enterprise, individual
- Tenant isolation boundary
- Status: active, suspended, deleted
- Created/updated timestamps

**Owned by NC Core.** Product-specific organization data (billing details, clinic branding, test configurations) stays in respective products.

### Membership

- **MembershipId**
- UserId + OrganizationId (a user may belong to multiple organizations)
- Role(s) within that organization
- Status: active, invited, suspended
- Invitation/acceptance metadata
- Created/updated timestamps

**Owned by NC Core.**

### Role & Permission

**Roles:**
- Predefined system roles: `org:admin`, `org:member`, `org:viewer`
- Product-scoped roles: `zgodomat:editor`, `verifytest:psychologist`, `booking:scheduler`

**Permissions:**
- Action-based: `user:read`, `user:write`, `member:invite`, `entitlement:grant`
- Product-scoped: `zgodomat:consent:view`, `verifytest:test:administer`, `booking:appointment:create`

**Model:**
- Role = named collection of permissions
- Roles assigned per membership (organization context)
- Permissions enforced at API/service layer

**Owned by NC Core.** Product-specific authorization logic (e.g., "may edit this specific consent document") is evaluated by the product using NC Core identity context.

### Product Entitlement

- **EntitlementId**
- OrganizationId
- ProductId: `zgodomat`, `verifytest`, `booking`
- Plan/tier: `basic`, `professional`, `enterprise`, or custom
- Feature flags: optional JSON blob for product-specific toggles
- Valid from/until (subscription period)
- Status: active, expired, suspended

**Owned by NC Core.** Billing transactions, invoices, payment methods remain in the billing system. NC Core reflects the entitlement state only.

### API Authentication Token

- **TokenId**
- UserId + OrganizationId (scope)
- Token type: `session`, `api_key`, `service_account`
- Token hash (never store plaintext)
- Scopes/permissions (optional subset)
- Expiration, revocation
- Created/last-used timestamps

**Owned by NC Core.**

### Audit Identity Record

- **AuditId**
- Timestamp
- Actor: UserId or ServiceAccountId
- OrganizationId (tenant context)
- Action: `user.created`, `member.invited`, `entitlement.granted`, `role.assigned`
- Subject: affected resource (UserId, MembershipId, EntitlementId)
- Metadata: IP, user-agent, request context (non-secret only)

**Owned by NC Core.** Product-specific audit trails (e.g., "consent document viewed") are owned by respective products but may reference NC Core identities.

## Data Ownership Boundaries

| Concern                              | Owner         |
|--------------------------------------|---------------|
| User identity, credentials, MFA      | **NC Core**   |
| Organizations, memberships, roles    | **NC Core**   |
| Product entitlements                 | **NC Core**   |
| API tokens, authentication           | **NC Core**   |
| Audit identity (who did what)        | **NC Core**   |
| Consent documents, acceptance logs   | Zgodomat      |
| Psychological tests, sessions, scores| VerifyTest    |
| Appointments, availability, calendar | Booking       |
| Invoices, payments, accounting       | Billing       |
| BUR training workflows               | Neuroconnect  |

## Architecture

### Topology

**Single-service application.**

NC Core is deployed as one conventional web application with:
- HTTP API (REST or GraphQL)
- Relational database (PostgreSQL recommended)
- Optional read replica for high query load

**No microservices** unless real operational boundaries demand them (e.g., separating audit write path for compliance isolation). Start simple.

### Integration Contract

Products integrate with NC Core via:

1. **Authentication API** — verify tokens, retrieve user identity and organization context
2. **Authorization API** — check permissions, retrieve roles and entitlements
3. **Management API** — create users, invite members, grant roles, manage entitlements (admin operations)
4. **Audit API** — write audit records for cross-product actions (optional)

**Example flow:**

```
User → Zgodomat frontend → Zgodomat backend
                               ↓
                         NC Core API: verify token
                               ↓
                         returns: { userId, orgId, roles, entitlements }
                               ↓
                         Zgodomat: enforce product logic
```

NC Core does NOT call product APIs. Products call NC Core.

### Tenant Boundaries

**OrganizationId is the tenant isolation key.**

- All queries MUST filter by OrganizationId.
- Multi-tenant database: single schema, row-level tenant enforcement.
- No cross-tenant data leakage in queries or APIs.
- Service accounts may have multi-org scope (for admin operations only).

### Authentication Options

**Phase 1 (MVP):**
- Username/password with bcrypt
- Session tokens (HTTP-only cookies or Bearer tokens)
- Optional: email-based password reset

**Phase 2:**
- OAuth 2.0 / OpenID Connect (support external IdPs: Google, Microsoft, custom SAML)
- Multi-factor authentication (TOTP)

**Phase 3:**
- API keys for service-to-service
- Refresh tokens
- SSO for enterprise customers

**Decision:** Do not lock into a cloud provider's identity service (e.g., Firebase Auth, AWS Cognito). Keep authentication portable. Consider open-source options (e.g., Keycloak, Ory, self-hosted OAuth) or implement standard flows in-app.

**Avoid:** Google Cloud-specific dependencies.

### Authorization Model

**Least-privilege by default.**

- Users see only their own organizations.
- Organization members see only their organization's data.
- Roles grant incremental permissions.
- Products enforce fine-grained rules (e.g., "edit only your own consent documents") using NC Core context.

**Enforcement layers:**

1. **API gateway** — verify token, load identity context
2. **Service layer** — check organization membership and role permissions
3. **Product layer** — apply product-specific rules

### Data Retention & Privacy

- Store only identity/access data; never duplicate product data.
- Support GDPR/RODO: user deletion cascades to memberships, tokens, audit logs (anonymize or delete per policy).
- Audit logs: retain for compliance period, anonymize after user deletion.

## Proposed Directory Structure

Assuming a conventional server-side web application (stack TBD):

```
nc-core/
├── docs/
│   ├── ARCHITECTURE.md       (this file)
│   ├── API.md                (API contract spec)
│   └── DEPLOYMENT.md         (deployment guide)
├── src/
│   ├── domain/
│   │   ├── user/
│   │   ├── organization/
│   │   ├── membership/
│   │   ├── role/
│   │   ├── entitlement/
│   │   ├── auth/             (authentication, token management)
│   │   └── audit/
│   ├── api/
│   │   ├── http/             (REST/GraphQL routes)
│   │   └── middleware/       (auth, tenant context)
│   ├── storage/
│   │   ├── migrations/
│   │   └── repositories/     (data access layer)
│   ├── service/              (business logic, orchestration)
│   └── config/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── migrations/               (database schema versions)
├── scripts/                  (setup, seed, admin tools)
├── README.md
├── AGENTS.md
├── PROJECT_STATE.md
└── [build config, dependencies]
```

Adapt to chosen stack. Key principle: separate domain logic from API and storage.

## MVP Sequence

### Stage 0: Foundation (current)
- ✅ Define boundaries and architecture
- ✅ Document domain model

### Stage 1: Minimal Identity
**Goal:** One product (e.g., Zgodomat) can authenticate users.

Implement:
- User entity (id, email, password hash, name, status)
- Organization entity (id, name, status)
- Membership entity (user + org)
- Basic authentication API: `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`
- Session token management
- Database schema + migrations
- Tenant-aware queries (enforce organizationId filter)

**Defer:**
- Roles, permissions (everyone is admin in their org)
- Entitlements (assume all products enabled)
- MFA, OAuth
- Audit logging

### Stage 2: Roles & Permissions
**Goal:** Distinguish admins from members.

Add:
- Role entity (predefined: `org:admin`, `org:member`, `org:viewer`)
- Permission checks in API middleware
- Membership role assignment
- API: `GET /orgs/{orgId}/members`, `POST /orgs/{orgId}/members/invite`, `PUT /members/{id}/role`

**Defer:**
- Fine-grained product-scoped roles
- Custom roles

### Stage 3: Entitlements
**Goal:** Products check which features are enabled per organization.

Add:
- Entitlement entity (orgId, productId, plan, valid dates)
- API: `GET /orgs/{orgId}/entitlements`, `POST /admin/entitlements` (admin-only grant)
- Products query entitlements before allowing access

**Defer:**
- Automatic billing integration
- Feature flag granularity

### Stage 4: Audit & Security Hardening
**Goal:** Track who did what, harden authentication.

Add:
- Audit record entity
- Audit API: `POST /audit/record` (called by products)
- MFA (TOTP)
- API key support for service-to-service
- Rate limiting, brute-force protection

### Stage 5: External IdP & SSO
**Goal:** Enterprise customers use their own identity providers.

Add:
- OAuth 2.0 / OIDC client support
- SAML integration (optional)
- Account linking (external IdP user → NC Core user)

### Stage 6: Advanced Authorization
**Goal:** Fine-grained, product-scoped roles and permissions.

Add:
- Custom roles (define permission sets per organization)
- Product-scoped permissions (`zgodomat:consent:view`, etc.)
- Permission inheritance and delegation

## Decision Points

| Decision                     | Recommendation                          | Status      |
|------------------------------|-----------------------------------------|-------------|
| Implementation stack         | TBD (consider: Node.js, Python, Go, Elixir) | Open    |
| Database                     | PostgreSQL (proven, tenant-safe)        | Open        |
| API style                    | REST (simple) or GraphQL (flexible)     | Open        |
| Authentication library       | Standard JWT + bcrypt, or Ory/Keycloak  | Open        |
| Deployment                   | Docker + managed DB, or PaaS            | Open        |
| Avoid                        | Google Cloud lock-in, microservices     | **Decided** |

## Integration Example

### Zgodomat authenticates a user:

1. User submits login form to Zgodomat frontend.
2. Zgodomat backend calls `POST /auth/login` on NC Core with email + password.
3. NC Core verifies credentials, returns session token + user/org context.
4. Zgodomat stores token, includes it in subsequent API requests.
5. Zgodomat calls `GET /auth/me` on NC Core to retrieve current user/org/roles.
6. Zgodomat enforces its own business rules (e.g., "may edit consent document X") using NC Core identity context.

### VerifyTest checks entitlement:

1. User accesses VerifyTest.
2. VerifyTest backend verifies token via NC Core.
3. VerifyTest calls `GET /orgs/{orgId}/entitlements?product=verifytest`.
4. NC Core returns entitlement record: `{ plan: "professional", features: [...] }`.
5. VerifyTest allows or denies access to premium features accordingly.

## Security Considerations

- **Never log plaintext passwords, tokens, or credentials.**
- Hash passwords with bcrypt (cost factor ≥ 12).
- Use HTTPS for all API communication.
- Rotate secrets (database passwords, JWT signing keys) regularly.
- Enforce rate limits on authentication endpoints.
- Implement account lockout after N failed login attempts.
- Audit all privilege escalation actions (role grants, entitlement changes).

## Conclusion

This architecture keeps NC Core minimal, focused, and infrastructure-scoped. It avoids premature complexity (no microservices, no vendor lock-in) while providing a stable foundation for independent products to share identity and access.

**Next steps:**
1. Choose implementation stack.
2. Implement Stage 1 (minimal identity).
3. Define REST API contract in `docs/API.md`.
4. Build database schema and migrations.
5. Integrate with first product (Zgodomat).

Keep it simple. Iterate based on real product needs.

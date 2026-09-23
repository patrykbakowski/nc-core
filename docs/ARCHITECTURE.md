# QM Core / QM Identity Architecture

## Naming

QManufacture owns the shared technical foundation.

- **QM Core** — shared identity/access foundation.
- **QM Identity** — identity/authentication module inside QM Core.
- **NC Platform** — separate Neuroconnect training application and a consumer of QM Core.
- **NC Core** and **NC ID** — deprecated architecture names. The repository remains named `patrykbakowski/nc-core` for continuity only.

## Purpose

QM Core is the shared identity and access infrastructure for QManufacture products and external clients such as Neuroconnect NC Platform. It owns users, organizations, memberships, coarse roles/permissions, product entitlements, API authentication and audit identity correlation.

**QM Core is infrastructure, not a product backend.** It does NOT own product business logic or data.

## Implementation Stack

**Django + PostgreSQL.**

KISS favors a small, reusable identity/access foundation. REST API. No GraphQL in MVP. No microservices.

## Domain Model

### User
- Identity: email (unique), name, phone (optional)
- Account status: active, suspended, deleted
- **Custom Django User model from first migration** (use `AbstractBaseUser` or `AbstractUser`)
- Django authentication machinery (password hashing, sessions, permissions)

### Organization
- Name, display name, organization type
- Tenant isolation boundary
- Status: active, suspended, deleted

### Membership
- User belongs to Organization with Role
- Status: active, invited, suspended
- Invitation metadata

### Role & Permission
**Coarse roles owned by QM Core:**
- `org:owner` — full control, transfer ownership
- `org:admin` — manage organization, members, entitlements
- `org:member` — access organization resources
- `org:viewer` — read-only access

**Fine-grained authorization stays in products.** Products define and enforce their own rules (e.g., "may edit consent document X") using QM Identity context. Products MAY pass opaque scopes (e.g., `zgodomat:editor`) to QM Core for storage, but QM Core does not interpret them.

### Product Entitlement
- OrganizationId + ProductId (`zgodomat`, `verifytest`, `booking`, `neuroconnect-training`)
- Plan/tier, valid from/until, status
- Products query entitlements before granting access

### API Authentication
Django sessions initially. API keys for service-to-service added later. OAuth/OIDC providers prepared for SSO but not implemented in MVP.

**Do not implement crypto/token/OAuth protocols from scratch.** Use Django auth and standards-compliant libraries when SSO is added.

### Audit Identity
QM Core logs identity/access changes: user created, member invited, role assigned, entitlement granted. Provides actor/tenant correlation (who, which org, when).

**Product-specific audit trails stay in products** (e.g., "consent document viewed"). QM Core is not a dumping ground for all product events.

## Data Ownership Boundaries

| Concern                              | Owner         |
|--------------------------------------|---------------|
| User identity, credentials           | **QM Core / QM Identity** |
| Organizations, memberships, roles    | **QM Core**   |
| Product entitlements                 | **QM Core**   |
| Authentication, sessions, API keys   | **QM Identity** |
| Audit: identity/access actions       | **QM Core**   |
| Consent documents, acceptance logs   | Zgodomat      |
| Tests, sessions, answers, scoring    | VerifyTest    |
| Appointments, availability           | Booking       |
| Invoices, payments                   | Billing       |
| Training courses, enrollments        | Neuroconnect NC Platform |

**Explicit boundary:** Neuroconnect training domain (Course, CourseSession, Enrollment, Material) is NOT QM Core.

## Consumers

QM Core is consumed by:

- Zgodomat,
- VerifyTest,
- Booking,
- Neuroconnect NC Platform,
- future QManufacture products with a genuine shared identity/access requirement.

Each consumer remains independently deployable/sellable at product level and keeps its domain data outside QM Core.

## Integration Contract

Products call QM Core REST API:

1. **Authentication** — `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`
2. **Authorization** — `GET /orgs/{orgId}/members/me/roles`, `GET /orgs/{orgId}/entitlements`
3. **Management** — `POST /orgs/{orgId}/members/invite`, `PUT /members/{id}/role`, `POST /admin/entitlements`

**Example:**

```
User → Zgodomat → QM Core: GET /auth/me
                    ← { userId, orgId, roles: ["org:member"], entitlements: [{product: "zgodomat", plan: "professional"}] }
Zgodomat enforces its own rules using this context.
```

QM Core does NOT own or orchestrate product business workflows.

## Tenant Boundaries

**OrganizationId enforces tenant isolation.**

- Django middleware loads tenant context from authenticated user
- Views/APIs enforce organization membership before data access
- Test suite includes multi-tenant isolation tests
- Service accounts may span orgs (admin operations only)

**Avoid simplistic claims.** Not every query in every product literally filters `OrganizationId`. The principle: enforce tenant context consistently, test isolation, prevent cross-tenant leakage.

## Authentication Phases

**MVP (Phase 1):**
- Custom Django User model, password hashing (PBKDF2 default)
- Django sessions (HTTP-only cookies)
- Email/password login, logout
- Password reset via email

**Phase 2:**
- API keys (Django REST Framework tokens or custom)
- Multi-factor authentication (django-otp)

**Phase 3:**
- External IdP via OAuth/OIDC
- SAML for enterprise SSO
- **Account linking requires verified linking flow** — never link solely because emails match

**Prepared but not now:** Social login (Google, Microsoft). No Google Cloud dependency.

## Django Application Structure

One deployable modular Django project:

```
nc_core/                 # legacy repository/package name may remain during migration
├── manage.py
├── nc_core/
│   ├── settings/
│   ├── urls.py
│   └── wsgi.py
├── users/               # QM Identity
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   └── tests.py
├── organizations/
│   ├── models.py
│   ├── views.py
│   └── tests.py
├── entitlements/
│   ├── models.py
│   └── views.py
├── audit/
│   ├── models.py
│   └── views.py
├── api/
│   ├── v1/
│   ├── middleware.py
│   └── permissions.py
└── tests/
```

Standard Django conventions. Django REST Framework for API. PostgreSQL database.

## MVP Sequence

### Stage 1: Minimal Identity & Roles
- Custom User model (from first migration)
- Organization, Membership, Role models
- Coarse roles: `org:owner`, `org:admin`, `org:member` (fail closed if no role)
- Django auth: login, logout, session management
- REST API: `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`
- Tenant context middleware enforces organization membership
- Permission checks in API views
- Member invitation API
- One real consumer can authenticate users
- **Defer:** Entitlements (assume all products enabled), MFA, opaque product-scoped roles

### Stage 2: Entitlements
- Entitlement model (orgId, productId, plan, valid dates)
- REST API: `GET /orgs/{orgId}/entitlements`, `POST /admin/entitlements`
- Products query before granting access
- **Defer:** Billing integration, feature flags

### Stage 3: Audit & Hardening
- AuditRecord model (actor, org, action, subject, timestamp)
- Audit log API (internal, products may write correlation events)
- Rate limiting
- Account lockout after failed logins
- **Defer:** MFA

### Stage 4: API Keys & Service Auth
- API key model/tokens for service-to-service
- Django REST Framework TokenAuthentication or custom
- **Defer:** OAuth/OIDC

### Stage 5: External IdP & SSO
- OAuth/OIDC client
- SAML for enterprise
- Verified account linking flow
- **Defer:** Advanced MFA options

## Security Notes

- Use Django's built-in password hashing
- HTTPS required for production
- Django's CSRF protection enabled
- Secrets in environment variables, never committed
- Rotate database credentials and SECRET_KEY according to operational policy
- Multi-tenant isolation tests in CI
- Audit all privilege escalation (role grants, entitlement changes)

## Next Steps

1. Select the first real consumer and define the minimal API contract.
2. Initialize Django project with custom User model and PostgreSQL.
3. Implement Stage 1 (minimal identity with roles from start).
4. Define REST API contract in `docs/API.md`.
5. Write database migrations and tenant-isolation tests.
6. Integrate the selected consumer.
7. Deploy to staging.

Keep it practical. Build for real product needs, not generic IAM abstractions.

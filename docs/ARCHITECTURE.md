# NC Core Architecture

## Purpose

NC Core is the shared identity and access infrastructure for the Neuroconnect ecosystem. It owns users, organizations, memberships, coarse roles/permissions, product entitlements, API authentication and audit identity correlation.

**NC Core is infrastructure, not a product backend.** It does NOT own product business logic or data.

## Implementation Stack

**Django + PostgreSQL.**

Neuroconnect already uses Django/PostgreSQL. KISS favors reuse. REST API. No GraphQL in MVP. No microservices.

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
**Coarse roles owned by NC Core:**
- `org:owner` — full control, transfer ownership
- `org:admin` — manage organization, members, entitlements
- `org:member` — access organization resources
- `org:viewer` — read-only access

**Fine-grained authorization stays in products.** Products define and enforce their own rules (e.g., "may edit consent document X") using NC Core identity context. Products MAY pass opaque scopes (e.g., `zgodomat:editor`) to NC Core for storage, but NC Core does not interpret them.

### Product Entitlement
- OrganizationId + ProductId (`zgodomat`, `verifytest`, `booking`)
- Plan/tier, valid from/until, status
- Products query entitlements before granting access

### API Authentication
Django sessions initially. API keys for service-to-service added later. OAuth/OIDC providers prepared for SSO but not implemented in MVP.

**Do not implement crypto/token/OAuth protocols from scratch.** Use Django auth, standards-compliant libraries (e.g., `django-oauth-toolkit`, `social-auth-app-django`) when SSO is added.

### Audit Identity
NC Core logs identity/access changes: user created, member invited, role assigned, entitlement granted. Provides actor/tenant correlation (who, which org, when).

**Product-specific audit trails stay in products** (e.g., "consent document viewed"). NC Core is not a dumping ground for all product events.

## Data Ownership Boundaries

| Concern                              | Owner         |
|--------------------------------------|---------------|
| User identity, credentials           | **NC Core**   |
| Organizations, memberships, roles    | **NC Core**   |
| Product entitlements                 | **NC Core**   |
| Authentication, sessions, API keys   | **NC Core**   |
| Audit: identity/access actions       | **NC Core**   |
| Consent documents, acceptance logs   | Zgodomat      |
| Tests, sessions, answers, scoring    | VerifyTest    |
| Appointments, availability           | Booking       |
| Invoices, payments                   | Billing       |
| Training courses, enrollments        | Neuroconnect  |

**Explicit boundary:** Neuroconnect training domain (Course, Enrollment, Material) is NOT NC Core.

## Integration Contract

Products call NC Core REST API:

1. **Authentication** — `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`
2. **Authorization** — `GET /orgs/{orgId}/members/me/roles`, `GET /orgs/{orgId}/entitlements`
3. **Management** — `POST /orgs/{orgId}/members/invite`, `PUT /members/{id}/role`, `POST /admin/entitlements`

**Example:**

```
User → Zgodomat → NC Core: GET /auth/me
                    ← { userId, orgId, roles: ["org:member"], entitlements: [{product: "zgodomat", plan: "professional"}] }
Zgodomat enforces its own rules using this context.
```

NC Core does NOT call product APIs. One-way dependency.

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
- External IdP via OAuth/OIDC (django-allauth or social-auth-app-django)
- SAML for enterprise SSO
- **Account linking requires verified linking flow** — never link solely because emails match

**Prepared but not now:** Social login (Google, Microsoft). No Google Cloud dependency.

## Django Application Structure

One deployable modular Django project:

```
nc_core/
├── manage.py
├── nc_core/              (project settings)
│   ├── settings/
│   ├── urls.py
│   └── wsgi.py
├── users/                (Django app)
│   ├── models.py         (User, extended profile)
│   ├── views.py
│   ├── serializers.py
│   └── tests.py
├── organizations/        (Django app)
│   ├── models.py         (Organization, Membership, Role)
│   ├── views.py
│   └── tests.py
├── entitlements/         (Django app)
│   ├── models.py         (Entitlement)
│   └── views.py
├── audit/                (Django app)
│   ├── models.py         (AuditRecord)
│   └── views.py
├── api/                  (REST API routes, middleware)
│   ├── v1/
│   ├── middleware.py     (tenant context, auth)
│   └── permissions.py
└── tests/                (integration, e2e)
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
- One product (Zgodomat) can authenticate users
- **Defer:** Entitlements (assume all products enabled), MFA, opaque product-scoped roles

### Stage 2: Entitlements
- Entitlement model (orgId, productId, plan, valid dates)
- REST API: `GET /orgs/{orgId}/entitlements`, `POST /admin/entitlements`
- Products query before granting access
- **Defer:** Billing integration, feature flags

### Stage 3: Audit & Hardening
- AuditRecord model (actor, org, action, subject, timestamp)
- Audit log API (internal, products may write correlation events)
- Rate limiting (django-ratelimit)
- Account lockout after failed logins
- **Defer:** MFA

### Stage 4: API Keys & Service Auth
- API key model/tokens for service-to-service
- Django REST Framework TokenAuthentication or custom
- **Defer:** OAuth/OIDC

### Stage 5: External IdP & SSO
- OAuth/OIDC client (django-allauth)
- SAML for enterprise (djangosaml2 or python3-saml)
- Verified account linking flow
- **Defer:** Advanced MFA options

## Security Notes

- Use Django's built-in password hashing (PBKDF2 default, configure for Argon2 if needed)
- HTTPS required for production
- Django's CSRF protection enabled
- Secrets in environment variables, never committed
- Rotate database credentials, SECRET_KEY regularly
- Multi-tenant isolation tests in CI
- Audit all privilege escalation (role grants, entitlement changes)

## Next Steps

1. Initialize Django project with custom User model and PostgreSQL
2. Implement Stage 1 (minimal identity with roles from start)
3. Define REST API contract in `docs/API.md`
4. Write database migrations
5. Integrate with Zgodomat
6. Deploy to staging environment

Keep it practical. Build for real product needs, not generic IAM abstractions.

# 17 — Security and Privacy

**Purpose:** Specify multi-tenant isolation, authentication, RBAC, encryption, audit logging and data retention controls required for commercially sensitive bioprocess IP.
**Related:** [05_SYSTEM_ARCHITECTURE.md](05_SYSTEM_ARCHITECTURE.md) · [07_DATABASE_SCHEMA.md](07_DATABASE_SCHEMA.md) · [08_API_SPECIFICATION.md](08_API_SPECIFICATION.md)

---

## 1. Security baseline (CONFIRMED `[BP p.10, p.15]`)
> Use organization-level data isolation, role-based access, encryption in transit and at rest, backup and recovery, audit logging and customer-controlled data retention. Consider private-cloud or on-premise deployment for confidential process data.

Explicitly out of scope for MVP `[BP p.5]`: claims of 21 CFR Part 11 compliance or GMP validation.

## 2. Organization-level data isolation
- Every tenant table carries `organization_id uuid NOT NULL`.
- Every repository query requires an explicit `org_id` argument derived from the verified `X-Organization-Id` header and checked against `memberships`.
- Cross-organization resource requests return `404 NOT_FOUND` (never `403`, to prevent UUID enumeration).
- Object storage keys are prefixed with `orgs/{organization_id}/...`.

## 3. Authentication (PROPOSED)
- Passwords hashed with `argon2id` (`argon2-cffi`).
- Short-lived JWT access token (15 min expiry, HS256/RS256) + rotating refresh token stored hashed in `refresh_tokens`.
- Dev/test seed users created only via explicit CLI seed script, never hardcoded in application logic.

## 4. Role-Based Access Control (RBAC) matrix (PROPOSED, **OQ-021**)

| Capability | `viewer` | `scientist` | `reviewer` | `org_admin` |
|---|:---:|:---:|:---:|:---:|
| View projects, passports, batches, vessels, assessments, reports | Yes | Yes | Yes | Yes |
| Create/edit projects, passport versions, vessels, scenarios | No | Yes | No | Yes |
| Upload files, map columns, import batches | No | Yes | No | Yes |
| Run assessments, update validation task status/waivers | No | Yes | Yes | Yes |
| Record assessment review sign-off (`review_signoffs`) | No | No | Yes | Yes |
| Generate PDF transfer reports | No | Yes | Yes | Yes |
| Manage org members, roles, archive projects, view audit log | No | No | No | Yes |

## 5. Audit logging & data protection
- Append-only `audit_events` table logs authentication events, membership changes, project/passport creations, batch imports, vessel version creations, assessment executions, task waivers, review sign-offs, and report downloads.
- Application logs never log raw file contents, measurement arrays, passwords, or tokens.
- File uploads validated for extension (`.csv`, `.xlsx`), MIME type, size limit (`MAX_UPLOAD_MB`, default 50 MB), and streamed with SHA-256 verification.

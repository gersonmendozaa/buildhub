# API contract

## 1. Style and versioning

- JSON REST API rooted at `/api/v1`; server-rendered pages use the same domain services.
- OpenAPI is generated in CI and checked for unintended breaking changes.
- UUIDs are opaque. Timestamps are RFC 3339 UTC. Dates are `YYYY-MM-DD`.
- Collection pagination is cursor-based: `data`, `next_cursor`, `has_more`.
- Mutating requests accept `Idempotency-Key`; create/invitation/admin endpoints require it.
- Resource mutations use `If-Match`/version to prevent lost updates.
- Every response carries `X-Request-ID`; logs and audit events use it.

Success envelope is the resource itself. Error envelope:

```json
{
  "error": {
    "code": "project_version_changed",
    "message": "The project changed after this invitation was sent.",
    "fields": {},
    "request_id": "01..."
  }
}
```

Do not leak existence across authorization boundaries: use `404` for an inaccessible private
resource. Validation is `422`, unauthenticated `401`, unauthorized known action `403`, stale
version `409` or `412`, rate limit `429`, and unexpected failure `500`.

## 2. Public endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/vendors` | Search/filter published vendor profiles |
| GET | `/vendors/{slug}` | Public profile, license badge/check date, score explanation |
| GET | `/vendors/{slug}/projects` | Confirmed public projects |
| GET | `/projects/{id}` | Public project detail |
| GET | `/taxonomies/categories` | Active service categories |
| GET | `/locations/counties` | Launch-enabled counties |
| GET | `/locations/counties/{id}/cities` | Valid city filter values |
| GET | `/health/live` | Process liveness only |
| GET | `/health/ready` | Dependency readiness, protected from detailed public output |

`GET /vendors` filters: `q`, `category`, `county`, `city`, `license_verified`,
`min_score`, `recent_since`, `sort`, `cursor`, `limit<=50`.

Public vendor payload includes a structured verification object:

```json
{
  "license": {
    "number": "1234567",
    "status": "active",
    "badge": "verified",
    "checked_at": "2026-09-27T10:00:00Z",
    "source": "California CSLB",
    "official_lookup_url": "https://..."
  },
  "score": {
    "value": 78.5,
    "version": "v1",
    "components": {"license": 30, "projects": 22.1, "recency": 17.4, "photos": 9}
  }
}
```

## 3. Authentication and account

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/register` | Role and consent versions required |
| POST | `/auth/login` | CSRF protected; rate limited |
| POST | `/auth/logout` | Invalidates session |
| POST | `/auth/email/verify` | Single-use token |
| POST | `/auth/password/forgot` | Constant-shape response |
| POST | `/auth/password/reset` | Rotates all sessions |
| GET/PATCH | `/me` | Own account only |
| POST | `/me/privacy-requests` | Access/delete/correct/limit/opt-out |
| GET | `/me/privacy-requests/{id}` | Own request status/download |

Browser clients use server sessions and CSRF tokens, not tokens in local storage. Future
native clients should use OAuth authorization code + PKCE rather than reusing cookie APIs.

## 4. Vendor endpoints

All paths require active vendor membership for the organization.

| Method | Path | Purpose |
|---|---|---|
| POST | `/vendor-organizations` | Create organization and owner membership |
| GET/PATCH | `/vendor-organizations/{id}/profile` | Draft/published profile management |
| PUT | `/vendor-organizations/{id}/categories` | Replace category set |
| PUT | `/vendor-organizations/{id}/service-areas` | Replace validated county/city set |
| POST | `/vendor-organizations/{id}/license-claims` | Claim normalized CSLB license |
| GET | `/vendor-organizations/{id}/license-claims/current` | State, source check, review needs |
| POST | `/vendor-organizations/{id}/projects` | Create project draft |
| GET | `/vendor-organizations/{id}/projects` | Own projects in all states |
| GET/PATCH | `/vendor-organizations/{id}/projects/{project_id}` | Edit with version check |
| POST | `/.../projects/{project_id}/submit-verification` | Freeze version and send invite |
| POST | `/.../projects/{project_id}/publish` | Requires current confirmation |
| DELETE | `/.../projects/{project_id}` | Soft delete/withdraw |

## 5. Upload protocol

1. `POST /media/uploads` with intended use, filename, declared MIME, and bytes.
2. Server authorizes quota and returns asset ID plus short-lived presigned upload data.
3. Browser uploads directly to the private raw bucket.
4. `POST /media/uploads/{id}/complete` verifies object metadata and queues processing.
5. Client polls `GET /media/{id}` or receives server-rendered status updates.
6. Ready asset is attached with `POST /projects/{id}/media` and kind/order/caption.

Presign conditions bind bucket/key, max bytes, MIME allowlist, checksum, and short expiry.
The client-provided MIME is never trusted. Asset URLs are not accepted from arbitrary hosts.

## 6. Homeowner verification

| Method | Path | Purpose |
|---|---|---|
| GET | `/verification-invitations/{token}` | Minimal preview; token exchanged after auth |
| POST | `/verification-invitations/{token}/claim` | Bind invited email to authenticated user |
| GET | `/me/project-verifications` | Pending and completed items |
| POST | `/projects/{id}/verification-decisions` | Confirm/reject/request correction |

Decision body includes `project_material_version`, decision, reason code, optional private
note, and idempotency key. Confirmation fails if the project version or invite state changed.

## 7. Moderation and admin

| Method | Path | Purpose |
|---|---|---|
| POST | `/reports` | Authenticated user reports public content |
| GET | `/admin/license-reviews` | Filterable exception queue |
| POST | `/admin/license-reviews/{claim_id}/decisions` | Structured decision and reason |
| GET | `/admin/moderation` | Content report queue |
| POST | `/admin/moderation/{report_id}/actions` | Allow/hide/remove/restore/restrict |
| GET | `/admin/imports` | CSLB import health and counts |
| POST | `/admin/imports/{id}/reprocess` | Safe, idempotent parser replay |
| GET | `/admin/audit-events` | Privileged, filtered audit view |

Admin list exports require step-up authentication, narrow filters, an explicit purpose,
watermarking, short-lived signed download, and an audit event.

## 8. Rate-limit baseline

Apply limits by normalized account plus privacy-preserving IP prefix, with WAF edge limits
and application-level action limits. Initial values are tuning defaults:

- login/password/email verification: 5 attempts per 15 minutes per account/IP;
- account registration: 5/hour/IP prefix;
- project verification send: 3/day/project and 10/day/vendor;
- verification decision: 10/hour/user;
- uploads: 100 objects/day/vendor plus byte quota;
- public search: 120/minute/client, lower for obvious automation;
- admin actions: no bulk endpoint without explicit separate authorization.

Return `Retry-After`. Limits do not replace abuse monitoring or account lock review.

## 9. Phase 2 API namespaces

Reserve, but do not expose: `/quote-requests`, `/quotes`, `/conversations`, `/messages`,
`/contracts`, `/milestones`, `/payments`, `/stripe/webhooks`, and `/disputes`. Publish a
separate reviewed contract when Phase 2 begins; do not guess the funds-flow API now.

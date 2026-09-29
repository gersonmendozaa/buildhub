# Product specification

## 1. Product promise

Homeowners can find Bay Area construction vendors whose California license record was
recently matched to an official CSLB source and whose displayed work was confirmed by the
associated homeowner. Vendors can establish a credible, evidence-backed portfolio.

The product must not imply that the platform guarantees workmanship, insurance coverage,
identity, or future license status. “Verified” claims always state what was checked and when.

## 2. Launch geography

Initial counties:

- San Francisco
- San Mateo
- Santa Clara
- Alameda
- Contra Costa
- Marin

Counties and cities are reference data, not free text. Vendors select one or more service
counties and may refine them to cities. A city selection is valid only under a selected
county. The schema supports statewide expansion.

## 3. Roles and permissions

| Capability | Homeowner | Vendor member | Admin |
|---|---:|---:|---:|
| Browse public vendors/projects | Yes | Yes | Yes |
| Manage own account/privacy | Yes | Yes | Yes |
| Confirm/reject associated project | Yes | No | Override with reason |
| Create vendor organization/profile | No | Yes | Yes |
| Claim license and upload evidence | No | Yes | Yes |
| Create/edit own projects | No | Yes | Yes |
| Publish a project | After confirmation only | Submit only | Moderate |
| Review license exceptions/content | No | No | Yes |
| Change score/license facts directly | No | No | No; source/hold actions only |

A user has one primary marketplace role in the MVP. Vendor membership is organization
scoped, enabling multiple staff members later. Admin access requires MFA and is never
self-service.

## 4. MVP workflows

### 4.1 Account and authentication

1. User registers with email, password, role, consent versions, and age/authority assertion.
2. System sends a single-use email verification link.
3. Unverified accounts cannot publish or confirm work.
4. Login uses secure server-side sessions. Sensitive actions require recent authentication.
5. Password reset and email change are audited; email change requires verification.

Acceptance:

- Email addresses are unique after case folding.
- Passwords are Argon2id-hashed; common/compromised password checks are enabled.
- Authentication and verification endpoints are rate limited.
- Session cookies are Secure, HttpOnly, SameSite=Lax, rotated at login, and invalidated at
  password reset.

### 4.2 Vendor onboarding and license claim

1. Vendor creates organization and draft profile.
2. Vendor enters CSLB license number, legal/business name, classifications, categories,
   contact details, and service areas.
3. Platform normalizes the license number and matches the latest successful CSLB import.
4. Exact eligible match produces `verified`; mismatch/missing data produces `needs_review`.
5. Admin may request limited documentary evidence. Documents remain private and expire
   under the retention policy.
6. Vendor may publish a profile without a verified badge only if marketplace policy allows;
   search clearly exposes license state and last check.

License claim states: `draft`, `pending_source`, `needs_review`, `verified`, `ineligible`,
`admin_hold`, `withdrawn`. All transitions carry an actor, reason code, source record,
timestamp, and previous/new value.

Acceptance:

- A license number can have only one active vendor claim unless an admin resolves a
  documented shared-license case.
- Vendor input never overwrites source facts.
- Expiration/suspension detected in a successful import removes the badge and recomputes
  the score in the same transaction/outbox cycle.
- UI shows `Last checked DATE` and an official CSLB lookup link.

### 4.3 Project creation and homeowner confirmation

1. Vendor creates a private draft with category, scope, city/county, coarse date range,
   description, and before/after images.
2. Exact street address is optional/private and never displayed. Prefer not collecting it.
3. Vendor supplies the homeowner email and attests it is used for verification with consent.
4. Platform creates a random, hashed, single-use invitation token and emails the homeowner.
5. Homeowner signs in/registers with the invited email, reviews the project, and chooses
   `confirm`, `reject`, or `request correction`.
6. Confirmation records a snapshot of the material project facts. Later material edits
   invalidate confirmation and require reconfirmation.
7. Only confirmed, moderation-cleared projects count toward score or appear publicly.

Material fields: vendor, homeowner association, category, scope, city/county, start/end
dates, and the published before/after asset set. Copy-only typo fixes may be nonmaterial but
must still be audited.

Acceptance:

- Vendor cannot confirm its own project or see the homeowner's platform activity.
- Invitation expires after 14 days and may be revoked/resend-limited.
- Confirmation uses a compare-and-set version to prevent confirming changed content.
- Public project pages reveal no homeowner name, email, street address, EXIF, or private
  invitation details.
- Rejection and correction reason text is private to vendor, homeowner, and admins.

### 4.4 Media

Allowed MVP types: JPEG, PNG, WebP, and HEIC if the processor safely supports it. Reject
animated images and file/type mismatches. Suggested limits: 15 MB/object, 30 megapixels,
20 images/project, and 10 projects/day/vendor pending abuse tuning.

Pipeline states: `reserved`, `uploaded`, `scanning`, `rejected`, `processing`, `ready`,
`published`, `deleted`. Processing validates magic bytes, scans, fixes orientation, strips
metadata, creates responsive AVIF/WebP/JPEG derivatives, and computes a perceptual hash.

### 4.5 Search and discovery

Search fields: business/display name, categories, license classifications, city, county,
and public project text. Filters: category, county, city, verified-license-only, minimum
score, and recent verified work. Default order is score descending with deterministic
tie-breakers (`verified_project_count`, `last_verified_project_at`, `vendor_id`).

Acceptance:

- Search never exposes draft/suspended/deleted profiles or unconfirmed projects.
- Query uses indexed database predicates and returns first page within the performance SLO.
- URL contains filter state for sharing and server rendering.
- Empty and low-result states explain how filters can be broadened.

### 4.6 Deterministic vendor score

Score range is 0–100 and is a ranking signal, not a quality guarantee.

```text
score = license_component          # 0 or 30
      + project_component          # 0..35
      + recency_component          # 0..20
      + photo_component            # 0..15
```

- `license_component`: 30 only when the current claim is verified, official status is
  eligible, expiration has not passed, and no admin hold exists; otherwise 0.
- `project_component`: `35 * min(ln(1+n) / ln(21), 1)`, where `n` is confirmed, public,
  non-removed projects. This caps at 20 and reduces volume gaming.
- `recency_component`: `20 * 0.5^(days_since_latest_confirmed_end / 365)`, capped to 0..20;
  0 when there is no confirmed project.
- `photo_component`: average evidence ratio over the latest 10 confirmed public projects,
  multiplied by 15. Ratio is 1.0 with at least one ready before and after image, 0.5 with
  only one side, otherwise 0.
- Final score is rounded to one decimal. Tie-breakers are specified above.

The score row stores formula version, inputs, output, explanation JSON, source event, and
timestamp. Recompute on relevant changes and nightly as reconciliation. A product/admin
user cannot hand-edit a score. Formula changes require a new version, backfill, QA report,
and release note.

Anti-gaming controls: unique homeowner email per project/vendor pair over a configurable
period, rate limits, duplicate-image perceptual hash flags, suspicious-account review, and
admin removal with a reason. Do not automatically accuse or penalize based solely on an
LLM or heuristic flag.

### 4.7 Admin operations

MVP dashboard queues:

- license claims needing review or stale source data;
- reported profiles/projects/images;
- failed or quarantined imports and media jobs;
- suspicious duplicate project/evidence signals;
- privacy requests and account deletion jobs.

Admin actions require structured reason codes plus optional notes. High-impact actions
(admin role grants, bulk badge changes, exports, audit access) are separately logged and
alerted. Admin cannot delete audit history through the UI.

## 5. Notifications

Transactional email only for MVP: verify email, reset password, project confirmation,
verification decision, badge status change, moderation decision, and privacy request.
Every template includes support contact, reason/context, and an idempotency key. Marketing
consent is separate and defaults off.

## 6. Accessibility and responsive behavior

- Target WCAG 2.2 AA for core journeys.
- Keyboard-complete flows, visible focus, labeled inputs/errors, semantic landmarks, and
  no color-only status indicators.
- Minimum 44×44 CSS-pixel touch targets on high-frequency controls.
- Responsive images with declared dimensions; usable at 320 CSS px width and 200% zoom.
- Automated axe checks plus manual keyboard and screen-reader smoke tests before launch.

## 7. Phase 2 requirements reserved in the model

### Quotes and messaging

Homeowner opens a quote request, invites vendors, and maintains a conversation. Messages
are append-only with edit/redaction metadata. Attachments use the private media pipeline.
Abuse reporting and blocking must exist before messaging is enabled.

### Contracts, milestones, and payments

A selected quote creates a versioned contract snapshot and milestones. Stripe Connect
uses hosted onboarding and hosted/Elements collection; the platform stores only Stripe
identifiers, status, amounts, currency, and webhook events—never PAN/CVC.

“Escrow” is not a UI or legal claim until counsel and Stripe approve the exact funds flow.
Payment release must be a deterministic state machine with signed contract/change-order
records, explicit approval, configurable timeout, notice, admin hold, refunds, and an
immutable ledger. Webhooks are signature-verified, idempotent, and replayable.

California counsel must approve flows for written contracts over the applicable threshold,
down-payment limitations, progress payments, cancellation notices, change orders,
mechanics-lien notices, marketplace licensing implications, and custody/money-transmission
risk before implementation or launch.

### Disputes

A dispute freezes automatic release for affected funds, preserves evidence, assigns an
admin mediator, and records proposals/outcomes. The system must distinguish support,
mediation, chargeback, refund, and legal process. No LLM makes or recommends final outcomes.

## 8. Explicitly out of MVP

- Native iOS/Android applications
- Real-time chat, quotes, contracts, or payments
- Reviews/ratings, referrals, ads, or paid ranking
- Statewide geography and non-CSLB licenses
- Real-time CSLB guarantee
- Automated identity/background checks
- AI-generated license, legal, score, or dispute decisions

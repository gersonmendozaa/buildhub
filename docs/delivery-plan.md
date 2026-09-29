# Four-week MVP delivery plan

## 1. Delivery assumptions

Four weeks is feasible only for the stated MVP, with a small experienced delivery team and
same-day business decisions. Recommended minimum: one senior full-stack lead, one product/UI
engineer, one platform/security engineer at least half-time, QA support, a product owner,
and access to California counsel. A single generalist can create a prototype but should not
be expected to deliver and operate the described production controls safely in one month.

## 2. Week-by-week plan

### Week 0 / first two days — unblock

- Confirm product name/domain, legal entity, support contact, brand basics, categories.
- Register/confirm official CSLB data service and obtain a representative sample/export.
- Create AWS organization/accounts, GitHub organization/repository, Anthropic workspace/key,
  SES/domain verification, and paging destination.
- Counsel starts terms/privacy/verification-language review.
- Approve taxonomy, badge language, score v1, retention baseline, and admin owners.

Exit gate: CSLB acquisition route is proven against sample data, not merely assumed.

### Week 1 — foundations and vertical slice

- IaC: accounts/VPC, ECS, RDS, S3, CloudFront/WAF, secrets, logging, DNS/TLS.
- CI/CD to staging with immutable images, migrations, tests, and rollback.
- Django skeleton/modules, auth/roles, core schema, reference locations/categories.
- Responsive design system and public/vendor/homeowner navigation.
- Vertical slice: vendor draft → one project → local fake confirmation → public page.

Exit gate: staging deployment from main is repeatable; authorization test baseline passes.

### Week 2 — verification and media

- CSLB adapter, raw snapshot, validation/quarantine, normalized merge, claim state machine.
- Vendor onboarding/profile/service area/classifications.
- Direct S3 upload, scan/re-encode/EXIF strip, derivatives, CDN publication.
- Email verification and homeowner invitation/decision with immutable project snapshot.
- Audit events for authentication, license, project confirmation, moderation actions.

Exit gate: a real sample license flows end-to-end; malicious/wrong files stay unpublished.

### Week 3 — discovery and operations

- Score v1 with snapshots/explanations and reconciliation job.
- Browse/search/filter, vendor/project public pages, SEO basics, accessibility pass.
- Admin queues for claims, reports, import/media failures, and privacy requests.
- Optional Anthropic suggestions behind disabled-by-default feature flags.
- Dashboards, alarms, runbooks, backup settings, cost budgets, retention jobs.

Exit gate: all critical user journeys pass in staging; LLM outage has no critical impact.

### Week 4 — hardening and launch

- Load test target traffic plus 3× burst; tune DB/indexes/tasks and image caching.
- Cross-role/tenant authorization tests, upload abuse tests, CSRF/session/rate-limit checks.
- Browser/device matrix, axe plus manual keyboard/screen-reader checks.
- Restore drill, rollback drill, CSLB failure/replay drill, admin training.
- Counsel-approved policy text, production data seed, smoke/canary, limited vendor cohort.
- 48-hour launch watch with named response coverage.

Exit gate: launch checklist signed by product, technical operator, security/privacy owner,
and counsel for relevant claims—not just “tests green.”

## 3. Prioritized backlog

### P0 — launch blocking

- Auth, role/object authorization, verified email, password reset
- Vendor organization/profile, taxonomy and Bay Area service areas
- Official CSLB ingest/recheck, review fallback, badge removal, provenance/freshness UI
- Project CRUD, safe media, homeowner confirmation, confirmed-only publication
- Score v1 and audit snapshots
- Search/filter and responsive public pages
- Minimal admin queues and content reporting
- CI/CD, TLS/WAF/rate limits, secrets, monitoring/alerts, backups/restore
- Privacy notices/request intake and terms/claims approved by counsel

### P1 — shortly after launch

- Passkeys/social login, richer organization membership
- Automated duplicate/evidence review tools
- Improved admin metrics and vendor analytics
- Cross-region backups, enhanced bot management, independent penetration test remediation
- Queue/cache only if measured load needs it

### P2 — separate project after legal/product design

- Quotes, messaging, contracts/change orders, Stripe Connect, milestones, disputes
- Native apps and statewide expansion

## 4. Test strategy

| Level | Required coverage |
|---|---|
| Unit | State transitions, score boundaries, normalization, retention rules |
| Property | Score always 0..100; invalid dates/states impossible; import idempotency |
| Integration | DB constraints, S3 presign/processor, email tokens, CSLB fixtures, Anthropic fallback |
| Authorization | Every private endpoint across owner, other vendor, homeowner, admin, anonymous |
| Browser | Register, claim, create/upload, invite, confirm, publish, search, admin hold |
| Contract | CSLB parser fixture versions; generated OpenAPI breaking-change check |
| Security | CSRF, XSS payloads, IDOR, file polyglots/bombs, rate limits, secret/log redaction |
| Operations | Backup restore, deployment rollback, job retry/DLQ, stale/empty CSLB source |

Production-like tests use synthetic users and licensed-data fixtures where permitted. Never
copy production PII into development or staging.

## 5. Launch acceptance checklist

### Product

- [ ] Vendor can complete onboarding and knows why a claim is pending/ineligible.
- [ ] Homeowner can confirm, reject, or request correction on the exact project version.
- [ ] Only current confirmed projects count/display.
- [ ] Search/filter and score explanation work at mobile widths.
- [ ] Badge says source and last-check time without overstating assurance.

### Security/privacy/legal

- [ ] Counsel approves terms, privacy, collection notices, verification/badge wording.
- [ ] Admin MFA and least privilege tested; no shared accounts.
- [ ] Cross-tenant authorization suite passes.
- [ ] Raw/private objects cannot be accessed through CDN or guessed URLs.
- [ ] Logs and Anthropic requests contain no restricted data.
- [ ] Privacy request workflow and retention jobs have owners.

### Reliability/operations

- [ ] Production alarms reach both named responders.
- [ ] Restore and rollback drills meet documented RTO/RPO.
- [ ] Empty/stale/malformed CSLB input quarantines without mass badge removal.
- [ ] Score recomputation is idempotent and reconciliation shows no drift.
- [ ] Runbooks, architecture, credentials inventory, and vendor contacts are handed over.
- [ ] AWS and Anthropic budgets/usage alerts are active.

## 6. Budget posture

The main fixed costs are Multi-AZ RDS, NAT, ALB, WAF, and always-on Fargate tasks. Keep the
application small by using PostgreSQL search and scheduled one-off tasks instead of Redis,
OpenSearch, Kubernetes, or a permanent worker fleet. Scale staging down out of hours and use
short log retention for nonsecurity debug logs.

For planning only, expect a low-hundreds to low-thousands USD monthly AWS bill across
production and nonproduction depending on database HA, NAT topology, traffic, log volume,
WAF requests, and image transfer. Anthropic is usage-based and separately capped. Produce a
region-specific AWS Pricing Calculator estimate immediately before implementation and set
budgets at 50/80/100% of the approved amount; do not treat this qualitative range as a quote.

## 7. Definition of done

A feature is done only when authorization, validation, audit behavior, responsive UI,
accessibility, tests, metrics, error states, documentation, and operational ownership are
included. A production release is done only after the same image digest passes staging,
database compatibility is checked, smoke tests pass, and rollback remains possible.

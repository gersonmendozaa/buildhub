# Security, privacy, and operations

## 1. Data classification

| Class | Examples | Handling |
|---|---|---|
| Public | Published profile, CSLB-approved public facts, confirmed project derivatives | CDN cache allowed; integrity/audit still required |
| Internal | Score inputs, moderation flags, operational metrics | Authenticated staff/service access |
| Confidential | User email/phone, private address, homeowner association, messages | Encrypt, least privilege, redact from logs/LLM |
| Restricted | License evidence, future contracts/disputes, payment identifiers | Separate private storage, step-up admin access, access alerts |

Do not collect SSNs, government-ID images, card numbers, bank details, precise homeowner
location, or biometric data in the MVP. Stripe-hosted experiences own future financial data.

## 2. Security controls

### Identity and authorization

- Deny-by-default object authorization in domain services; views never filter only in UI.
- Vendor membership and project ownership are checked on every request.
- Admins use MFA/passkeys, short sessions, step-up for exports/role changes, and separate
  named accounts. Quarterly access review and immediate offboarding.
- AWS access uses Identity Center/SSO, least-privilege roles, SCP guardrails, and CloudTrail.
- CI uses GitHub OIDC to assume a narrow deploy role; no AWS keys in repository secrets.

### Application

- Django security middleware, CSRF, strict host/origin lists, output escaping, CSP with
  nonces, HSTS, Referrer-Policy, Permissions-Policy, and anti-clickjacking headers.
- Argon2id, verified-email gating, login throttling, session rotation, and secure cookies.
- Server-side validation, parameterized ORM queries, UUID identifiers, and generic private
  resource errors.
- SSRF defense: do not fetch user-supplied URLs. Image ingest is direct upload only.
- Dependency, secret, IaC, and container scanning in CI; signed images and SBOM retained.
- Annual penetration test or at minimum prelaunch independent test of auth, authorization,
  uploads, admin, and project confirmation.

### Files

- All S3 public access blocked. Separate raw/private and derivative buckets with KMS/SSE.
- Short-lived presigns constrained by key, type, bytes, checksum; random object keys.
- Validate magic bytes and decoded dimensions, scan with ClamAV, re-encode images, strip
  EXIF/GPS, cap decompression, and quarantine failures.
- License evidence is never copied to the derivative/CDN bucket. All restricted reads use
  short-lived signed URLs after authorization and generate an access audit event.

### Secrets and encryption

- Secrets Manager holds Django secret, DB credential/rotation config, Anthropic key, email
  signing secrets, and future Stripe webhook secrets. Inject at runtime, never at image build.
- TLS 1.2+ externally and to managed dependencies where supported. RDS/S3/EBS/backups are
  encrypted with environment-specific KMS keys.
- Separate Anthropic keys/workspaces by environment and rotate at least every 90 days until
  Workload Identity Federation removes static production credentials.

## 3. Privacy program baseline

Even if the startup initially falls below CCPA applicability thresholds, implement the
rights workflow and data minimization now:

- notice at collection for account, vendor claim, project invitation, uploads, and analytics;
- versioned privacy policy and terms acceptance;
- access/export, deletion, correction, limitation, and opt-out request workflow;
- honor Global Privacy Control if sale/share or cross-context advertising ever applies;
- service-provider contracts/data processing terms and a current subprocessor inventory;
- purpose/retention inventory for every PII field;
- no behavioral advertising or sale/share of personal information in MVP;
- identity verification proportionate to the request; secure, expiring export links;
- legal-hold and exception handling reviewed by counsel.

Public professional-license facts may be legally treated differently from account/project
PII, but do not use that as a blanket exemption. Keep source provenance and suppress fields
not needed for the marketplace.

## 4. Threat-focused controls

| Threat | Principal mitigation |
|---|---|
| Vendor claims another license | Exact source match, business-name check, email evidence/manual queue, one active claim |
| Fake confirmed work | Invited verified homeowner, immutable snapshot, rate/duplication flags, audit |
| Vendor self-confirms | Cross-role/account checks, organization membership exclusion, signal review |
| Malicious/private photo | Scan/re-encode/EXIF strip, human report queue, private raw bucket |
| Badge remains after suspension | Weekly successful import, atomic state/score update, stale-data alert |
| Bad CSLB file revokes all badges | Schema/count/freshness gates, quarantine, last-known-good retention |
| Broken object authorization | Domain-layer policy tests and cross-tenant integration tests |
| Prompt injection/data leakage | No tools, strict templates/schema, PII redaction, model is advisory only |
| Admin abuse | MFA, least privilege, reason codes, immutable audit, access alerts |
| Credential leak | Secret scanning, runtime secrets, rotation, scoped keys, incident runbook |

## 5. Logging and observability

Emit structured JSON with timestamp, environment, service, level, request ID, route name,
status, latency, account/vendor pseudonymous ID, deploy SHA, and error code. Never log
passwords/tokens, cookies, raw headers, emails/phones, addresses, license documents, private
notes, message bodies, presigned URLs, or Anthropic prompts.

Metrics/dashboards:

- ALB request rate, p50/p95/p99 latency, 4xx/5xx, unhealthy hosts;
- ECS CPU/memory/restarts/deployment failures;
- RDS CPU, storage, connections, replica/storage latency, backup status;
- S3/Lambda media success, quarantine, processing latency;
- CSLB age, row count delta, match/review/badge change counts, job outcome;
- registration/login/verification funnel and invitation delivery/decision rate;
- score recomputation failures/drift;
- Anthropic request count, tokens, cost estimate, latency, error/fallback rate;
- WAF blocks/rate-limit volume and admin/high-impact audit events.

Page the named operator for sustained 5xx, no healthy tasks, database exhaustion/storage,
failed production deployment, failed/stale CSLB import, backup failure, security anomalies,
and privacy-request deadline risk. Ticket/nonpage for single media failures or LLM fallback.
Use CloudWatch alarms to SNS, then a configured paging/email destination.

## 6. Backup and recovery

- RDS automated backups/PITR with at least 14-day retention at launch; 35 days preferred
  after cost validation. Take a manual snapshot before risky migrations.
- S3 versioning on raw/private and published buckets; lifecycle noncurrent versions to
  lower-cost storage and expire per approved retention policy.
- IaC state in a dedicated encrypted/versioned bucket with locking and tightly limited IAM.
- Nightly logical export is optional defense-in-depth, encrypted and kept in a separate
  backup account; it does not replace PITR.
- Cross-region copy is a post-launch control unless the business requires regional disaster
  recovery; document the accepted regional outage risk.

Quarterly, and before launch, restore the latest database point to an isolated staging
instance, verify migrations and core row counts, recover a previous S3 object version, and
record time/evidence. A backup is not considered working until restored.

## 7. Operational runbooks

### CSLB import failure

1. Alert and mark import failed/quarantined; do not change existing claims.
2. Inspect source availability, freshness, checksum, schema, row-count delta, parser logs.
3. Retry idempotently or deploy a reviewed parser version against the saved raw snapshot.
4. Reconcile sample licenses against official lookup before accepting.
5. Record incident and notify admins if freshness passes eight days.

### Incorrect badge

1. Apply an admin hold with reason; preserve the source record and public-safe explanation.
2. Check latest official record, import provenance, match, and time.
3. Correct mapping/parser or release hold; recompute score.
4. Notify vendor of state change and appeal/support channel. Never rewrite history.

### Suspected credential compromise

1. Disable affected account/key/session and preserve logs.
2. Rotate secrets and increase monitoring; invalidate app sessions if appropriate.
3. Determine access scope through CloudTrail/app/audit logs.
4. Engage counsel/incident lead for notification assessment and document timeline.

### Failed deployment

1. ECS circuit breaker returns to prior task definition/image digest.
2. Stop forward migration if safe; never blindly roll back a destructive database change.
3. Restore from snapshot only under incident command after impact confirmation.
4. Run smoke suite, communicate status, and open corrective action.

### Privacy request

1. Verify identity without collecting excessive new data.
2. Discover/export or delete through a repeatable job with exception/legal-hold report.
3. Deliver via expiring authenticated link and record completion.
4. Notify service providers where required; do not expose other users' data.

## 8. Operational ownership

Before production, contract or assign:

- a primary and secondary on-call owner;
- a business owner for license exceptions and moderation;
- a privacy/security request owner;
- an infrastructure maintainer for monthly patches and dependency updates;
- a lawyer for marketplace, contractor, privacy, and Phase 2 payment review.

Managed infrastructure reduces toil but does not remove the need for accountable operators.

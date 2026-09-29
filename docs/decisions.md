# Decisions, assumptions, and open questions

## Accepted architectural decisions

### ADR-001: Modular monolith over microservices

**Decision:** One Django application and PostgreSQL database with strict module/domain
boundaries. **Reason:** Fastest safe delivery and lowest operational burden. **Revisit when:**
independent scale, ownership, or availability requirements emerge.

### ADR-002: Server-rendered responsive UI over SPA/native apps

**Decision:** Django templates + HTMX/Alpine/Tailwind. **Reason:** One deployable, strong SEO,
less client auth/state complexity, and mobile-responsive delivery in the deadline. The REST
domain remains available for future native clients.

### ADR-003: PostgreSQL search over OpenSearch

**Decision:** FTS, trigram, and relational filters. **Reason:** Expected launch scale does not
justify another data plane. **Revisit when:** measured p95, relevance, facets, or corpus size
cannot meet targets after query/index tuning.

### ADR-004: ECS Fargate over Kubernetes/App Runner

**Decision:** ECS Fargate behind ALB/CloudFront. **Reason:** Managed containers, scheduled
one-off jobs, private VPC integration, WAF/ALB control, and a straightforward growth path
without a Kubernetes control plane. App Runner is simpler but less flexible for the combined
web, jobs, private networking, and edge controls.

### ADR-005: `us-west-2`

**Decision:** Oregon rather than `us-west-1`. **Reason:** service breadth, multi-AZ capacity,
and cost posture outweigh negligible regional latency for Bay Area users.

### ADR-006: Anthropic is advisory only

**Decision:** Use the supplied Anthropic credential for opt-in copy/alt-text/moderation
suggestions, behind an adapter and feature flag. **Reason:** LLM output is nondeterministic and
must not affect regulated facts, rank, enforcement, money, or legal outcomes.

### ADR-007: Exact CSLB source adapter, no scraping

**Decision:** Official registered web service or authorized data export with saved snapshots.
**Reason:** Provenance, reliability, source-change detection, and terms compliance.

## Product/business decisions required in the first 48 hours

1. What is the legal entity, product name, primary domain, and support contact?
2. Will unverified/ineligible vendors be publicly listed, or only verified vendors?
3. Is one CSLB license allowed to back multiple vendor organizations? Default: no, manual
   exception only.
4. Which categories/classifications launch, and are any high-risk trades excluded?
5. Does project confirmation require the homeowner to create an account? Default: yes.
6. May the platform contact the homeowner at the vendor-provided email, and what exact
   vendor attestation/notice is required?
7. How are historical projects handled when homeowner contact is unavailable? Default: they
   may display only in a clearly unverified portfolio section and never affect score; simplest
   MVP is to omit them.
8. Are vendor phone/email public? Default: vendor chooses; personal homeowner data never is.
9. Who performs license exception review, moderation, privacy requests, and on-call response?
10. What are approved retention periods and the dispute/legal-hold process?
11. What traffic, vendor, project, image-storage, and monthly budget assumptions define load
    and cost tests?
12. Which transactional email provider/sender domain and customer-support system are used?

## External prerequisites and blockers

- CSLB service registration may request company, host name, and IP address. Confirm its
  authentication, output schema, rate/usage conditions, freshness, and production IP needs
  before final network design.
- The no-cost portal and paid full/update files expose different scope/cadence. Confirm that
  the chosen source includes status, classifications, expiration, bond, and workers'
  compensation fields required by the product. Do not promise fields absent from that feed.
- SES production access and domain reputation setup can take time; start on day one.
- Anthropic production workspace/service-account key and spend limits are required. The
  application works with LLM features disabled.
- California legal review is mandatory before enabling contracts, milestone payments,
  automatic release, or calling any flow “escrow.”

## Explicit assumptions

- Launch is English-only and web-only.
- Initial traffic is modest enough for PostgreSQL search and two small web tasks.
- The platform is a marketplace/referral service in MVP, not the contracting party.
- No payments, quotes, chat, public reviews, background checks, or real-time license promise.
- Only project city/county are public; exact property address is unnecessary by default.
- Admin dispute tooling is Phase 2; MVP content/license appeals use support workflows.

## Risks and mitigations

| Risk | Impact | Mitigation/owner |
|---|---|---|
| CSLB access not approved or missing fields | Core promise blocked | Day-1 spike; adapter; manual fallback is temporary and transparently labeled |
| One-month scope expands | Unsafe/late launch | Fixed P0 backlog and written change control by product owner |
| No operational owner after agency handoff | Prolonged outage/security risk | Managed support contract and named primary/secondary before production |
| Fake project confirmations | Trust erosion | Verified invited user, snapshots, limits, duplicate signals, audit/review |
| Verification wording overpromises | Legal/reputation risk | Counsel-reviewed badge text and last-check/source disclosure |
| Upload abuse or privacy leak | User harm/cost | Private-first pipeline, scan/re-encode/EXIF strip, quotas, report queue |
| LLM sends PII or creates unsafe action | Privacy/decision risk | Allowlisted tasks, redaction, no tools, strict schema, human review, kill switch |
| Phase 2 funds flow is legally incorrect | Severe legal/financial risk | No implementation until counsel + Stripe approve state machine/contracts |

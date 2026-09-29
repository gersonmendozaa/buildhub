# BuildHub Marketplace — MVP architecture and specification

BuildHub is a mobile-responsive marketplace connecting Bay
Area homeowners with verified California construction vendors.

This repository contains the runnable MVP and its implementation blueprint. The
design favors a small, modular, open-source application and managed AWS infrastructure
so that a small external team can operate it safely.

## Local MVP

The first runnable feature slice is included. It supports:

- homeowner and vendor registration/sign-in;
- vendor profiles, categories, service counties, and license-review state;
- vendor project submission;
- private before/after image uploads with re-encoding and metadata removal;
- optional Claude vision analysis for stage, relevance, privacy flags, and alt text;
- manual-review fallback when Claude is unavailable or uncertain;
- homeowner confirmation restricted to the invited email account;
- material project versions that invalidate confirmation after photo changes;
- public vendor search/filter and confirmed project portfolios;
- a basic Django Admin operations surface and verification event trail.

Run it locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open `http://127.0.0.1:8000`. Demo credentials created by `seed_demo`:

- Vendor: `vendor_demo` / `demo-password-123`
- Homeowner: `homeowner_demo` / `demo-password-123`

SQLite is used when `DB_HOST` is empty. Copy `.env.example` values into your shell
or environment manager to use PostgreSQL. The local feature slice intentionally uses
demo license status; the real CSLB adapter is the next infrastructure-dependent feature.

### Project images and Claude analysis

Set `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`, and `ANTHROPIC_ENABLED=true` in the
ignored local `.env` file to enable advisory image analysis. The application never
sends the original file: it re-encodes the image as JPEG, removes metadata, and sends
the processed copy. Claude can recommend manual review but cannot delete content or
confirm a project. An administrator can review flagged images in Django Admin.

New projects remain drafts until they contain at least one approved `before` image and
one approved `after` image. Adding or removing an image increments the material version
and invalidates any earlier homeowner confirmation.

For a temporary ngrok demo, configure an ngrok account token locally, then run Django
with `.ngrok-free.app` in `DJANGO_ALLOWED_HOSTS`, the HTTPS wildcard in
`DJANGO_CSRF_TRUSTED_ORIGINS`, and secure cookies enabled. Never use the development
server or temporary tunnel as the production deployment.

### CSV test data

The synthetic marketplace dataset can be loaded into the local database with:

```bash
python manage.py import_marketplace_csv \
  outputs/buildhub-csv-test-data/marketplace_test_data.csv
```

New accounts created by the import use `csv-test-password-123` unless a different
value is provided with `--test-password`. All emails use the reserved `.test` domain,
and all license numbers are synthetic. Do not treat these records as CSLB data.

## Document map

- [Product specification](docs/product-spec.md) — scope, workflows, rules, and acceptance criteria
- [System architecture](docs/architecture.md) — stack, AWS topology, environments, and key decisions
- [Data model](docs/data-model.md) — MVP schema plus Phase 2 entities
- [API contract](docs/api.md) — API conventions, endpoints, authorization, and errors
- [Security and operations](docs/security-operations.md) — privacy, threat controls, backups, monitoring, and runbooks
- [Delivery plan](docs/delivery-plan.md) — four-week execution plan, staffing, gates, and launch checklist
- [Open questions and decisions](docs/decisions.md) — assumptions, ADRs, and decisions required from the business
- [Source notes](docs/sources.md) — official CSLB, California privacy, AWS, and Anthropic references

## Recommended implementation

- Python 3.13, Django 5.x, Django REST Framework, PostgreSQL 16+
- Django templates, HTMX, Alpine.js, and Tailwind CSS for a responsive web UI
- `django-allauth` for account flows and Django Admin for the first operations console
- Docker, Terraform/OpenTofu, GitHub Actions, Ruff, mypy, pytest, Playwright
- AWS ECS Fargate, RDS PostgreSQL, S3, CloudFront, ALB, WAF, EventBridge Scheduler,
  Secrets Manager, CloudWatch, SES, Route 53, and ACM in `us-west-2`
- Anthropic Messages API behind an internal adapter for optional assistive features

## Non-negotiable launch gates

1. Confirm and register the production CSLB data-access method. Do not build a
   brittle HTML scraper or claim real-time verification.
2. Obtain California counsel's approval of marketplace terms, project verification
   wording, privacy notices, and all Phase 2 contract/payment flows.
3. Restore a production-like database backup and an object-version recovery in staging.
4. Complete accessibility, authorization, upload-security, and core workflow tests.
5. Assign named owners for production alerts, content reports, CSLB exceptions, and
   privacy requests.

The Phase 2 payment schema is intentionally provisional. No escrow or milestone
payment flow should be enabled before legal and Stripe platform review.

# Technical plan, stage 5 (`/plan`), draft 1, 2026-10-21

## Context

The CPO approved the design spec (`docs/design-spec.md`, draft 2) on 2026-10-21. This plan is the Engineer's answer to it: how to build the MVP of the CRA and AI Act status-and-deadline dashboard for vendors of AI credit-scoring software.

The paid pilot starts **2026-11-15**, with one vendor paying €36k and one bank co-paying €15k once its legal review is done. The plan is scoped to what can be pilot-ready on that date. Everything else is phased after it.

Inputs read: `docs/design-spec.md`, `docs/prd.md`, the `CLAUDE.md` decision log, `docs/opportunity-brief.md`, the fresh-review section of `docs/ceo-review.md`, `README.md`, `schema.sql`, `build_db.py`, the `*.json` files and `regtech_cyber.db`.

**No code is written until the CPO approves this plan.**

## Headlines

1. **The pilot can start on 15 Nov, but not with everything.**
   - **Day 1:** the vendor workspace, with requirements, AI risks and Art. 14 clocks. **Drills only.**
   - **Real incident data:** only after the external pentest, around 7 Dec.
   - **Bank access and exports:** only after the pentest *and* legal sign-off on the disclaimer (D-4), target around 11 Dec.
   - This still fits success metrics P1, P2, P4 and P6.
2. **Stack:**
   - Python 3.12 and Django 5.2 LTS, server-rendered with HTMX; PostgreSQL 16; Keycloak (EU) for sign-in with MFA; WeasyPrint for PDF/UA exports.
   - EU-headquartered hosting (OVHcloud or Scaleway), with AWS Frankfurt as fallback.
3. **Tenant isolation is enforced in the database:**
   - row-level security on every tenant table;
   - customer sessions use a separate database role that can only read column-limited `cust_*` views.

   So D1 (customers never see clocks or filing times) is guaranteed by the database, not just by the screens.
4. **Deadline engine:**
   - **Authoritative:** a pure Python module, needed for the before/after previews.
   - **Independent check:** a revised Postgres `cra_deadline_check` view, which tests compare against the Python engine.
5. **D7 and D8:** accept all four proposals. Close states (plus reopen) and drill mode go in the pilot cut. Linked events get their table now and their screens in phase 1b. Events stay out of CSV import, which saves about 3 days.

## Architecture and stack

| Layer | Choice |
|---|---|
| App | Python 3.12, Django 5.2 LTS (supported to April 2028), server-rendered templates, HTMX, about 150 lines of plain JavaScript (countdown, tab title, clock-skew check) |
| Database | Managed PostgreSQL 16, EU region, encrypted, point-in-time recovery, multi-AZ |
| Live clock strip | HTMX polls every 30 s. Countdowns come from server time. Polling does **not** reset the idle timer. |
| Identity | Keycloak 26, EU-hosted, over plain OIDC: vendor SSO through brokering; customer admins as invited local users with MFA required (passkey or authenticator app, no SMS); step-up re-authentication |
| PDF | WeasyPrint, PDF/UA-1, checked with veraPDF |
| Jobs | One scheduled management command: the nightly audit entry for evidence that has gone stale |
| Files | None in the pilot: evidence is links only (C5) |
| Hosting | EU managed platform: 2 app instances plus a multi-AZ database, enough for 99.5% availability |
| CI | GitHub Actions: pytest, Hypothesis, Playwright with axe-core, pip-audit, Bandit or Semgrep, secret scanning |

**Not used:** a single-page app, GraphQL, microservices, or Django admin in production. Leaving out the admin enforces "no support-staff access to tenant data".

## Data model (summary)

**Conventions:** UUIDs in URLs. All times `timestamptz` in UTC, truncated to the minute (enforced by CHECK). Every tenant table carries a `vendor_tenant_id`.

- **Tenancy:**
  - `tenant` (vendor or customer, with a parent vendor);
  - `user_account`;
  - `role_grant`, with history. The responder role is looked up on every request.
  - `customer_invitation`;
  - `activity_sharing_setting`, defaulting to "organisation" (D9);
  - `system_setting`: disclaimer template, `month_rule`, retention. Changes are audited and need no release.
- **Reference data (R-X1, nothing hard-coded):**
  - `annex_iii_category`, `requirement_set`, `requirement` (with a `pending_oj_check` flag);
  - `category_requirement_set`;
  - `taxonomy` (with `licence_status`) and `taxonomy_item`;
  - loaded from YAML in `data/catalog/`.
  - **`regtech_cyber.db` is not loaded** (IP not cleared).
- **Registry and status per version (D3):**
  - `product`, `product_version` (carry-forward), `deployment`;
  - `requirement_status`, `ai_risk`, `ai_risk_requirement_link` (informational only);
  - `evidence_item` (links). "Evidence stale" is computed when read and can never be set by hand.
- **`finding` → `art14_event`** (0 rows today, so this is a schema change only):
  - `actively_exploited` becomes `event_type` (vulnerability or severe incident); `reported_at` becomes `awareness_at`.
  - The filing columns are kept. Status becomes `open`, `closed_reporting_complete` or `closed_not_reportable`.
  - Title and description move to a responder-only `art14_event_detail` table, encrypted at the application level in phase 1b.
  - The disclosure, bug-bounty and CVSS fields are dropped.
  - New fields: product and version, assigned responder, started_by, started_via, awaiting_responder, `is_drill` (cannot change after creation).
  - New tables: `art14_event_deployment`, `art14_users_informed` (one row per deployment, with a customer reference and withdrawal fields), `art14_event_link`, `drill_outcome`.
  - Triggers: drill status can't change; drills can't be released; filing times can't be earlier than awareness.
- **`cra_deadline_check`** moves to Postgres:
  - it includes severe incidents;
  - the final report for a severe incident is notification + 1 month, clamped;
  - it adds a `stopped` state.
  - SQLite can't do this: `date('2027-01-31','+1 month')` gives 2027-03-03.
- **`audit_event`:**
  - append-only, enforced by having no UPDATE or DELETE rights, a trigger, and a hash chain;
  - incident values are masked when displayed or exported, never deleted;
  - for D9 it stores the real actor plus `shared_as`. The vendor sees a name only when the entry *and* the current setting are both "named".
- **Exports and imports:**
  - `export_record`: export ID plus SHA-256. The files aren't stored.
  - `import_batch`: preview, then all-or-nothing.
- **Existing knowledge base:**
  - remove `finding`, `security_changelog` and `cra_deadline_check` from `schema.sql`, and the findings loader from `build_db.py`;
  - delete `findings.json` and rebuild `regtech_cyber.db`, checking the counts are unchanged (8 / 9 / 17);
  - add a `.dockerignore` so the book-derived content can never be shipped.

## Authorization and isolation

1. **Database roles:**
   - `app_vendor` works under row-level security on the tenant id;
   - incident-detail tables additionally require `app.is_responder`;
   - `app_customer` can read only the `cust_*` views, with no base tables.
2. **Request context:** middleware sets `app.tenant_id` and the responder flag (`SET LOCAL`), from a fresh lookup on every request. If the context is missing, queries return 0 rows.
3. **Application policy:** `apps/authz/capabilities.py` encodes the design's permission matrix. A test fails the build if any route has no declared capability.

**Not-found behaviour:** anything outside the caller's scope gets the same 404 as a UUID that doesn't exist. The customer incident page looks identical whether the vendor has no events or only unreleased ones.

**Sessions:**
- idle timeouts of 8 h for vendor users and 30 min for customer users;
- absolute limits of 24 h and 8 h;
- "Mark informed" needs a fresh MFA step-up: `auth_time` no more than 5 min old, valid for one action.

**Isolation tests (block merges):**
- **Route matrix:** for every role, request objects belonging to other tenants and other customers; expect byte-identical 404s.
- **Database:** the customer role is denied every base table; no context gives 0 rows.
- **Responder role:** revoking it mid-session takes effect on the next request.
- **Non-inference:** "no events" and "only unreleased events" give identical responses.
- **Export content:** exports contain no awareness or filing times and no drills.

## Deadline engine

`apps/art14/deadlines.py` is pure Python. Deadlines are computed when read and never stored.

- **Clocks:**
  - early warning = awareness + 24 h;
  - notification = awareness + 72 h;
  - vulnerability final report = fix + 14 days;
  - severe-incident final report = notification filing + 1 month.
- **Month rule:** `calendar_clamp_utc` (D10, the default) or `days_30`, configurable.
- **States:** met, late, open, overdue, not started, stopped.
- **Local-time input** (`localtime.py`):
  - a time more than 60 s in the future is rejected;
  - a skipped DST hour is rejected;
  - a repeated DST hour needs an explicit offset choice.
- **Tests:**
  - **Fixed EU DST dates:** 2026-10-25, 2027-03-28, 2027-10-31.
  - **Month ends:**
    - 31 Jan → 28 or 29 Feb, 31 Mar → 30 Apr, 31 Dec → 31 Jan;
    - a 23:30 UTC filing on 31 Jan gives 28 Feb, not 1 Mar.
  - **Exact boundaries:** filed exactly at the due time is met; a minute later is late.
  - **Hypothesis property tests:**
    - exact 24 h and 72 h gaps;
    - converting to local time and back gives the original;
    - the clamp rule holds;
    - due times only move later when the start moves later.
  - **Awareness edits and reclassification:** they shift exactly the right clocks.
  - **Differential test:** Python and the Postgres view agree.
  - **Golden file** `tests/golden/deadlines.csv`, for P3 (zero deadline errors), readable by legal.

## Modules → screens → requirements

| Module (`apps/…`) | Screens and flows | Covers |
|---|---|---|
| `tenancy` | S-14 users and roles, customer access; F-1 | NFR-1, NFR-2, D5 |
| `identity` | S-0, step-up on S-10 | NFR-1, D6 |
| `authz` | all | 2.3, OQ2, D4 |
| `audit` | S-16, audit export | NFR-3, D9 |
| `catalog` | S-14, taxonomy seeding | R-X1, D-1 |
| `registry` | S-14, setup checklist | D3 |
| `requirements` | S-3, S-4 | R-1 |
| `airisks` | S-5, S-6 | R-2, OQ3 |
| `art14` | S-1 strip and tab title, S-7, S-8, S-8a, S-9, S-11, S-12, S-13, drills | R-3, D4, D7, D8, D10, NFR-4 |
| `release` | S-10 | R-4, Art. 14(8) |
| `customer` | S-B0 to S-B7 | R-4, OQ1, D1, D2, D9 |
| `imports` | S-15 | CSV import |
| `exports` | S-17, S-B6 | NFR-3, NFR-8 |
| `ui` | shell, disclaimer footer, design tokens | NFR-8 |

## D7 and D8 recommendations

- **D7, close states:** accept, in the pilot cut (about 1.5 ed).
  - "Closed – reporting complete" is allowed once all three filings are recorded.
  - "Closed – determined not reportable" needs a rationale, and the clocks show `stopped`.
  - **Added:** reopening needs a reason and is audited (about 0.5 ed).
- **D7, linked events:** accept the model of two linked events (each with its own clocks and filings). Rejected alternative: one event with two types. The table goes in now and the screens in phase 1b (about 2 ed).
- **D8, drill mode:** accept, in the pilot cut (about 2.5 ed). Before the pentest, drills are the only events allowed.
  - Drills use the same code path as real events.
  - The database guarantees separation: drill status can't change, drills are filtered from customer views, they can't be released, and they're excluded from counts.
  - If a real event is logged as a drill by mistake, the fix is to log it again as a real event and close the drill.
- **D8, no events in CSV import:** accept. Saves about 3 ed. A responder-only historical import can come later if asked for.

## Phased delivery (2 engineers; ed = engineer-days)

- **Phase 0, foundations (22–30 Oct), about 17 ed:**
  - scaffold, CI, dev, staging and prod (3);
  - Keycloak, MFA and sessions (3);
  - tenancy, RLS, roles, authz and the route-matrix harness (4);
  - audit log (2);
  - deadline engine and tests (3);
  - catalog loader (2).

  **Content dependency:** the PM or legal writes about 35 requirement rows (CRA Annex I Parts I and II, AI Act Art. 15) by 30 Oct.
- **Phase 1a, pilot cut (ready 13 Nov), about 21 ed:**
  - shell, clock strip, tab title, disclaimer and banned-word check (3);
  - setup and registry (3);
  - requirements (3);
  - AI risks (2.5);
  - Art. 14 log, start-clock, detail, filings, awareness edit, close and reopen, drills (6.5);
  - audit screen (1.5);
  - accessibility pass (1.5).

  Phases 0 and 1a need about 38 ed against about 34 available, so **reclassify and CSV import slip to week 1 of the pilot**. P1 has a 4-week window, so this fits.
- **Phase 1b (16 Nov to about 11 Dec), about 30 ed:**
  - reclassify, CSV import, linked events, carry-forward and the stale-evidence job;
  - customer workspace and invitations;
  - mark informed with step-up and withdrawal, plus per-customer references;
  - PDF/UA and CSV exports with hashes;
  - application-level encryption of incident details;
  - **external pentest around 30 Nov to 4 Dec**, plus about 3 ed of fixes.

  **Gates:**
  - real incident data only once every critical and high pentest finding is fixed;
  - bank access only once that is done *and* legal has signed off on the disclaimer and the "About this information" text.
- **Phase 2 (2027):**
  - export verification screen;
  - file uploads with malware scanning;
  - customer identity federation;
  - historical import;
  - 5(c) as data;
  - alerts (depending on P8).

## Security and testing

- **Unit tests:** engine, local-time handling, masking and anonymisation renderer, CSV validation, formula-injection escaping.
- **Integration tests on real Postgres:** RLS, roles, triggers, all-or-nothing import, optimistic locking.
- **Isolation suite:** runs on every pull request.
- **Accessibility:**
  - Playwright with axe-core at 320 px and desktop;
  - keyboard scripts for S-8, S-8a, S-9 and S-10;
  - manual NVDA and VoiceOver checks;
  - veraPDF;
  - colour-contrast check.
- **Copy checks:**
  - a scan for banned words ("compliant", "certified", "secure", "bank" in UI chrome, and the rest), with an allowlist for the disclaimer;
  - no green, red or amber status tokens.
- **Application security:**
  - OWASP ASVS L2 checklist;
  - strict CSP and HSTS;
  - rate limits on sign-in and exports;
  - dependency, static-analysis and secret scanning;
  - no incident text or personal data in logs;
  - break-glass procedure for operator database access.
- **Pentest scope:** isolation, the responder boundary, authentication and step-up, CSV and PDF injection, export integrity, and inference of unreleased incidents.

## Files

- **Create:**
  - `pyproject.toml`, `uv.lock`, `manage.py`, `tracker/settings/{base,dev,prod}.py`, `tracker/urls.py`;
  - `apps/{tenancy,identity,authz,audit,catalog,registry,requirements,airisks,art14,release,customer,imports,exports,ui}/` (key files: `apps/art14/deadlines.py`, `apps/art14/localtime.py`, `apps/authz/capabilities.py`);
  - `db/sql/{rls_policies,db_roles,customer_views,cra_deadline_check,audit_append_only,drill_guards}.sql`;
  - `data/catalog/*.yaml` and `data/catalog/taxonomies/{nist_ai_100_2,mitre_atlas}.yaml`;
  - `tests/{unit,property,isolation,authz_matrix,integration,a11y,e2e,copy_lint}/` and `tests/golden/deadlines.csv`;
  - `infra/` (Dockerfile, docker-compose.dev.yml, Keycloak realm export), `.dockerignore`, `.github/workflows/ci.yml`.
- **Modify:**
  - `schema.sql`, `build_db.py`, `regtech_cyber.db` (rebuild);
  - `.gitignore`;
  - `README.md`: status line only.
- **Delete:** `findings.json`.
- **Untouched:** `risks.json`, `innovations.json`, `mitigations.json`, `barriers.json`, the notebook, `docs/`.
- **Orchestrator bookkeeping:** the header of `docs/design-spec.md` still says "awaiting CPO approval". Fix it once plan mode ends.

## Decisions needed from the CPO before `/build`

- **C1, event references leak hidden incidents.** A customer seeing E-0003 and then E-0007 can infer that hidden events exist. **Recommend:** customers get their own reference, assigned at release (INC-1, INC-2…). This is a small change to the design.
- **C2, countdowns reveal the awareness time** to non-responder admins (due time − 24 h = awareness). **Recommend:** accept it as a known limitation.
- **C3, hosting.** **Recommend:** an EU-headquartered provider (OVHcloud or Scaleway) with EU-managed Keycloak, and AWS Frankfurt as fallback. Ask the bank's supplier-risk team which they prefer.
- **C4, team size.** Confirm 2 engineers. With 1, choose between a 1 Dec start and a reduced day-1 with drills only from week 3.
- **C5, evidence as links only in the pilot.** File uploads come in phase 2.
- **C6, pilot-agreement clause.** No real incident data until the pentest passes (around 7 Dec). Until then the vendor keeps its existing Art. 14 process.
- **C7, a fix recorded before awareness.** **Recommend:** allow it with a warning, compute as specified, and refer it to legal.
- **C8, taxonomy seeds.** **Recommend:** NIST AI 100-2 and MITRE ATLAS (Apache-2.0), after a licence check. Hold OWASP (CC BY-SA) pending counsel.

## Risks and assumptions

- **Schedule:** there's no slack with 2 engineers, and the catalog content (owned by the PM or legal) is on the critical path.
- **No alerts:** an 8 h idle sign-out hides the strip on an unattended screen. This is accepted by design. Include an out-of-hours drill in P4.
- **Pentest findings** may delay real data and bank access, but not the pilot start.
- **Legal changes** to the disclaimer or month rule are configuration, so no release is needed.
- **Engine drift** between Python and the Postgres view is caught by the differential test.
- **Assumptions:**
  - the month rule is global, not per tenant;
  - invitation emails don't count as "alerts";
  - the pilot is small (1 vendor, 1 product, 1–2 customer accounts).

## Verification

- `pytest` runs green: unit, property (Hypothesis), integration on Postgres, the isolation and authz matrix, copy checks, and the golden deadline file.
- Playwright end-to-end tests with axe-core cover the drill flow (log → strip → filings → close), the admin-started clock, mark informed with step-up, customer view and export, and CSV import.
- veraPDF passes on the exports.
- Manually in staging, a drill run on the EU DST date confirms correct local and UTC deadlines.
- `python build_db.py` rebuilds `regtech_cyber.db` with unchanged counts (8 / 9 / 17).
- `/test` (QA) checks the result against the PRD and design spec. The external pentest is a gate before real data is loaded.

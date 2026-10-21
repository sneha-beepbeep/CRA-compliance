# Test report: phase 0 and phase 1a (stage 7, `/test`)

**Date:** 2026-10-21. **Build tested:** branch `pipeline-setup`, commit `e98b843` (phase 0 and 1a from `0ee7371`).
**Tested against:** `docs/prd.md` (draft 1), `docs/design-spec.md` (draft 2), `docs/technical-plan.md` (phase 0 and 1a scope), decisions D1–D10, C1–C8 and build deviations 1–13 in `CLAUDE.md`, and the gates in `docs/critical-path.md`.
**Tester:** QA. I did not write this code. I changed no application code.

---

## 1. Summary

- **The Engineer's suite passes:** 572 passed, 0 failed, 2 skipped, on local PostgreSQL 16.2. This matches the Engineer's report. The 2 skips are not real browser tests (see QA-10).
- **My own checks:** I wrote 117 scripted checks, plus a 39-request smoke pass and a headless-browser pass over 14 screens at two widths. **110 checks passed and 7 failed.** They ran against a separate QA database through a non-superuser login role, set up the way `db/sql/db_roles.sql` says production must be.
- **The core risks hold up under independent testing:**
  - tenant isolation and row-level security;
  - incident details visible to responders only, including when the role is revoked mid-session;
  - customers never see clocks (D1);
  - the deadline engine;
  - drill guards;
  - the append-only audit trail;
  - session timeouts;
  - deviation 13;
  - the C7 warning.
- **One critical new defect (QA-01):** with the documented production database roles, **every sign-in fails with a server error.** The Engineer's tests and CI can't catch it, because they connect as the database superuser. The fix is small.
- **Defects found:** 1 Critical, 3 Medium, 8 Low. All are new. The Engineer's declared gaps are listed separately in section 6 and are not counted as defects.
- **Recommendation:** **No-ship as of today.** It becomes a **conditional ship for the 15 Nov drills-only start** once QA-01 is fixed and the sign-in path has been proven end to end in EU staging. Full conditions are in section 9.

---

## 2. What I tested and how

| Area | Method |
|---|---|
| Full suite | `pytest` on a local PostgreSQL 16 (`scripts/localpg.sh`) |
| Production-like request path | A separate database `qa_tracker` with login role `qa_app`. `qa_app` is not a superuser. It holds `app_auth` with INHERIT TRUE, and `app_vendor`/`app_customer` with INHERIT FALSE, SET TRUE, as `db_roles.sql` specifies. Requests went through the Django test client with `DEBUG=False` and dev login off. |
| Database guards | Direct SQL as `app_vendor`, `app_customer` and the owner |
| Deadline engine | All 21 golden rows checked by hand, plus 15 extra cases I calculated myself |
| Browser | Playwright with Chromium and axe-core (WCAG 2.0/2.1/2.2 A and AA tags), at 1280 px and 320 px, on 14 vendor screens. Also a drill flow at 320 px. I installed Playwright into `.venv` for the run and uninstalled it afterwards. |
| Static security | Bandit over `apps/` and `tracker/` (no issues). A manual secrets grep. Review of the prod settings, headers and CSP. |

**Not run:**
- **pip-audit:** it sends the dependency list to an external vulnerability service, which this task's rules exclude. CI runs it (`pip-audit --strict`), but CI has never run.
- **Keycloak/OIDC with MFA, GitHub Actions and the Docker image:** there was no infrastructure access. These were also declared untested by the Engineer.

Probe scripts are in the session scratchpad. They are not in the repo.

---

## 3. Test suite results

```
572 passed, 2 skipped in 16.70s
SKIPPED [1] tests/a11y/test_axe.py:8: Playwright not installed; run the axe-core pass in CI
SKIPPED [1] tests/e2e/test_drill_e2e.py:8: Playwright not installed; browser e2e runs in CI
```

- There were no failures.
- `makemigrations --check`: no changes detected.
- With Playwright installed, the two skipped files still test nothing. `test_axe.py` is a placeholder that skips itself, and `test_drill_e2e.py` contains no test functions (QA-10).

---

## 4. Independent verification of high-risk areas

| Area | Result | Evidence |
|---|---|---|
| **Tenant isolation (NFR-2)** | **Pass** | Another tenant's event gives a 404 that is byte-identical to a random UUID's, for both the responder and the admin. The strip shows no other-tenant content. A deployment typed with another vendor's customer name creates a new customer tenant and never attaches to theirs. Selecting another vendor's version gives a 404. `app_vendor` cannot write across tenants (suite). |
| **`app_customer` role** | **Pass** | It is denied `cra_deadline_check` and every base table (suite plus my check). Every vendor route gives a customer a 404. A customer POST to `/profile/` gives a 404. |
| **Details for responders only (D4, OQ2)** | **Pass** | A non-responder admin gets the restricted view with no title, description or filing column. Every detail and action route (details, time, awareness, close, reopen, take-over, drill outcome, log) gives a 404. The database also hides `art14_event_detail` from non-responders. |
| **Role revoked mid-session** | **Pass** | An access manager granted the role, and the admin saw details on their next request. The role was revoked, and on the next request the admin got the restricted view, a 404 on `/details` and no "Open event" link on the strip. Both changes are audited. A non-access-manager can't grant the role. |
| **D1: no clocks or filing times for customers** | **Pass** | The customer home page has no strip, no event references and no Art. 14 states. The strip partial gives a customer a 404. `cust_incident` has no awareness, filing or drill columns (suite). |
| **Deadline engine** | **Pass** | The 21 golden rows match my hand calculations: G01–G21 cover 24h/72h, the 25 Oct 2026, 28 Mar 2027 and 31 Oct 2027 changeovers, the repeated hour, the weekend case, met and late at the exact minute, open at the due minute and overdue one minute after, the clamps from 31 Jan (28 Feb, and 29 Feb in 2028), 31 Mar, 31 Dec and 28 Feb, the days_30 rule, stopped clocks and C7. My 15 extra cases also pass: more clamps (31 Aug, 31 May, 29 Feb 2028), a Berlin 31 Jan 23:30 local filing (22:30Z → 28 Feb), 24h and 72h across the end of DST, a severe incident ignoring the fix time, seconds truncation, skipped and repeated local hours in Warsaw and Berlin, and choosing an explicit offset. The Python engine and the Postgres view agree (suite differential and property tests). |
| **Drill guards (C6, D8)** | **Pass** | `real_events_enabled` is absent, so it defaults to off. A responder logging without the drill flag, or with `drill=0`, gets a drill. A start-a-clock by an admin is a drill, awaiting a responder, with no detail row. `is_drill` can't change, as `app_vendor` or as the owner. Inserting a release row for a drill is rejected by the trigger. The drill outcome is recorded. |
| **Audit append-only and hash chain** | **Pass, with one limitation** | `app_vendor` DELETE is denied. Tampering with a middle row is detected at the right `seq`. **Deleting the newest row is not detected** (QA-09). |
| **Copy rules** | **Pass** | The copy lint passes. My grep of the catalog YAML (including fields the lint skips) found no banned words. The NFR-8 notice is in the footer on every vendor page and on the customer placeholder page. Help says "The dashboard does not notify anyone". |
| **Session timeouts (D6)** | **Pass** | A vendor idle for 7h58m still sees the strip, and the strip poll doesn't reset the idle timer. At 8h02m the poll gets a 401 and `HX-Redirect` to signed-out. The 24h absolute limit is enforced. A customer idle for 31 min is signed out, and at 29 min is not. The signed-out page title is "Signed out – deadlines hidden". |
| **Deviation 13** | **Pass** | `CUSTOMER_INVITATIONS_ENABLED = False`. The checklist has 6 required steps. The invite step is not shown on S-2 or S-14. |
| **C7: fix before awareness** | **Pass** | It is accepted, with the warning "…earlier than the awareness time… Check this case with legal counsel." A filing time before awareness is rejected. |
| **Close and reopen with reasons** | **Pass, with defect QA-02** | Closing as reporting complete without filings is rejected. "Not reportable" with a 19-character rationale is rejected, and with 35 characters is accepted; the clocks then show "stopped" and the event leaves the strip. Reopen is rejected with a short reason, and accepted and audited with a long one. An awareness edit is rejected with a 19-character or whitespace-only reason. A 26-character reason gives a before/after preview, is audited with old, new and reason, is masked for the admin and unmasked for the responder, and shows the admin "recalculated by a responder". **But a closed event can still be edited without reopening it** (QA-02). |
| **CSRF and headers** | **Pass** | A POST without a token gives a 403. Present: CSP (`script-src 'self'`, no inline script), X-Frame-Options DENY, nosniff, Referrer-Policy same-origin, `Cache-Control: no-store`, COOP. HSTS (1 year) and the SSL redirect are set in prod. No console or CSP errors in the browser. |
| **Dev-only routes** | **Pass** | `/dev/login/` is not routed with prod settings or with `DEV_LOGIN_ENABLED=False`. Prod has `DEBUG=False` and the OIDC backend only. |
| **Secrets** | **Pass** | Nothing is hard-coded in app code. The test key is marked. The dev compose file and CI use throwaway local passwords, which is acceptable. Bandit found no issues. |
| **Sign-in under production DB roles** | **Fail** | QA-01 |

---

## 5. Defects

Every defect below is new; none was declared by the Engineer. Severity is judged for the 15 Nov drills-only start unless stated otherwise.

### QA-01 Critical: every sign-in fails under the documented production database roles

- **Where:** `db/sql/db_roles.sql` and `db/sql/rls_policies.sql`, with `django.contrib.auth.login` → `update_last_login`.
- **Cause:** `app_auth` has `UPDATE (last_login)` on `user_account`, but row-level security on `user_account` gives `app_auth` a **SELECT** policy only. The UPDATE therefore matches 0 rows, and Django raises `DatabaseError: Save with update_fields did not affect any rows`.
- **Steps to reproduce:**
  1. Create a login role that isn't a superuser:

     ```sql
     CREATE ROLE qa_app LOGIN PASSWORD '...';
     GRANT app_auth TO qa_app WITH INHERIT TRUE;
     GRANT app_vendor, app_customer TO qa_app WITH INHERIT FALSE, SET TRUE;
     ```

  2. Point `DATABASE_URL` at it.
  3. Sign in any user. The dev login, `Client.force_login` and the OIDC callback all go through `auth.login`.
  4. As `qa_app`, `UPDATE user_account SET last_login=now() WHERE email='admin@acme.example'` returns `UPDATE 0`.
- **Expected:** sign-in succeeds. **Actual:** a 500 error, and nobody can sign in.
- **Why the tests miss it:** the suite and the CI workflow connect as the database superuser or owner, so the `app_auth` path is never exercised.
- **Ask for the Engineer:**
  - add an `app_auth` UPDATE policy on `user_account` limited to `last_login`, or stop updating `last_login`;
  - add a regression test that runs requests through a login role that isn't a superuser, and run it in CI.

### QA-02 Medium: closed events can be changed without reopening

- **Where:** `apps/art14/services.py` (`record_time`, `edit_awareness`, `update_details`, `reassign`) and the matching views. None of them check `status`.
- **Steps to reproduce:**
  1. Close an event as "determined not reportable".
  2. As the responder, POST to `/events/<id>/time` (early warning), `/events/<id>/awareness` (with a valid reason) or `/events/<id>/details`.
- **Expected:** rejected with "Reopen the event first". **Actual:** all three return 302 and save. After the filing POST the event is still `closed_not_reportable` but has an early-warning filing time, so its "stopped" clock becomes "met" or "late".
- **Risk:** the buttons are hidden for closed events, but a stale tab from during the incident can still submit. The changes are audited, so nothing is hidden. But a "closed – reporting complete" record can change after closure, which weakens the regulatory record.

### QA-03 Medium: no audited way to change system settings

- **Where:** the `SystemSetting` docstring in `apps/tenancy/models.py` says settings are "changed by operators through `manage.py set_system_setting` (audited)". The command doesn't exist.
- **Effect:** each of these needs raw SQL with no audit entry:
  - turning on `real_events_enabled` (the C6 gate, around 7 Dec);
  - changing the disclaimer after legal sign-off;
  - changing `month_rule`.

  The technical plan says "Changes are audited and need no release."
- **Blocks:** the real-data gate, not 15 Nov.

### QA-04 Medium: the incident screens don't reflow at 320 px (WCAG 1.4.10)

- **Where:** the vendor shell layout. At 320 px, the side nav and main column overflow:
  - 336 px wide on S-8 and S-8a;
  - 377 px on S-9;
  - also S-3 to S-6, S-11 and profile.
- **Steps to reproduce:** open `/events/start` at a 320 px viewport. `document.documentElement.scrollWidth` is 336, so the page scrolls sideways.
- **Expected:** design section 16 says S-7, S-8, S-8a and S-9 "must be fully usable on mobile, since the person who learns of an incident may be on a phone at night". S-7, S-2, S-14 and S-16 do reflow.
- **Note:** the Engineer declared the accessibility pass not done. This is a concrete finding from that pass, and it affects the P4 out-of-hours drill.

### QA-05 Low: tap targets too small (WCAG 2.5.8)

- **Found by:** axe `target-size`, rated serious.
- **Where:**
  - the `<summary>` toggles "Early warning filing time", "Notification filing time" and "Final report filing time" on S-9 (3 to 4 nodes);
  - "Add a product" and "Add a version" on S-14.

  The filing-time toggles are the controls used most during an incident.
- **Elsewhere:** axe found no other violations on the 14 screens at either width.

### QA-06 Low: the deadline preview and the ">24h ago" warning appear only once the whole form is valid

- **Where:** S-8 and S-8a (`_preview` needs `form.is_valid()`, and htmx doesn't send a request while required fields are empty).
- **Steps to reproduce:** on `/events/log?drill=1`, enter the type, date and time, then leave the field. The preview stays at "Enter the event type and awareness time…" until Product and Title are also filled.
- **Expected:** design 8.3 says the preview "updates as you type" from the type and awareness time. The warning that the early warning has already passed should show **before** saving.
- **Actual:** a user who clicks "Log … and start clocks" straight away never sees the warning.

### QA-07 Low: a malformed version ID gives a server error

- **Steps to reproduce:** POST `/version/select` with `version=not-a-uuid`.
- **Expected:** 404. **Actual:** 500 (unhandled `ValidationError`).
- **Note:** the other bad-input POSTs I tried return 4xx. The `next` redirect is safe (`//x`, `/\x` and `https://x` all stay on the site).

### QA-08 Low: the audit trail is hard to read

- **Shown as codes:** S-16 shows raw action codes (`edited_awareness_time`, `started_clock`) and Python dict values (`Before: {'awareness_at': '2026-10-21T17:36:00Z'}`), with times in UTC ISO only.
- **Design 13 calls for:** human-readable actions and local plus UTC times.
- **Not masked:** drill-outcome notes are free text and are never masked for non-responders. They are drill-only, so this is low risk.

### QA-09 Low: the hash chain doesn't detect deletion of the newest entries

- **Steps to reproduce:** as the owner, disable `audit_event_no_update_delete`, delete the highest `seq` for a tenant, then run `audit_verify_chain(tenant)`. It returns NULL (intact).
- **Why:** this is inherent to a hash chain that isn't anchored anywhere outside the database. Anchoring would mean storing the latest hash elsewhere, for example in a periodic export or a log.
- **Also:**
  - nothing verifies the chain on a schedule;
  - `audit_verify_chain` can be called by any vendor session for any tenant ID (it returns only a `seq` or NULL).
- **Action:** add both to the pentest scope.

### QA-10 Low: there is no browser test coverage, and the "runs in CI" claim is wrong

- **The two skips test nothing:** `tests/e2e/test_drill_e2e.py` contains no tests, and `tests/a11y/test_axe.py` is a placeholder.
- **The skip messages are wrong:** they say "runs in CI", but `.github/workflows/ci.yml` doesn't install Playwright, so CI would skip them too.
- **CI can't catch QA-01:** CI's Postgres user is the superuser.

### QA-11 Low: S-0 sign-in error states are missing

- **What happens:** a sign-in refused for missing MFA (`amr`) or an unknown subject redirects to `/` and then to the sign-in page, with no message. (`LOGIN_REDIRECT_URL_FAILURE` is the default `/`.)
- **Expected:** design 14 specifies "Sign-in didn't complete. Contact your administrator." and "MFA not set up: blocked with setup instructions".
- **Note:** this is part of the untested Keycloak area.

### QA-12 Low (phase 1b risk): an old N/A rationale stays visible to customers

- **What happens:** `change_status` keeps `rationale` when a requirement moves away from `not applicable`, and `cust_requirement_status` returns `rationale` whatever the status.
- **Effect:** once the customer view exists, a withdrawn N/A rationale would still be shown to the bank.
- **When to fix:** before the bank-access gate.

### Observations (not defects)

- The setup step "Confirm your time zone" is per user. One admin sees "Setup: 5 of 6" while the responder sees setup complete. Decide whether that's intended.
- The footer shows the zone name ("Europe/Berlin"), not the abbreviation shown in design 4 ("CEST").
- The Keycloak realm uses `oidc-amr-mapper`. In Keycloak this mapper usually also needs authenticator reference values set in the authentication flow, or `amr` comes back empty. If it does, the app (correctly) refuses every sign-in. **Verify in staging.**
- C2 behaves as accepted: non-responders see absolute due times, from which the awareness time can be worked out.

---

## 6. Declared gaps (from the Engineer, confirmed, not counted as defects)

| Gap | Status | Matters for |
|---|---|---|
| Keycloak/OIDC sign-in and MFA, CI and Docker untested | Confirmed untested. QA-01 shows the sign-in path is broken under prod roles. | **15 Nov** |
| Browser accessibility pass not done | Confirmed. My partial pass found QA-04 and QA-05. Manual screen-reader and keyboard checks were not done. | 15 Nov (QA-04), ongoing |
| S-12 reclassify and S-15 CSV import | Not built. Planned for pilot week 1. | P1 within 4 weeks; real data |
| Audit trail has no "Who" filter or export | Confirmed | NFR-3 "exportable"; real-data gate |
| Time zone defaults to Europe/Berlin, not the browser zone | Confirmed. Users must confirm their zone (it's a checklist step). | Low |
| No screen to edit or deactivate users | Confirmed. Provisioning, including linking `oidc_subject`, needs an operator procedure. | 15 Nov (operations) |
| Phase 1b not started (customer workspace, S-10, exports, encryption of incident details, linked events, carry-forward, stale-evidence job) | Confirmed. The customer gets a placeholder page and the release tables are guarded. | Bank-access gate |
| Catalog: 29 DRAFT placeholder rows with `pending_oj_check: true` (the plan said about 35) | Confirmed | **15 Nov** (P1 can't start meaningfully without them) |
| Taxonomies have `licence_status: pending` and 3 SAMPLE items each | Confirmed. Seeding is correctly blocked; manual "Add a risk" works. | 15 Nov (P2 depends on seeding by 13 Nov) |

---

## 7. Requirements traceability (phase 0 and 1a scope)

Pass = verified, by the suite and/or my checks. Partial = works, with a defect or a missing piece.

| Requirement or decision | Screens | Result | Notes |
|---|---|---|---|
| R-1 statuses, citations, official link | S-3, S-4 | Pass | Content is placeholder (declared) |
| R-1 count summary, not a score | S-2, S-3 | Pass | Text with a denominator; no bars (lint) |
| R-1 N/A needs ≥20-character rationale, audited | S-4 | Pass | Suite and database CHECK |
| R-1 "evidence stale" system-only | S-3, S-4, S-2 panel | Pass | Computed on read |
| R-2 register seeded from a taxonomy | S-5 | Pass (gate) | Blocked until the licence is cleared (by design) |
| R-2 / OQ3 handling stages, last tested, last reviewed, owner, links | S-5, S-6 | Pass | Links are informational only |
| R-3 event type and awareness time with zone, stored in UTC | S-8, S-8a | Pass | DST skipped and repeated hours handled |
| R-3 24h, 72h, fix + 14d, notification + 1 month (clamp) | S-8, S-9, S-1 | Pass | Golden rows checked by hand, plus 15 extra cases |
| R-3 UTC + local time, countdown, states | S-1, S-7, S-9 | Pass | Tab title works in the browser |
| R-3 record filing times; the tool doesn't file | S-9 | Pass | QA-05 target size |
| R-3 awareness edit: reason, previous value, visible recompute | S-11 | Pass | |
| R-3 link to version and deployments | S-9 details | Pass | |
| R-3 "users informed" (Art. 14(8)) | S-10 | Deferred (1b) | Placeholder text on S-9 |
| R-4 customer read-only view | S-B1–B7 | Deferred (1b) | Placeholder page; D1 holds |
| R-X1 data-driven categories and sets | S-14 | Pass | 5(c) listed but disabled |
| OQ2 / D4 states for every admin; details for responders, checked on every request | S-7, S-9, S-1 | Pass | Revocation mid-session verified |
| D3 status per version | S-3, S-5 | Pass | Carry-forward deferred (1b) |
| D5 only access managers grant roles | S-14 users | Pass | Invitations deferred (deviation 13) |
| D6 idle 8h / 30 min, absolute 24h / 8h, polling doesn't reset | all | Pass | Step-up: unit-tested only; S-10 in 1b |
| D7 close states and reopen with reasons | S-9, S-13 | Partial | QA-02. Linked-event screens in 1b |
| D8 drills | S-7, S-8, S-8a | Pass | Events not in CSV import: S-15 not built |
| D9 audit stores the real actor; anonymised rendering | S-16 | Pass (unit) | Customer activity in 1b |
| D10 month-end clamp, pending legal | S-9 | Pass | Note shown on severe incidents |
| C1 customer reference at release | (DB) | Pass (DB) | Screens in 1b |
| C5 evidence as links only | S-4, S-6 | Pass | |
| C6 real events off by default | S-8, S-8a | Pass | Turning it on: QA-03 |
| C7 fix before awareness warns | S-9 | Pass | |
| Design deviation 15: a responder is required before setup completes | S-2, S-8a | Pass | S-8a is blocked when there is no responder |
| Deviation 13: invite step optional and hidden | S-2, S-14 | Pass | |
| NFR-1 SSO + MFA | S-0 | **Fail / not tested** | QA-01, QA-11; Keycloak not available |
| NFR-2 tenant isolation | all | Pass | Tested through a non-superuser role |
| NFR-3 audit append-only, views logged | S-16 | Partial | No "Who" filter or export (declared); QA-08, QA-09 |
| NFR-4 time handling | S-8, S-9 | Pass | |
| NFR-5 TLS, EU hosting, encryption at rest | – | Not tested | Infrastructure; app-level encryption in 1b |
| NFR-6 availability | – | Not tested | |
| NFR-8 notice on every screen | footer | Pass | Exports in 1b |
| Design 15 copy rules | all | Pass | |
| Design 16 accessibility (WCAG 2.2 AA) | all | Partial | axe is clean except target size; QA-04 reflow; screen reader not tested |
| S-15 CSV import, S-17 exports | – | Deferred | Week 1 / 1b |

---

## 8. Security checks

| Check | Result |
|---|---|
| `DEBUG` off in prod | Pass |
| Dev login absent in prod | Pass (routing and view) |
| Secret key from the environment; no hard-coded secrets | Pass |
| HSTS, SSL redirect, secure cookies (prod) | Pass (settings) |
| CSP, X-Frame-Options, nosniff, Referrer-Policy, no-store, COOP | Pass (response headers) |
| CSRF | Pass |
| XSS (a `<script>` event title) | Pass (escaped) |
| Open redirect on `/version/select` | Pass |
| Bandit | Pass (0 issues) |
| pip-audit | Not run (would send data to an external service) |
| Django admin absent | Pass |
| Least-privilege grants | Acceptable. `app_vendor` has row-level UPDATE on `user_account` and `role_grant` (all columns). Only app code limits this; column grants would tighten it. Low, and for the pentest. |

---

## 9. Recommendation

### 15 Nov drills-only pilot start: **NO-SHIP today; CONDITIONAL SHIP once the following are true**

**Must be true before 15 Nov:**

1. **QA-01 is fixed**, with a regression test that drives requests through a login role that isn't a superuser, and that test runs in CI.
2. **Sign-in is proven end to end in EU staging:** Keycloak, OIDC, MFA enforced and `amr` present. A refused MFA must be refused. This also covers the declared untested items. Infrastructure access is still pending in `CLAUDE.md`, so this is now the biggest date risk.
3. **CI runs green on GitHub Actions,** and the Docker image builds and runs in staging with `migrate`, `apply_db_security` and `load_catalog`.
4. **Catalog content (critical-path item 1) replaces the 29 DRAFT rows** and is loaded. Without it, P1 measures placeholder rows.
5. **An operator runbook exists** for provisioning users (including `oidc_subject`) and roles, because there is no user-management screen.
6. **The pilot agreement's C6 clause is signed.** This is a CPO item.

**Should be fixed before 15 Nov (the CPO may accept them for pilot week 1):**
- QA-04: 320 px reflow on S-8, S-8a and S-9. The out-of-hours drill will probably happen on a phone.
- QA-02: closed-event edits.
- QA-06: the live preview and warning.
- QA-05: target size.
- QA-07: the 500 error.

**Known and accepted for drills:**
- QA-08 to QA-12;
- reclassify and CSV import in week 1;
- taxonomy seeding waits for licence clearance (manual "Add a risk" works).

### Before the real-incident-data gate (around 7 Dec)

- The external pentest has passed and every critical and high finding is fixed. Add QA-09 (chain anchoring and scheduled verification) and the column-level grants note to its scope.
- QA-03 is fixed, so that turning on `real_events_enabled` is an audited operator action.
- Application-level encryption of incident details (phase 1b plan) is done.
- S-12 reclassify is built and tested.
- The audit "Who" filter and export are built (NFR-3, "exportable").
- QA-02 is fixed. With real events, a closed regulatory record must not change silently.
- Backups and point-in-time recovery, the break-glass procedure, and the on-call owner named in the pilot agreement are all in place.

### Before the bank-access gate (around 11 Dec)

- The phase 1b customer workspace (S-B0 to S-B7), S-10 mark informed with step-up, and the exports (PDF/UA and CSV with hashes) are built, and QA has re-tested them. That re-test must include HTTP-level non-inference tests ("no events" vs "unreleased only") and checks that exports contain no clocks or drills.
- QA-12 is fixed.
- Customer invitations are on, and customer MFA works through Keycloak.
- Legal has signed off on the disclaimer, "About this information" and the month rule (D-4).
- QA-11 sign-in error states are done.

---

## 10. Decisions for the CPO

1. **Accept the conditional ship for 15 Nov,** or move the date if staging access for Keycloak, Postgres and CI can't be in place in time to meet conditions 1 to 3.
2. **Decide whether QA-04 and QA-02 must be fixed before 15 Nov** or can slip to pilot week 1.
3. **Confirm the per-user time-zone setup step** (observation in section 5) is intended.
4. **Plan for possible slippage on taxonomy licence clearance (due 13 Nov)** and the catalog content (due 30 Oct). Both are on the critical path for P1 and P2.

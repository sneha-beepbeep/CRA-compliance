# Test report: phase 0 and phase 1a (stage 7, `/test`)

| Revision | Date | Commit tested | Verdict |
|---|---|---|---|
| **2 (re-test, current)** | 2026-10-21 | `7407241` (fixes in `dcca29c`) | **Conditional ship** for the 15 Nov drills-only start. No open defect blocks it. The remaining conditions are infrastructure and content (section R2-8). |
| 1 (first run, history) | 2026-10-21 | `e98b843` | No-ship today; conditional once QA-01 is fixed. Kept below, unchanged except that its headings are one level lower. |

**Tested against:** `docs/prd.md` (draft 1), `docs/design-spec.md` (draft 2), `docs/technical-plan.md`, decisions D1–D10 and C1–C8, build deviations 1–27, CPO option D, and the Cloudflare static-file decision in `CLAUDE.md`. Gates are from `docs/critical-path.md`.
**Tester:** QA. I did not write this code and changed no application code.

---

# Revision 2: re-test after the Engineer's fixes

## R2-1. Summary

- **Every first-run defect is fixed, and I verified each one independently:**
  - QA-01 to QA-08, QA-11 and QA-12 are **fixed**.
  - QA-09 is **partly fixed**, as the Engineer said: the anchoring command works, but it isn't scheduled yet and its output isn't stored outside the database.
  - QA-10 is **fixed in the repo**, but CI has still never run.
- **The critical sign-in defect (QA-01) is gone.** I rebuilt my own QA database with a login role that isn't a superuser, set up exactly as `db/sql/db_roles.sql` specifies, and took out last run's workaround. Sign-in now works through both Django's login and the OIDC backend path. Refusals for missing MFA, an unknown account and an inactive account all behave correctly.
- **Option D works as specified:**
  - the checklist has the same 5 steps for every admin;
  - the banner works with and without JavaScript;
  - zones are validated server-side;
  - confirmations are audited;
  - there's no open redirect, and nothing resets the idle timer;
  - the CSP is unchanged, and deadlines are unchanged.
- **No regressions:**
  - isolation, the responder boundary, D1, deadlines, drill guards, append-only audit, copy lint and timeouts all pass again;
  - axe found **0 violations and 0 sideways scrolling** across 64 page loads (18 screens, 2 roles, 320 px and 1280 px).
- **New defects: 0 Critical, 0 High, 0 Medium, 2 Low.**
  - QA-13: the operator commands need owner database credentials, and that isn't documented anywhere.
  - QA-14: the new sign-in policy covers more rows than it needs to.
- **Recommendation:** conditional ship for the 15 Nov drills-only start. What's left is infrastructure and content, which I could not test locally: staging sign-in through Keycloak, a real CI run, a real Docker build, catalog content, and the operator runbook.

## R2-2. Test suite results (local PostgreSQL 16.2)

| Run | Command | Result |
|---|---|---|
| Owner connection, including browser tests | `pytest` with `PLAYWRIGHT_BROWSERS_PATH=.playwright` | **664 passed, 1 skipped** (49 s) |
| Through the non-superuser login role, as CI selects | `TEST_LOGIN_ROLE=… pytest -m "postgres and not browser"` | **394 passed**, 271 deselected |
| Through the login role, everything except browser tests | `TEST_LOGIN_ROLE=… pytest -m "not browser"` | **630 passed**, 35 deselected |
| Prod-role tests alone, in login-role mode | `tests/isolation/test_prod_roles.py` | 7 passed. The test that is skipped in the owner run executes here. |

- **The Engineer's counts are confirmed:** 664 and 1, and 630.
- **The skip is legitimate:** it's a test that only means something in login-role mode, and it passes there.
- **35 browser tests now exist and run** (Playwright drill flow, time-zone banner, axe). Last time there were 0.
- **CI's second run selects only 394 tests** (`postgres and not browser`). The Engineer's 630 come from `not browser`. Both are fine: the tests left out don't make HTTP requests.
- **Not run:**
  - pip-audit: it would send dependency data to an outside service;
  - Keycloak with MFA, a GitHub Actions run, a real `docker build`: there's no infrastructure, and no Docker daemon.

## R2-3. Status of the first-run defects

Every result below comes from my own probes in the session scratchpad, not only from the Engineer's tests.

| ID | Sev. (run 1) | Status | How I verified it |
|---|---|---|---|
| QA-01 sign-in under prod DB roles | Critical | **Fixed** | `qa_app` is NOSUPERUSER and NOBYPASSRLS, with grants set exactly as in `db_roles.sql`. `force_login` and Django `login()` set `last_login` with no workaround. In the OIDC backend path (`get_or_create_user` with `amr=[pwd,otp]`; only the userinfo HTTP call is stubbed), sign-in succeeds and sets `last_login`. Without MFA, an unknown subject or an inactive account, sign-in is refused. `app_auth` still can't change any other column. A 39-request smoke pass across 3 personas through the login role returns the expected statuses. |
| QA-02 edits to closed events | Medium | **Fixed** | In the app: a filing POST gives 400 and nothing is saved, awareness edits are refused, a details POST gives 400, a GET on the edit screens redirects with "Reopen the event first", reassign gives 400, and take-over changes nothing. In the database (as `app_vendor` with the responder flag): filing, awareness, rationale and status changes, and updates to the detail row and deployment link, are all rejected with "closed event: reopen it first". Reopen with a reason still works. A drill outcome can still be recorded on a closed drill, as intended. |
| QA-03 audited system settings | Medium | **Fixed**, with new Low QA-13 | Run as owner, `set_system_setting` rejects: a reason under 20 characters, a missing operator, a non-boolean value, a disclaimer without `{vendor_legal_name}`, a disclaimer with other placeholders, and an unknown month rule. A valid change writes one `changed_system_setting` entry into **each** vendor's trail, shown in S-16 as "Changed system setting · Operator: …". After `real_events_enabled=true`, "+ Log event" appears and a real (non-drill) event is created. The hash chain stays intact. `--list` works. |
| QA-04 reflow at 320 px | Medium | **Fixed** | No sideways scrolling on any of 18 screens (S-2 to S-16, S-8 and S-8a, S-9 details, S-11, reassign, profile, help) at 320 px, as the responder and as an admin with the banner showing. |
| QA-05 target size | Low | **Fixed** | axe (WCAG 2.0/2.1/2.2 A and AA): 0 violations on 64 page loads. |
| QA-06 live preview and overdue warning | Low | **Fixed** | Type plus awareness time alone now shows the preview, with Title and Product still empty. An awareness time 30 h ago shows the warning and an acknowledgement tick-box (deviation 16). Saving without the tick is refused with "Tick the box…"; with the tick it saves. Without JS (S-8a), the first save shows the warning and saves nothing, and the second save with the tick works. |
| QA-07 500 error on a malformed version ID | Low | **Fixed** | `version=not-a-uuid` now gives a 404. |
| QA-08 readable audit trail | Low | **Fixed** | Actions have human labels and values show local plus UTC times. There's no raw dict output. Drill-outcome notes are masked for non-responders. |
| QA-09 hash chain doesn't detect deletion of the newest entries | Low | **Partly fixed** | `audit_verify_chain` is no longer callable by `app_vendor` (permission denied). `verify_audit_chain` exits 0 on an intact chain and 1 when a middle row is tampered with. After the newest row is deleted, a plain run still exits 0; **with `--anchors` from an earlier run** it exits 1 and reports "anchored head seq 32 is missing". It works only once it is scheduled and its output is stored outside the database, which isn't done yet. |
| QA-10 no browser tests; CI claim wrong | Low | **Fixed in the repo** | 35 browser tests collected and run. CI now installs Chromium and has a second, login-role pass. CI itself has still never run. |
| QA-11 S-0 error states | Low | **Fixed** | Messages for no MFA ("…is not set up… SMS codes are not accepted"), an unknown account ("You don't have access to this workspace…") and a generic failure (`?error=1`: "Sign-in didn't complete…"). Each is shown once. |
| QA-12 old rationale visible to customers | Low | **Fixed** | Leaving N/A clears the rationale (the history stays in the audit trail). Queried as `app_customer`, `cust_requirement_status` and `cust_ai_risk` return NULL for a leftover rationale when the status isn't N/A, accepted or not applicable. |

## R2-4. Option D (time-zone confirmation) and deviations 16, 22 and 23

| Check | Result |
|---|---|
| The checklist count is the same for all admins | **Pass.** With a responder assigned, both the responder and the admin see setup complete. Without one, both see "Setup: 4 of 5". The time-zone step is gone. |
| Banner with JS (browser zone Europe/Lisbon) | **Pass.** It shows for an unconfirmed admin and pre-selects Europe/Lisbon with the "Your browser reports…" note. Confirming returns to the same page and the banner disappears. Local times change to WET, and the UTC deadline values stay the same. The zone is stored and marked confirmed. |
| Banner without JS | **Pass.** The select defaults to UTC and the detected note stays hidden. Choosing Europe/Warsaw and confirming works and returns to the page. |
| Zone validation (server side) | **Pass.** `Mars/Olympus`, `posixrules`, `Etc/GMT+5`, an empty value, `Europe/Warsaw<script>` and `../../etc/passwd` all get a 400. None is saved or audited. A bogus `detected` value is stored as null. |
| Audit entries | **Pass.** `confirmed_time_zone` records the old zone, the new zone and the browser-detected zone. The profile route still records `set_time_zone`. |
| Open redirect via `next` | **Pass.** `//evil`, `/\evil`, `https://evil`, `javascript:` and `/%2F%2Fevil` all stay on the site. |
| Idle timer | **Pass.** The banner makes no background requests (none in a 5 s idle window apart from static files), and the strip poll still doesn't reset the idle timer. |
| CSP | **Pass.** `script-src 'self'` is unchanged, there's no inline script (`timezone.js` is a static file), and there are no console errors on any page. |
| Deadlines unchanged | **Pass.** UTC due times are identical before and after the zone change; only the local half changes. |
| Customers (deviation 22) | **Pass.** No banner. A customer POST to `/profile/time-zone` gives a 404. |
| UTC until confirmed (deviation 23) | **Pass.** An unconfirmed user sees "Times are shown in UTC and UTC until you confirm" and times like "18:39 UTC · 18:39 UTC". This is clunky but matches the approved deviation. |
| CSRF on the new endpoint | **Pass** (403 without a token) |

## R2-5. Regression checks

All of these pass again, through the non-superuser login role where requests are involved:

- **Isolation:** another tenant's event gives a byte-identical 404, the strip shows nothing from other tenants, a deployment can't attach to another vendor's customer, and selecting another vendor's version gives a 404.
- **`app_customer`:** denied the base tables and `cra_deadline_check`.
- **Responder boundary:** 9 detail and action routes give a non-responder a 404. Grant and revoke take effect on the next request and are audited. Non-access-managers can't grant the role.
- **D1:** the customer sees no strip, no event references and no Art. 14 content, and every vendor route gives a customer a 404.
- **Deadlines:** my 15 independent cases (clamps, DST, met at the exact minute, seconds truncation, skipped and repeated local hours) all pass, and the golden, property and differential suites pass.
- **Drill guards:** while the gate is off, events are forced to drills. `is_drill` can't change, as `app_vendor` or as the owner. Releasing a drill is rejected.
- **Audit append-only:** DELETE is denied for `app_vendor`, and tampering with a middle row is detected.
- **Copy lint:** in the suite, passes. I also read the new strings (banner, S-0 errors, deviation 16 text) and found no banned words.
- **Timeouts:** vendor idle 8 h, polling doesn't reset, 24 h absolute; customer 30 min.
- **Security:**
  - headers: CSP, X-Frame-Options, nosniff, Referrer-Policy, no-store, COOP;
  - CSRF and XSS escaping;
  - `/dev/login/` absent outside dev;
  - Bandit: 0 issues (in the suite run).

## R2-6. Docker review (no daemon, so read-through plus the Engineer's static tests)

**Correct as far as I can tell:**
- **Build context:** the `.dockerignore` allowlist (`*` then `!` for 9 paths) is the standard Docker pattern. `tests/unit/test_docker_image.py` reimplements Docker's matching and passes: no book-derived files, docs, tests, `.venv`, `.playwright` or `.localpg`, and no dev seed code (`devdata.py`, `seed_dev.py`). Nothing else imports `devdata`, so leaving it out is safe.
- **Build steps:**
  - multi-stage;
  - `uv sync --frozen --no-default-groups --no-install-project` installs runtime dependencies only;
  - `collectstatic` runs at build time with prod settings.
- **Runtime image:**
  - no uv;
  - code owned by root, running as `10001:10001`;
  - `PYTHONDONTWRITEBYTECODE` and `/dev/shm` for gunicorn, so nothing writes under `/app`;
  - the venv's Python is a symlink into the same base image, so it resolves in the runtime stage.

**Not verifiable without a daemon and network:**
- whether the pinned digests and the `uv:0.13.4` tag exist and match;
- that the image builds, starts and serves.

**CI has no `docker build` job.** I recommend adding one, so a bad pin or a missing file shows up before staging.

**Static files (CPO decision: Cloudflare, not WhiteNoise):** with `DEBUG=False`, the app doesn't serve `/static/`. I accept this as an infrastructure item, with two things to check in staging:
1. Cloudflare must serve `/static/` **on the same hostname** as the app, because the CSP is `script-src 'self'; style-src 'self'`. A separate static host would block htmx, `clocks.js` (countdowns, tab title) and `timezone.js`.
2. The files must reach Cloudflare from somewhere. The image's `/app/staticfiles` isn't served by gunicorn, so the origin for `/static/` (an upload step or a bucket) needs defining.

**Dev tooling note:** `manage.py runserver` can't start as the login role, because it can't read `django_migrations`. This is dev-only and not a defect, since gunicorn doesn't check migrations. Migrations and `apply_db_security` must run with owner credentials.

## R2-7. New defects found in the re-test

### QA-13 Low: operator commands need owner credentials, and nothing says so

- **Steps to reproduce:** run `manage.py set_system_setting --list`, `set_system_setting real_events_enabled true …` or `verify_audit_chain` with `DATABASE_URL` pointing at the application login role (as configured per `db_roles.sql`).
- **Actual:** `permission denied for table system_setting` (or `for function audit_verify_chain`). Nothing changes, so it fails safe.
- **Expected:** the command help or an operator runbook says it must run with the owner (migration) credentials, like `migrate` and `apply_db_security`. Today neither command, nor any doc, says so.
- **When it matters:** around 7 Dec, when an operator turns on real events under time pressure, and for the scheduled chain check.

### QA-14 Low: the new sign-in policy covers more rows than it needs to

- **Where:** `auth_last_login` in `db/sql/rls_policies.sql` is `FOR UPDATE TO app_auth USING (is_active)`.
- **Effect:** as the login role, `UPDATE user_account SET last_login=now()` touched **all 6 active users across both tenants**. The column grant keeps this to `last_login` only (I confirmed other columns are denied), so the impact is limited to forging "last login" times.
- **Suggestion:** narrow it if possible, or record it as accepted and add it to the pentest scope. `last_login` isn't used for P5; the audit trail is.

### Observations (not defects)

- **Phase 1b:** the closed-event trigger freezes every `art14_event` column. CRA Art. 14(8) informing users can happen after an event is closed. The S-10 design must not need to update `art14_event` on a closed event, or it will be blocked. `art14_users_informed` itself is not guarded.
- **Browser tests run as owner:** they use a dev server connected as the owner (deviation 18), so they don't exercise the login role. The test-client suite covers that path instead.

## R2-8. Recommendation

### 15 Nov drills-only pilot start: **CONDITIONAL SHIP**

No open application defect blocks the pilot. QA-13 and QA-14 are Low.

**Conditions still outstanding.** All are infrastructure or content I could not test locally:

1. **Sign-in in EU staging, end to end:** Keycloak, OIDC, MFA enforced, and `amr` actually present in the ID token. The realm's `oidc-amr-mapper` may need authenticator reference values set in the flow, or every sign-in will be refused. Also check a refused-MFA sign-in shows the S-0 message.
2. **CI has run green on GitHub Actions:** both pytest runs (owner with browser tests, and the login role), Bandit, pip-audit and the migration check.
3. **The Docker image builds and runs in staging, with:**
   - the app connected as a login role set up exactly per `db_roles.sql`;
   - `migrate`, `apply_db_security` and `load_catalog` run with owner credentials;
   - Cloudflare serving `/static/` on the same origin, with countdowns, tab title, htmx preview and banner checked in a browser there.
4. **Catalog content (critical-path item 1, due 30 Oct)** replaces the 29 DRAFT rows and is loaded.
5. **An operator runbook exists:**
   - provisioning users and roles, including `oidc_subject`;
   - which credentials each `manage.py` command needs (QA-13);
   - how to schedule `verify_audit_chain` and where its output goes.
6. **CPO items:** the C6 clause in the pilot agreement is signed. The taxonomy licence check (13 Nov) gates seeding; manual "Add a risk" works without it.

### Before the real-incident-data gate (around 7 Dec)

- The external pentest has passed and every critical and high finding is fixed. Scope includes QA-14, the column grants on `app_vendor`, and the chain anchoring.
- **QA-09 is completed:** `verify_audit_chain --anchors` runs on a schedule, and its output is kept outside the database, in storage the DB owner can't rewrite.
- `real_events_enabled` is turned on only through `set_system_setting`, with operator and reason.
- Application-level encryption of incident details (phase 1b) is done.
- S-12 reclassify is built and tested.
- The audit "Who" filter and export (NFR-3) are built.
- Backups and point-in-time recovery, the break-glass procedure, and the on-call owner are in place.
- **The Cloudflare scope is decided against C3.** If Cloudflare proxies all traffic, real incident data passes through TLS termination at a US-headquartered provider. Decide this before real data, not after.

### Before the bank-access gate (around 11 Dec)

- The phase 1b customer workspace (S-B0 to S-B7), S-10 mark informed with step-up, and the PDF/UA and CSV exports with hashes are built. QA re-tests them, including HTTP-level tests that customers can't infer unreleased incidents, and checks that exports contain no clocks or drills.
- Check S-10 against the closed-event trigger (observation above).
- Customer invitations are on, and customer MFA works through Keycloak.
- Legal has signed off on the disclaimer, "About this information" and the month rule (D-4). Use `set_system_setting` for any wording change.
- The bank's supplier-risk review has accepted the hosting and Cloudflare arrangement.

## R2-9. Decisions for the CPO

1. **Accept the conditional ship for 15 Nov.** The deciding factor is now staging access (Keycloak, Postgres, GitHub Actions), which is still pending. If staging isn't available in time for conditions 1 to 3, move the date.
2. **Cloudflare scope:** static files only, or all traffic? Decide before staging if possible, and at the latest before real data, because of C3 and the bank's review.
3. **Deviations 22 and 23 are still pending your approval.** QA verified that they behave as described and has no objection. The "UTC and UTC" wording is clunky but harmless.
4. **QA-13 and QA-14:** fix now, or accept until the pentest. QA suggests documenting QA-13 before 15 Nov, since the runbook is condition 5.

---
---

# Revision 1: first run (history, commit `e98b843`)

The first-run report follows, unchanged except that every heading is one level lower. Its defect statuses are out of date; section R2-3 above has the current statuses.


**Date:** 2026-10-21. **Build tested:** branch `pipeline-setup`, commit `e98b843` (phase 0 and 1a from `0ee7371`).
**Tested against:** `docs/prd.md` (draft 1), `docs/design-spec.md` (draft 2), `docs/technical-plan.md` (phase 0 and 1a scope), decisions D1–D10, C1–C8 and build deviations 1–13 in `CLAUDE.md`, and the gates in `docs/critical-path.md`.
**Tester:** QA. I did not write this code. I changed no application code.

---

### 1. Summary

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

### 2. What I tested and how

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

### 3. Test suite results

```
572 passed, 2 skipped in 16.70s
SKIPPED [1] tests/a11y/test_axe.py:8: Playwright not installed; run the axe-core pass in CI
SKIPPED [1] tests/e2e/test_drill_e2e.py:8: Playwright not installed; browser e2e runs in CI
```

- There were no failures.
- `makemigrations --check`: no changes detected.
- With Playwright installed, the two skipped files still test nothing. `test_axe.py` is a placeholder that skips itself, and `test_drill_e2e.py` contains no test functions (QA-10).

---

### 4. Independent verification of high-risk areas

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

### 5. Defects

Every defect below is new; none was declared by the Engineer. Severity is judged for the 15 Nov drills-only start unless stated otherwise.

#### QA-01 Critical: every sign-in fails under the documented production database roles

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

#### QA-02 Medium: closed events can be changed without reopening

- **Where:** `apps/art14/services.py` (`record_time`, `edit_awareness`, `update_details`, `reassign`) and the matching views. None of them check `status`.
- **Steps to reproduce:**
  1. Close an event as "determined not reportable".
  2. As the responder, POST to `/events/<id>/time` (early warning), `/events/<id>/awareness` (with a valid reason) or `/events/<id>/details`.
- **Expected:** rejected with "Reopen the event first". **Actual:** all three return 302 and save. After the filing POST the event is still `closed_not_reportable` but has an early-warning filing time, so its "stopped" clock becomes "met" or "late".
- **Risk:** the buttons are hidden for closed events, but a stale tab from during the incident can still submit. The changes are audited, so nothing is hidden. But a "closed – reporting complete" record can change after closure, which weakens the regulatory record.

#### QA-03 Medium: no audited way to change system settings

- **Where:** the `SystemSetting` docstring in `apps/tenancy/models.py` says settings are "changed by operators through `manage.py set_system_setting` (audited)". The command doesn't exist.
- **Effect:** each of these needs raw SQL with no audit entry:
  - turning on `real_events_enabled` (the C6 gate, around 7 Dec);
  - changing the disclaimer after legal sign-off;
  - changing `month_rule`.

  The technical plan says "Changes are audited and need no release."
- **Blocks:** the real-data gate, not 15 Nov.

#### QA-04 Medium: the incident screens don't reflow at 320 px (WCAG 1.4.10)

- **Where:** the vendor shell layout. At 320 px, the side nav and main column overflow:
  - 336 px wide on S-8 and S-8a;
  - 377 px on S-9;
  - also S-3 to S-6, S-11 and profile.
- **Steps to reproduce:** open `/events/start` at a 320 px viewport. `document.documentElement.scrollWidth` is 336, so the page scrolls sideways.
- **Expected:** design section 16 says S-7, S-8, S-8a and S-9 "must be fully usable on mobile, since the person who learns of an incident may be on a phone at night". S-7, S-2, S-14 and S-16 do reflow.
- **Note:** the Engineer declared the accessibility pass not done. This is a concrete finding from that pass, and it affects the P4 out-of-hours drill.

#### QA-05 Low: tap targets too small (WCAG 2.5.8)

- **Found by:** axe `target-size`, rated serious.
- **Where:**
  - the `<summary>` toggles "Early warning filing time", "Notification filing time" and "Final report filing time" on S-9 (3 to 4 nodes);
  - "Add a product" and "Add a version" on S-14.

  The filing-time toggles are the controls used most during an incident.
- **Elsewhere:** axe found no other violations on the 14 screens at either width.

#### QA-06 Low: the deadline preview and the ">24h ago" warning appear only once the whole form is valid

- **Where:** S-8 and S-8a (`_preview` needs `form.is_valid()`, and htmx doesn't send a request while required fields are empty).
- **Steps to reproduce:** on `/events/log?drill=1`, enter the type, date and time, then leave the field. The preview stays at "Enter the event type and awareness time…" until Product and Title are also filled.
- **Expected:** design 8.3 says the preview "updates as you type" from the type and awareness time. The warning that the early warning has already passed should show **before** saving.
- **Actual:** a user who clicks "Log … and start clocks" straight away never sees the warning.

#### QA-07 Low: a malformed version ID gives a server error

- **Steps to reproduce:** POST `/version/select` with `version=not-a-uuid`.
- **Expected:** 404. **Actual:** 500 (unhandled `ValidationError`).
- **Note:** the other bad-input POSTs I tried return 4xx. The `next` redirect is safe (`//x`, `/\x` and `https://x` all stay on the site).

#### QA-08 Low: the audit trail is hard to read

- **Shown as codes:** S-16 shows raw action codes (`edited_awareness_time`, `started_clock`) and Python dict values (`Before: {'awareness_at': '2026-10-21T17:36:00Z'}`), with times in UTC ISO only.
- **Design 13 calls for:** human-readable actions and local plus UTC times.
- **Not masked:** drill-outcome notes are free text and are never masked for non-responders. They are drill-only, so this is low risk.

#### QA-09 Low: the hash chain doesn't detect deletion of the newest entries

- **Steps to reproduce:** as the owner, disable `audit_event_no_update_delete`, delete the highest `seq` for a tenant, then run `audit_verify_chain(tenant)`. It returns NULL (intact).
- **Why:** this is inherent to a hash chain that isn't anchored anywhere outside the database. Anchoring would mean storing the latest hash elsewhere, for example in a periodic export or a log.
- **Also:**
  - nothing verifies the chain on a schedule;
  - `audit_verify_chain` can be called by any vendor session for any tenant ID (it returns only a `seq` or NULL).
- **Action:** add both to the pentest scope.

#### QA-10 Low: there is no browser test coverage, and the "runs in CI" claim is wrong

- **The two skips test nothing:** `tests/e2e/test_drill_e2e.py` contains no tests, and `tests/a11y/test_axe.py` is a placeholder.
- **The skip messages are wrong:** they say "runs in CI", but `.github/workflows/ci.yml` doesn't install Playwright, so CI would skip them too.
- **CI can't catch QA-01:** CI's Postgres user is the superuser.

#### QA-11 Low: S-0 sign-in error states are missing

- **What happens:** a sign-in refused for missing MFA (`amr`) or an unknown subject redirects to `/` and then to the sign-in page, with no message. (`LOGIN_REDIRECT_URL_FAILURE` is the default `/`.)
- **Expected:** design 14 specifies "Sign-in didn't complete. Contact your administrator." and "MFA not set up: blocked with setup instructions".
- **Note:** this is part of the untested Keycloak area.

#### QA-12 Low (phase 1b risk): an old N/A rationale stays visible to customers

- **What happens:** `change_status` keeps `rationale` when a requirement moves away from `not applicable`, and `cust_requirement_status` returns `rationale` whatever the status.
- **Effect:** once the customer view exists, a withdrawn N/A rationale would still be shown to the bank.
- **When to fix:** before the bank-access gate.

#### Observations (not defects)

- The setup step "Confirm your time zone" is per user. One admin sees "Setup: 5 of 6" while the responder sees setup complete. Decide whether that's intended.
- The footer shows the zone name ("Europe/Berlin"), not the abbreviation shown in design 4 ("CEST").
- The Keycloak realm uses `oidc-amr-mapper`. In Keycloak this mapper usually also needs authenticator reference values set in the authentication flow, or `amr` comes back empty. If it does, the app (correctly) refuses every sign-in. **Verify in staging.**
- C2 behaves as accepted: non-responders see absolute due times, from which the awareness time can be worked out.

---

### 6. Declared gaps (from the Engineer, confirmed, not counted as defects)

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

### 7. Requirements traceability (phase 0 and 1a scope)

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

### 8. Security checks

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

### 9. Recommendation

#### 15 Nov drills-only pilot start: **NO-SHIP today; CONDITIONAL SHIP once the following are true**

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

#### Before the real-incident-data gate (around 7 Dec)

- The external pentest has passed and every critical and high finding is fixed. Add QA-09 (chain anchoring and scheduled verification) and the column-level grants note to its scope.
- QA-03 is fixed, so that turning on `real_events_enabled` is an audited operator action.
- Application-level encryption of incident details (phase 1b plan) is done.
- S-12 reclassify is built and tested.
- The audit "Who" filter and export are built (NFR-3, "exportable").
- QA-02 is fixed. With real events, a closed regulatory record must not change silently.
- Backups and point-in-time recovery, the break-glass procedure, and the on-call owner named in the pilot agreement are all in place.

#### Before the bank-access gate (around 11 Dec)

- The phase 1b customer workspace (S-B0 to S-B7), S-10 mark informed with step-up, and the exports (PDF/UA and CSV with hashes) are built, and QA has re-tested them. That re-test must include HTTP-level non-inference tests ("no events" vs "unreleased only") and checks that exports contain no clocks or drills.
- QA-12 is fixed.
- Customer invitations are on, and customer MFA works through Keycloak.
- Legal has signed off on the disclaimer, "About this information" and the month rule (D-4).
- QA-11 sign-in error states are done.

---

### 10. Decisions for the CPO

1. **Accept the conditional ship for 15 Nov,** or move the date if staging access for Keycloak, Postgres and CI can't be in place in time to meet conditions 1 to 3.
2. **Decide whether QA-04 and QA-02 must be fixed before 15 Nov** or can slip to pilot week 1.
3. **Confirm the per-user time-zone setup step** (observation in section 5) is intended.
4. **Plan for possible slippage on taxonomy licence clearance (due 13 Nov)** and the catalog content (due 30 Oct). Both are on the critical path for P1 and P2.

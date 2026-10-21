# Release notes: pilot release 1 (phase 0 + 1a), drills-only start on 2026-11-15

| | |
|---|---|
| **Release** | Phase 0 (foundations) and phase 1a (vendor workspace), the pilot cut of the CRA Art. 14 / AI Act Art. 15 status-and-deadline dashboard |
| **Pilot** | One vendor of AI credit-scoring software (€36k, 3 months, starting 2026-11-15). One of its customers co-pays €15k after a successful pilot and that customer's legal review. |
| **Mode at launch** | **Drills only.** Real incident data is refused by the system until the pentest gate (around 2026-12-07). |
| **Code tested** | Branch `pipeline-setup`, commit `7407241` (application code from `dcca29c`), test report revision 2 |
| **Quality status** | QA verdict: **conditional ship** for the 15 Nov drills-only start. The CPO accepted it on 2026-10-21, and accepted QA-13 and QA-14 until the pentest. No open defect blocks launch. The remaining conditions are infrastructure, content and contracts (Part C). |
| **Prepared** | 2026-10-21 by the Launch Coordinator |

**How to read this document**

- **Part A** is written for the pilot vendor. It can be shared once the CPO approves it.
- **Parts B to F** are internal.
- Anything marked **[ASSUMPTION]** or **[OWNER/DATE NEEDED]** has not been confirmed and needs a decision from the CPO.
- 2026-11-15 is a **Sunday**. This document treats the go/no-go as Friday 13 Nov and the vendor kickoff as Monday 16 Nov **[ASSUMPTION: CPO to confirm]**.

---

## Part A. Pilot notes for the vendor

*Plain-language notes for the vendor's security, compliance and product leads. Share them with the vendor's pilot lead before the kickoff.*

### What this is

A shared workspace for your team to:

- record where you stand on the security requirements of the EU Cyber Resilience Act (CRA) and the AI Act;
- keep a register of the AI-specific risks to your credit-scoring system;
- see the CRA Art. 14 reporting deadlines for an exploited vulnerability or a severe incident.

It **supports** your own compliance work. It shows only what your team enters. **It is not a certification, conformity assessment, audit opinion or determination of compliance** with Regulation (EU) 2024/2847 (CRA) or Regulation (EU) 2024/1689 (AI Act). It doesn't file anything with any authority. You keep responsibility for your reports and for your legal judgement.

Every screen carries this notice: *"Status reflects information entered by [your company's legal name]. It is not a determination of compliance."* The wording is still being reviewed by legal and may change during the pilot.

### What you can use from the start of the pilot

- **Sign-in with multi-factor authentication** (an authenticator app or passkey; SMS codes are not accepted).
- **A short setup checklist** of 5 steps. One of them is naming at least one **incident responder**: the role that can see incident details.
- **Products and versions.** Status is tracked per product version.
- **The requirements list:** CRA Annex I Part I and Part II, and AI Act Art. 15. For each requirement you can:
  - set a status;
  - attach evidence as **links**;
  - see when evidence has gone stale;
  - mark it not applicable, with a written reason of at least 20 characters.

  The summary is a count, such as "evidence attached for 9 of 35 requirements". It is not a score.
- **The AI-risk register:** each risk has a handling stage, an owner, a "last tested" date and links to the requirements it relates to. There are no scores and no pass/fail.
- **Art. 14 deadline clocks for drills.** You can:
  - log a simulated exploited vulnerability or severe incident, or have any admin start a clock from the type, the awareness time, the product and an assigned responder;
  - see the 24-hour early warning, the 72-hour notification and the final report deadline, each in UTC and your local time, with a live countdown and the browser tab title;
  - record when you filed each report yourself;
  - correct the awareness time, with a reason, and see before and after how the deadlines move;
  - close an event as "reporting complete" or "determined not reportable" (with a reason), and reopen it with a reason;
  - record how a drill went.
- **Restricted incident details.** Every admin sees deadline states. Only people with the incident-responder role see titles, descriptions and filing details. Your designated access managers grant roles.
- **An audit trail** of who changed what, and when.

### What is not in this release

| Not included yet | When | What to do meanwhile |
|---|---|---|
| **Real incident data** | After the independent penetration test passes, expected around **7 Dec 2026**. We'll confirm in writing. | Use drills only. Keep running your existing Art. 14 process for any real event. The pilot agreement requires this. |
| **The workspace for your customer** (read-only view, "mark users informed" under Art. 14(8), the customer's own incident references) | After the pentest and legal sign-off, expected around **11 Dec 2026** | Nothing. Your customer has no access before then. |
| **Exports** (PDF and CSV) | With your customer's workspace | Use the screens. |
| **Linked events** (one situation that is both an exploited vulnerability and a severe incident) | Planned during the pilot | Log two separate drills. |
| **Changing an event's type** | Planned in the first weeks of the pilot | Close the drill as not reportable and log it again with the right type. |
| **Bulk import of statuses from a spreadsheet** | Planned in the first weeks of the pilot | Enter statuses on screen. |
| **Notifications of any kind** (email, SMS, push) | Not planned for this version. Your feedback decides whether they come later. | See "Known limitations". |
| **A screen to add or remove users** | Not yet | Ask us. We add and remove users for you **[OWNER/DATE NEEDED: response time to commit to]**. |
| **File uploads for evidence** | Later (2027) | Attach links to where the evidence lives. |

### Known limitations

1. **The dashboard does not notify anyone.** Someone on your side has to look at it, including outside office hours, to keep track of a 24-hour deadline. The pilot agreement names your out-of-hours owner, and we will run an out-of-hours drill with them.
2. **You are signed out after 8 hours without activity** (and after 24 hours in any case). The countdown screen doesn't keep you signed in by itself, so an unattended screen will end up showing the sign-in page, not the clocks.
3. **Any admin can work out when you became aware of an event.** Admins without the responder role don't see incident details, but they do see due times, and the 24-hour due time minus 24 hours is the awareness time. We have accepted this.
4. **Times are shown in UTC until you confirm your time zone.** A banner asks you once, and suggests the time zone your browser reports. Until you confirm, times appear as "UTC · UTC". The deadlines themselves don't change.
5. **Evidence is links only.** The dashboard doesn't open, check or store what a link points to.
6. **Deadlines are only as right as the awareness time you enter.** If that time is wrong, every deadline is wrong.
7. **Rules still awaiting legal confirmation:**
   - **The final report for a severe incident** is counted as one calendar month after the notification, clamped to month end (31 Jan becomes 28 or 29 Feb). The screen shows a note saying so.
   - **A fix recorded before the awareness time** is allowed with a warning. Check those cases with your legal counsel.
8. **Requirement entries.** Titles and citations have been prepared from the Official Journal texts. Any entry that is still awaiting a final check against the Official Journal is marked as such **[ASSUMPTION: depends on the catalog content due 30 Oct]**.
9. **AI-risk suggestions.** The register can be pre-filled from public AI-threat taxonomies (NIST AI 100-2, MITRE ATLAS), but only once licence checks are complete. You can always add risks by hand.
10. **Scope.** This version covers AI systems that assess the creditworthiness of individuals. It doesn't cover businesses' credit, fraud detection or insurance pricing. Whether the CRA applies to your product depends on what software you ship to your customers. Check your scope with legal counsel.
11. **Accessibility.** Screens have passed automated accessibility checks at phone and desktop widths. Manual screen-reader testing has not been completed.

### How to tell us about a problem

**[OWNER/DATE NEEDED: support contact, hours and response times for the pilot.]** If the dashboard is unavailable, nothing about your real reporting changes: during the drills-only period your existing Art. 14 process remains the one you rely on.

---

## Part B. Internal release notes

### B1. What is in this release

| Commit | Date | What |
|---|---|---|
| `0ee7371` | 2026-10-21 | Phase 0 and 1a build. Django 5.2, PostgreSQL 16 RLS and roles, deadline engine, audit hash chain, drill guards, vendor screens. Deviations 1–13. |
| `f773fd1` | 2026-10-21 | Pipeline status only |
| `e98b843` | 2026-10-21 | Removed a stray empty `test.py` |
| `dcca29c` | 2026-10-21 | Fixes for QA-01 to QA-12, option D time-zone banner, hardened Docker image. Deviations 14–27. |
| `7407241` | 2026-10-21 | Pipeline status only (Cloudflare decision). **This is the commit QA re-tested.** |
| `09ece5a` | 2026-10-21 | Test report revision 2 (documentation only) |

**Not on GitHub yet:** pushing waits until after `/ship`, on the CPO's instruction. As a result, `.github/workflows/ci.yml` has **never run**.

**The release candidate will change.** The Cloudflare static-file change (C-7 below) and the new CI `docker build` job create at least one new commit after the one QA tested. QA must smoke-test that commit in staging (C-9) before go.

### B2. Build deviations (all approved by the CPO)

No single register of deviations 1–27 exists in the repo. Only the ones below are described in `CLAUDE.md`, the code or the test report. **[OWNER/DATE NEEDED: Engineer to provide the full register of 1–27, with one line each, before `/graduate`, so this list can be completed.]**

| # | Deviation | Source |
|---|---|---|
| 4 | Dev-only login shortcut, never routed in prod (tested) | CLAUDE.md |
| 5 | `app_auth` database role for identity lookups before the tenant context is set | CLAUDE.md |
| 7 | `real_events_enabled` enforces C6 in code; off by default | CLAUDE.md |
| 9 | 20-character minimum for reasons and rationales | CLAUDE.md |
| 1–3, 6, 8, 10–12 | Approved at build review. Descriptions are not recorded in the repo. | — |
| 13 | "Invite a customer admin" setup step hidden; optional; never counts toward completion (`CUSTOMER_INVITATIONS_ENABLED=False`) | CLAUDE.md, code |
| 14–21 | Approved at defect-fix review. Recorded detail exists for: **16** (logging more than 24 h after awareness needs an acknowledgement tick-box) and **18** (browser tests run against a dev server connected as owner, not the login role). | test report |
| 22 | Customers get no time-zone banner (`/profile/time-zone` gives customers a 404) | test report |
| 23 | Unconfirmed users see times as "UTC · UTC" until they confirm | test report |
| 24 | gunicorn starts directly from the image's own environment | CLAUDE.md |
| 25 | `--worker-tmp-dir /dev/shm` | CLAUDE.md |
| 26 | `/app` is read-only at runtime | CLAUDE.md |
| 27 | Dev seed code (`devdata.py`, `seed_dev.py`) is excluded from the image | CLAUDE.md |
| Option D | The time-zone setup step is replaced by a one-time banner that uses the browser's detected zone; required setup steps are now 5 | CLAUDE.md |

Also accepted at `/plan`: C1, C2, C3, C5, C7 and C8. C4 (2 engineers) and C6 (drills until the pentest) were confirmed by the CPO.

### B3. Test results (test report revision 2, local PostgreSQL 16.2)

| Run | Result |
|---|---|
| Full suite as owner, including browser tests | 664 passed, 1 skipped (the skip is a login-role-only test that passes in that mode) |
| Through the non-superuser login role, excluding browser tests | 630 passed |
| CI's login-role selection (`postgres and not browser`) | 394 passed |
| Browser tests (Playwright drill flow, time-zone banner, axe) | 35 run |
| Accessibility (axe, WCAG 2.0/2.1/2.2 A and AA) | 0 violations across 64 page loads (18 screens, 2 roles, 320 px and 1280 px) |
| QA's own checks | About 190 pass. 1 expected failure (the open part of QA-09). |
| Bandit | 0 issues |
| Deadline engine | 21 golden rows plus 15 independent cases pass; the Python engine and the Postgres view agree |

QA independently re-verified isolation, the responder boundary, D1, drill guards, append-only audit, the copy lint, timeouts and the security headers.

### B4. Open defects (accepted by the CPO until the pentest)

| ID | Sev. | Issue | Mitigation now | Closes at |
|---|---|---|---|---|
| QA-09 (partial) | Low | Deleting the newest audit rows isn't detected unless `verify_audit_chain --anchors` runs on a schedule, with its output stored off the database. The command works; the scheduling and storage don't exist yet. | Runbook and schedule before 15 Nov (C-12) | Real-data gate |
| QA-13 | Low | `set_system_setting` and `verify_audit_chain` fail safe ("permission denied") under the app login role, and nothing documents that they need owner credentials | Runbook (C-12) | Pentest; a help-text fix is optional |
| QA-14 | Low | RLS policy `auth_last_login` lets `app_auth` update `last_login` for active users in every tenant (that column only) | Pentest scope; `last_login` is not used for P5 | Pentest |

**Observation carried to phase 1b:** the closed-event trigger freezes every `art14_event` column, so S-10 "mark informed" must not need to update `art14_event` on a closed event.

### B5. Untested at release (to be proven in staging per Part C)

- Keycloak/OIDC sign-in with MFA, and the `amr` claim in the ID token. The realm export's only redirect URI is `http://localhost:8000/oidc/callback/`.
- Any GitHub Actions run, including pip-audit (QA didn't run it, because it sends data to an outside service).
- `docker build` and running the image, including whether the pinned base-image digests and `uv:0.13.4` resolve.
- Cloudflare static-file serving, and the CSP after the static-origin change.
- NFR-5: TLS, EU hosting and encryption at rest. NFR-6: availability.
- Backups, point-in-time recovery and restore.
- Manual keyboard and screen-reader checks (NVDA/VoiceOver): not reported as done.
- Step-up re-authentication: unit-tested only (it's used by S-10, in phase 1b).

### B6. Gaps found while preparing this release

1. **No production way to provision users.** `OIDC_CREATE_USER=False`, there is no user-management screen, and the only seeding code (`seed_dev`) is dev-only and excluded from the image. Creating the vendor tenant, the first access manager and each user's `oidc_subject` link today needs `manage.py shell` or SQL run as owner. That is **not audited** in the tenant's trail. See decision F-2.
2. **CI does not trigger on this branch.** `ci.yml` runs on `pull_request` and on `push` to `main` only. Getting "CI green" needs a push plus a PR to `main`, which in turn needs the deferred push.
3. **Static file names are not content-hashed** (no `ManifestStaticFilesStorage`). Behind Cloudflare's cache, a deploy or rollback can serve old `clocks.js`/`app.css` with a new app, or the reverse. The static-host change (C-7) should include hashed file names or a cache-purge step.

---

## Part C. Go/no-go checklist for 15 Nov (drills-only start)

**Rule:** every item must be **Go** at the go/no-go meeting on **Fri 13 Nov [ASSUMPTION]**. A single No-go moves the start date, as QA advised; it does not open a waiver. Dates marked *(proposed)* are the Launch Coordinator's back-scheduling and need CPO confirmation.

**Owners:**

- **CPO**;
- **PM**;
- **Legal:** the CPO's lawyer;
- **Eng:** the 2 engineers. **[OWNER/DATE NEEDED: name which engineer owns each item.]**
- **QA**;
- **Ops:** the operator and on-call person for our side. **[OWNER/DATE NEEDED: not assigned to anyone yet.]**

| # | Item | Owner | Due | Done when |
|---|---|---|---|---|
| C-1 | **Hosting provider chosen** (C3: OVHcloud or Scaleway; AWS Frankfurt as fallback). Ask the bank's supplier-risk team for its preference, as C3 recommends. | CPO | 2026-10-27 *(proposed)* | Provider and region recorded in `CLAUDE.md` |
| C-2 | **EU staging and prod provisioned:** 2 app instances, managed PostgreSQL 16 (EU region, encrypted at rest, multi-AZ, PITR on), TLS, secrets store (`DJANGO_SECRET_KEY`, `DATABASE_URL`, `OIDC_RP_CLIENT_SECRET`, `KEYCLOAK_REALM_URL`, `ALLOWED_HOSTS`), container registry. App traffic does **not** go through Cloudflare. | Eng + Ops | 2026-11-02 *(proposed)* | Both environments reachable at their own hostnames; settings documented |
| C-3 | **Database roles applied per `db/sql/db_roles.sql`:** a login role that is NOSUPERUSER and NOBYPASSRLS, granted `app_auth` WITH INHERIT TRUE and `app_vendor`/`app_customer` WITH INHERIT FALSE, SET TRUE. `migrate`, `apply_db_security` and `load_catalog` run with **owner** credentials. The app's `DATABASE_URL` uses the **login role**. | Eng | 2026-11-04 *(proposed)* | `SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname='<login role>'` returns `f, f`. Sign-in works through the app. |
| C-4 | **Keycloak (EU) with MFA proven end to end in staging:** realm imported with staging/prod redirect URIs and web origins; TOTP required for new users; the `oidc-amr-mapper` configured (authenticator reference values in the browser flow if needed) so the **ID token** carries `amr` containing `otp` (or `webauthn`/`hwk`). Test 3 cases: MFA user signs in; user without MFA gets the S-0 "MFA not set up" message; unknown subject gets "You don't have access". | Eng, verified by QA | 2026-11-06 *(proposed)* | Decoded staging ID token shows `amr`; the 3 cases pass and QA has recorded them |
| C-5 | **CI green on GitHub Actions:** both pytest runs (owner with browser tests; login role), Bandit, pip-audit, the migration check and gitleaks. Needs the deferred push plus a PR to `main` (B6.2). | Eng (CPO approves the push) | 2026-11-04 *(proposed)* | A green run linked from the PR |
| C-6 | **CI `docker build` job added** (QA recommendation), so a bad digest pin or missing file fails before staging | Eng | 2026-11-04 *(proposed)* | The job is green in the same run |
| C-7 | **Static-file change (not built yet):** Cloudflare serves **only** static files, from a **separate hostname** such as `static.<domain>`. Its origin is EU object storage, filled from the image's `collectstatic` output at deploy. The app needs: `STATIC_URL` set to that origin; CSP `script-src` and `style-src` (and `img-src`, `font-src` if used) to include it; and content-hashed static file names or a purge step (B6.3). No app traffic, cookies or incident data go through Cloudflare. | Eng | 2026-11-04 *(proposed)* | Merged with a test asserting the CSP includes the static origin |
| C-8 | **Image built and run in staging:** deployed **by digest**, the digest recorded in a deploy log; `/app` read-only, running as uid 10001 | Eng + Ops | 2026-11-06 *(proposed)* | App serves; the deploy log has the digest |
| C-9 | **Browser check in staging by QA**, on the new commit: countdowns tick, tab title updates, htmx preview works, time-zone banner works, no CSP errors in the console, isolation smoke test through the login role | QA | 2026-11-10 *(proposed)* | QA notes appended to the test report |
| C-10 | **`real_events_enabled` confirmed off:** run `manage.py set_system_setting --list` as owner in **prod** | Ops | 2026-11-13 and again on the morning of 16 Nov | Output shows `real_events_enabled = None` (unset) or `False`. **Anything else is No-go.** |
| C-11 | **Catalog content** replaces the 29 DRAFT rows. OJ citations checked against Regulation (EU) 2024/2847 and 2024/1689; lawyer spot-checks the titles; `load_catalog` run in staging, then prod. | PM drafts, Legal reviews, Eng loads | **2026-10-30** (content); load by 2026-11-06 *(proposed)* | `grep -c DRAFT data/catalog/*.yaml` gives 0; any remaining `pending_oj_check` flags are deliberate and listed |
| C-12 | **Taxonomy licences** (NIST AI 100-2, MITRE ATLAS) checked and marked `cleared` (OWASP stays on hold). If not cleared, launch anyway with manual "Add a risk" and tell the vendor. | CPO, Eng marks the data | **2026-11-13** | Licence notes with attribution text filed |
| C-13 | **Operator runbook**, which closes QA-13 and part of QA-09. It covers: (a) provisioning the vendor tenant, users, the first access manager and the `oidc_subject` link, and deactivating users (see F-2); (b) which commands need **owner** credentials: `migrate`, `apply_db_security`, `load_catalog`, `set_system_setting`, `verify_audit_chain` (only the app runs on the login role); (c) scheduling `verify_audit_chain --anchors <previous.json>`, at least daily **[ASSUMPTION]**, with output written to storage the DB owner can't rewrite (for example object storage with retention lock), and exit code 1 paging Ops; (d) the deploy and rollback steps from Part E. | Eng drafts, Ops owns | 2026-11-10 *(proposed)* | Ops has done a dry run of each procedure in staging |
| C-14 | **Backups and point-in-time recovery:** PITR enabled in prod, plus one **test restore** into a separate instance, with `apply_db_security` and the login role re-created and `verify_audit_chain` passing on the restored copy | Eng + Ops | 2026-11-11 *(proposed)* | Restore time and steps recorded in the runbook |
| C-15 | **Break-glass procedure:** who can use owner credentials in prod, how access is requested and logged, and how any trigger disabled on `audit_event` is recorded. No Django admin in prod (by design). | Ops + CPO | 2026-11-11 *(proposed)* | Written; credentials held by the named people only |
| C-16 | **Pilot agreement signed with the C6 clause** (drills only until we confirm in writing; the vendor keeps its existing Art. 14 process) **and the on-call clause** naming the vendor's out-of-hours owner | CPO + Legal | **2026-11-15** (signed before the kickoff) | Signed copy on file |
| C-17 | **Vendor accounts provisioned in prod:** at least one access manager and at least one incident responder (needed to complete setup), each with MFA enrolled | Ops | 2026-11-13 | Each user has signed in once successfully |
| C-18 | **Pilot kickoff and drill plan agreed with the vendor:** kickoff agenda; P1 (all requirements given a status by week 4); P2 (10 or more risks by week 6); a **P4 drill schedule** with one exploited-vulnerability drill and one severe-incident drill, **at least one of them out of hours** with the named on-call owner; the weekly P5 check; when P6 and P8 get asked | CPO + PM | 2026-11-12 *(proposed)* | Plan sent to the vendor; out-of-hours drill date fixed |
| C-19 | **Our own support and on-call cover** for the pilot: contact, hours, response times (Part A placeholders filled) | CPO + Ops | 2026-11-12 *(proposed)* | Part A has no placeholders left |
| C-20 | **Monitoring live in prod:** uptime check on the app hostname; 5xx rate; sign-in failure count (S-0 error renders); `verify_audit_chain` exit status; database CPU, storage and backup status. Logs must not contain incident text (by design). | Eng + Ops | 2026-11-11 *(proposed)* | Each monitor has fired once in a test |
| C-21 | **Product README rewritten for end users.** It currently says "Nothing is built yet" and still carries the `docs/` pointer (see F-1). | Launch Coordinator, once the CPO authorises | Before `/graduate` | No placeholders; no `docs/` pointer |

### Launch-day sequence (target Mon 16 Nov [ASSUMPTION])

1. Ops runs `set_system_setting --list` as owner and confirms `real_events_enabled` is unset or false (C-10).
2. Ops runs `verify_audit_chain`, stores the output off the database as the first anchor, and confirms exit code 0.
3. Ops records the prod image digest in the deploy log.
4. The vendor kickoff runs a walkthrough and a first daytime drill end to end.
5. **For the first 72 h, watch:** sign-in failures, 5xx errors, CSP errors reported by the vendor, the countdowns ticking, the anchored chain checks, and any attempt to log a non-drill event (the system should refuse it).

---

## Part D. Later gates (separate go/no-go each)

### D1. Real-data gate (around Mon 7 Dec 2026)

Real (non-drill) Art. 14 events stay refused until **every** item is Go.

| # | Item | Owner | Due |
|---|---|---|---|
| R-1 | External pentest done (around 30 Nov–4 Dec), with **every critical and high finding fixed and re-tested**. Scope includes isolation, the responder boundary, authentication and step-up, **QA-14**, the column grants on `app_vendor`, and **audit chain anchoring (QA-09)**. | CPO commissions; Eng fixes | ~2026-12-04 |
| R-2 | QA-09 fully closed: anchors scheduled and stored off the database, and a check run by someone outside the DB-owner group has passed | Ops | Before R-8 |
| R-3 | Application-level encryption of incident details built and tested | Eng, QA | ~2026-12-04 |
| R-4 | S-12 reclassify built and tested | Eng, QA | Pilot weeks 1–2 |
| R-5 | The audit trail's "Who" filter and export (NFR-3) built and tested | Eng, QA | ~2026-12-04 |
| R-6 | Backups, PITR, break-glass and on-call owner all in place and re-confirmed (from C-14, C-15 and C-16) | Ops | ~2026-12-04 |
| R-7 | The C6 confirmation letter to the vendor ("pentest completed, critical and high findings remediated") | CPO | At the gate |
| R-8 | **Switch:** `manage.py set_system_setting real_events_enabled true --operator '<name>' --reason '<pentest ref, CPO approval, date>'`, run with **owner** credentials. Confirm it shows up in every vendor audit trail and that "+ Log event" appears. | Ops, with the CPO's written approval | At the gate |

### D2. Bank-access gate (around Fri 11 Dec 2026)

| # | Item | Owner | Due |
|---|---|---|---|
| B-1 | Phase 1b customer workspace (S-B0 to S-B7), S-10 "mark informed" with step-up, PDF/UA and CSV exports with hashes: built, and **re-tested by QA**. The re-test covers HTTP-level non-inference ("no events" vs "only unreleased"), exports containing no clocks or drills, and S-10 against the closed-event trigger. | Eng, QA | ~2026-12-09 |
| B-2 | Legal sign-off in writing: the disclaimer, "About this information", "What this is not", the month rule (D10), C7, and the hosted-API scope advice. Wording changes are applied with `set_system_setting`. | CPO + Legal | ~2026-12-04 |
| B-3 | The bank's supplier-risk review accepts the hosting provider and region (C3) **and** the Cloudflare static-files-only arrangement | CPO | Before B-5 |
| B-4 | `CUSTOMER_INVITATIONS_ENABLED` turned on; customer MFA proven through Keycloak (30-minute idle timeout) | Eng, QA | ~2026-12-09 |
| B-5 | Customer admins invited by the vendor | Vendor, with Ops support | At the gate |
| B-6 | Signed-off sample export shared early with the bank's legal team. **P6 and the bank's €15k depend on it.** | CPO | As soon as B-2 is done |

---

## Part E. Rollback plan

### E1. Blast radius at this release

Before the real-data gate, the system holds **drills, requirement statuses, AI-risk entries, evidence links and the audit trail. No real incident data.** Under C6 the vendor must keep its existing Art. 14 process, so an outage or a rollback cannot cause a missed regulatory deadline. The worst plausible harms are:

- a cross-tenant or role-boundary leak of the vendor's statuses or drill text;
- lost pilot data, which hurts P1, P2 and P5;
- damage to the vendor's trust in the product.

After 7 Dec the blast radius grows, and this plan must be reviewed at the real-data gate (R-6).

### E2. Triggers

| Trigger | Action | Decision owner |
|---|---|---|
| **Any sign-in without MFA succeeds**, or one tenant sees another tenant's data, or a non-responder sees incident details | **Take the service offline at once** (scale the app to 0 or switch to a maintenance page), then investigate. Don't just roll back. | Ops acts; CPO informed within 1 hour |
| `real_events_enabled` found true before the real-data gate | Set it back right away with `set_system_setting real_events_enabled false --operator … --reason …` (this is audited). Then check whether any non-drill events exist. | Ops; CPO informed |
| A deadline shown in the app differs from the golden file or a hand calculation (P3) | Roll back the image if the engine changed in the release; otherwise take the clocks out of use and tell the vendor | Eng + CPO |
| No one can sign in for more than 30 minutes after a deploy | Roll back the image (E3) | Ops |
| 5xx rate above 5% for 10 minutes after a deploy, or the health check fails **[ASSUMPTION: thresholds]** | Roll back the image (E3) | Ops |
| `verify_audit_chain` exits 1 | Freeze: no deploys, no restores. Keep the evidence (E4.3) and escalate to the CPO. | Ops + CPO |
| Countdowns or banner broken, or CSP errors after a static-file change | Forward-fix the static origin, CSP or cache (purge). An image rollback alone won't fix it. | Eng |

### E3. Image rollback

1. Every deploy is **by digest** (`<registry>/tracker@sha256:…`), never by tag. The deploy log records the current and the previous digest.
2. To roll back: redeploy the **previous digest** from the deploy log on every app instance; confirm the version on a health page or in the logs; re-run C-10 (`--list`) and a sign-in.
3. **Pair static files with the image.** With hashed static names (C-7), the old files are still on the static host and the old image references them. Without hashed names, re-upload the previous build's static files and purge the Cloudflare cache.
4. **Migrations decide whether an image rollback is safe.** From the first pilot release on, any migration must be backward-compatible with the image before it (add first, remove in a later release). If a release contains a migration the previous image can't run against, treat its rollback as a database decision (E4), not an image rollback.
5. **First release (16 Nov): there is no previous image.** "Rollback" means taking the service offline. The vendor carries on with its existing process as C6 requires, and we tell the vendor (E5).

### E4. Database rollback stance

1. **Default: forward-fix.** Don't reverse migrations in prod. The migrations include `apply_db_security` (roles, RLS, triggers), and reversing it half-way could weaken isolation.
2. **Restore from backup only** for corruption or data loss that can't be fixed forward, decided by the CPO. Restore **point-in-time into a new instance**, never over the live one. Then:
   - re-run `apply_db_security` with owner credentials;
   - re-create the login role per `db_roles.sql`;
   - run `verify_audit_chain`;
   - switch `DATABASE_URL`.
3. **The audit log is append-only and hash-chained. Never truncate, delete from, or restore over `audit_event` without keeping the chain.** Before any restore:
   - export `audit_event` in full (`pg_dump -t audit_event`) to the anchor storage;
   - store the latest `verify_audit_chain` output there too.

   After the restore:
   - entries after the restore point will show as missing against the last anchors. That is **expected**. Write it down in the incident record, with the pre-restore export as the evidence, and start a new anchor baseline;
   - add an audit entry for the restore through an audited path **[OWNER/DATE NEEDED: no command exists for this; the runbook must define one or the Engineer adds it]**.
4. Any disabling of the `audit_event` triggers is a **break-glass action** (C-15). It is logged outside the database, with who, when and why.

### E5. Telling the vendor

| When | What | Who |
|---|---|---|
| Within 1 hour of going offline or rolling back (business hours); by the next morning otherwise **[ASSUMPTION]** | What happened, what data (if any) was affected, that drills-only means no regulatory impact, and that their existing Art. 14 process remains the one they rely on | CPO (or delegate) to the vendor's pilot lead and named on-call owner |
| Any isolation or role-boundary incident | Facts, scope, and next steps. Legal decides on any further notification. | CPO + Legal |
| On restoration | What changed, any drill data to re-enter, any effect on P1, P2 and P4 timelines | CPO + PM |

### E6. When a rollback becomes a business question (link to the CEO's 90-day signals)

A technical rollback is not a kill signal on its own. Escalate to the CPO for a `/checkpoint` (Continue, Reshape or Abandon) if any of these happen:

- the pilot is paused for more than 5 working days **[ASSUMPTION]**;
- the vendor withdraws;
- the start slips so far that it can't produce pre-pilot or early-pilot evidence by **2027-01-19**.

The CEO's 90-day signals (`docs/ceo-review.md`, PRD section 9; deadline **2027-01-19**) are: fewer than 3 vendors will pilot or discuss price; most target vendors ship no software to their clients; an existing tool already combines AI-specific risk tracking with CRA Art. 14 tracking for this segment; vendors say their clients don't require this in procurement.

The vendor delivery-model answers (critical-path item 2, around 25 Nov) feed the second signal directly. Losing the pilot vendor would put the first at risk.

---

## Part F. Decisions and owners needed from the CPO

1. **F-1. The README is not rewritten.** The Launch Coordinator's job includes rewriting `README.md` for end users. This `/ship` run was limited to `docs/release-notes.md`, so the README still describes a product where "nothing is built yet" and still has the `docs/` pointer. Authorise a README rewrite before `/graduate` (C-21).
2. **F-2. User provisioning path.** Choose between:
   - (a) a small audited `provision_user` / `deactivate_user` management command, which is Engineer work before 13 Nov;
   - (b) a runbook procedure using `manage.py shell` as owner, which accepts that provisioning isn't in the tenant's audit trail until a screen exists.

   The Launch Coordinator recommends (a). It matters for D5 and the bank's review.
3. **F-3. Name the owners:** the Ops/on-call person on our side, and which engineer owns C-2 to C-9, C-13 and C-14.
4. **F-4. Confirm the dates:** go/no-go on Fri 13 Nov; kickoff on Mon 16 Nov (15 Nov is a Sunday); the proposed back-schedule dates in Part C. **If staging access (C-2, C-4, C-5) isn't in place by about 6 Nov, move the start date.** QA named staging access as the deciding factor.
5. **F-5. Hosting provider (C-1):** OVHcloud or Scaleway. Ask the bank's supplier-risk team first if the timing allows.
6. **F-6. Pilot support terms:** our support contact, hours and response times, and the user add/remove turnaround (Part A placeholders).
7. **F-7. Rollback thresholds:** the 5xx rate, the pause length that counts as a business escalation, and the vendor communication times marked [ASSUMPTION] in Part E.
8. **F-8. Deviation register:** ask the Engineer to provide one-line descriptions for deviations 1–3, 6, 8, 10–12, 14, 15, 17 and 19–21, which aren't recorded in the repo (B2).
9. **F-9. Push to GitHub:** CI (C-5) can't run until the branch is pushed and a PR to `main` is opened. That is the push the CPO deferred until after `/ship`.

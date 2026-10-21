# CRA and AI Act Security Tracker (working title)

A web dashboard to assess cybersecurity compliance status for software vendors who build complex decion-making AI systems for use by EU markets. It tracks the vendor's work on the security requirements of the EU Cyber Resilience Act (CRA) and the AI Act, records how the vendor handles AI-specific risks, and counts down the CRA Art. 14 reporting deadlines for exploited vulnerabilities and severe incidents.

**Status: pilot, drills only.** The vendor workspace is built and in a paid pilot with one vendor from mid-November 2026. Until an independent penetration test has passed (expected around 7 December 2026), the system accepts **simulated ("drill") events only** and refuses real incident data. The customer-facing view, exports and several other features are still to come (see [What's coming](#whats-coming)).

> **What this is not.** This is not a certification, conformity assessment, audit opinion or determination of compliance with Regulation (EU) 2024/2847 (Cyber Resilience Act) or Regulation (EU) 2024/1689 (AI Act). The dashboard **supports** your own work and shows only what your team enters. It doesn't file anything with any authority. You remain responsible for your reports and your legal judgement.

Every screen shows the notice: *"Status reflects information entered by {your company's legal name}. It is not a determination of compliance."*

## Who it's for

- **Vendor admins:** security, compliance and product leads at a company that sells AI credit-scoring software into the EU.
- **Incident responders:** the people at that vendor who handle an exploited vulnerability or severe incident and file the CRA Art. 14 reports.
- **Operators:** the people who deploy and run the service (see [For operators](#for-operators)).

## What you can do today

- **Track requirements.** See each requirement from CRA Annex I (Parts I and II) and AI Act Art. 15, with its exact citation and a link to the official text. For each one, per product version, you can:
  - set a status;
  - attach evidence as links;
  - see when evidence has gone stale;
  - mark it not applicable, with a written reason of at least 20 characters.

  The overview is a count, such as "evidence attached for 9 of 35 requirements". It is not a score.
- **Keep an AI-risk register.** List risks such as data poisoning or adversarial examples. Each one gets a handling stage, an owner, a "last tested" date and links to the requirements it relates to. There are no scores and no pass/fail.
- **Run Art. 14 deadline drills.**
  - Log a simulated exploited vulnerability or severe incident, and see:
    - the 24-hour early warning;
    - the 72-hour notification;
    - the final report deadline.
  - Each deadline appears in UTC and your local time, with a live countdown and the browser tab title.
  - Record when you filed each report yourself.
  - Correct the awareness time, with a reason, and see before and after how the deadlines move.
  - Close an event as "reporting complete" or "determined not reportable", and reopen it, with reasons.
  - Record how the drill went.
- **Keep incident details to responders.** Every admin sees deadline states. Only incident responders see titles, descriptions and filing details.
- **Review the audit trail.** It records who changed what and when. Entries can't be edited or deleted.

## What's coming

| Feature | Expected |
|---|---|
| Real (non-drill) incident data | After the penetration test passes, around 7 Dec 2026. The vendor is told in writing. |
| A read-only view for your customers, "mark users informed" under CRA Art. 14(8), and the customer's own incident references | After the penetration test and legal sign-off, around 11 Dec 2026 |
| PDF and CSV exports | With the customer view |
| Changing an event's type, and importing statuses from a spreadsheet | During the pilot |
| Linked events (one situation that is both an exploited vulnerability and a severe incident) | During the pilot |
| A screen to add and remove users | Not yet scheduled |
| File uploads for evidence | 2027 |
| Notifications (email, SMS, push) | Not planned for this version. Depends on pilot feedback. |

## Getting started (vendor users)

### Signing in

1. Your operator creates your account. There is no self sign-up.
2. Open the address your operator gives you and choose **Sign in**.
3. Sign in through the identity service. You need **multi-factor authentication**: on first sign-in you are asked to set up an authenticator app. **SMS codes are not accepted.**
4. If sign-in fails, the sign-in page tells you why:
   - MFA isn't set up;
   - you don't have access to this workspace;
   - or a general failure.

   Contact your operator.

**Sessions:** you are signed out after **8 hours without activity**, and after **24 hours** in any case. The countdown screen does not keep you signed in by itself.

### Roles

| Role | Can |
|---|---|
| **Admin** (every vendor user) | Work on requirements and AI risks. See every event's deadline states. Start a clock from the event type, the awareness time, the product and an assigned responder. |
| **Incident responder** | Everything an admin can, plus see and edit incident details, record filing times, correct the awareness time, close and reopen events. |
| **Access manager** | Grant or remove the incident-responder role on the **Users and roles** page. Changes take effect on the user's next page load and are recorded in the audit trail. |

### First steps

The overview page and the **Products and customers** page show a 5-step setup checklist ("Setup: 4 of 5 steps done"). Setup isn't complete until at least one person has the incident-responder role.

### Confirm your time zone

Until you confirm a time zone, times are shown in UTC, for example "18:39 UTC · 18:39 UTC". A **Confirm your time zone** banner suggests the zone your browser reports. Confirm it, or pick another. The deadlines themselves never change: they are fixed in UTC, and only the local-time display follows your choice. You can change the zone later on your profile page.

## Limitations

- **No notifications.** The dashboard doesn't notify anyone. Someone has to look at it, including outside office hours, to keep track of a 24-hour deadline.
- **An unattended screen gets signed out** after 8 hours idle, and then shows the sign-in page, not the clocks.
- **Any admin can work out the awareness time.** Admins without the responder role don't see incident details, but the 24-hour due time minus 24 hours gives the awareness time.
- **Deadlines are only as right as the awareness time you enter.**
- **Evidence is links only.** The dashboard doesn't open, check or store what a link points to.
- **Rules pending legal confirmation:**
  - the severe-incident final report is counted as one calendar month after the notification, clamped to month end (31 Jan gives 28 or 29 Feb). A note on screen says so;
  - a fix recorded before the awareness time is allowed with a warning. Check those cases with legal counsel.
- **Requirement wording.** Requirement titles may still be awaiting a final check against the Official Journal. Those entries are marked as such.
- **AI-risk suggestions** from public taxonomies (NIST AI 100-2, MITRE ATLAS) appear only once their licences are cleared. You can always add risks by hand.
- **Scope:** credit scoring of individuals only, not businesses' credit, fraud detection or insurance pricing. Whether the CRA applies to your product depends on what software you ship to your customers. Check with legal counsel.
- **Accessibility:** automated accessibility checks pass at phone and desktop widths. Manual screen-reader testing has not been completed.
- **User management** is done by your operator. There is no in-app screen for it yet.

---

## For operators

The stack is Python 3.12, Django 5.2, PostgreSQL 16 (row-level security and separate database roles) and HTMX, with Keycloak for sign-in over OIDC. Dependencies are managed with [uv](https://docs.astral.sh/uv/).

### Local development

```sh
uv sync                                  # runtime + dev dependencies (pytest, hypothesis, bandit, pip-audit)
uv sync --group localpg                  # optional: PostgreSQL 16 binaries inside .venv, no Docker needed
scripts/localpg.sh start                 # starts a throwaway local Postgres on 127.0.0.1:54329, prints a DATABASE_URL
export DATABASE_URL='<the URL printed above>'
uv run python manage.py migrate          # also applies roles, RLS policies, views and guards
uv run python manage.py seed_dev         # dev only: loads the catalog, creates two sample vendor tenants
uv run python manage.py runserver
```

- **Sign in without Keycloak:** open <http://127.0.0.1:8000/dev/login/> and pick a seeded user, for example `responder@acme.example` (incident responder and access manager) or `admin@acme.example` (admin, sees the time-zone banner). The dev login exists only with the default dev settings (`tracker.settings.dev`) and is never routed in production.
- **Stop the database** with `scripts/localpg.sh stop`.
- **Docker instead of local binaries:** `docker compose -f infra/docker-compose.dev.yml up -d` starts PostgreSQL 16 and Keycloak 26, with the `tracker` realm imported from `infra/keycloak/tracker-realm.json`. Use `DATABASE_URL=postgres://tracker:tracker@127.0.0.1:5432/tracker`.
- **Run as the database owner locally.** `runserver` can't start as the restricted login role.

### Running the tests

Tests that need PostgreSQL skip unless `DATABASE_URL` is set.

```sh
uv run pytest                                            # everything installed; browser tests skip without Playwright
TEST_LOGIN_ROLE=tracker_test_app uv run pytest -m "not browser"
                                                         # every request goes through a non-superuser login role,
                                                         # as in production (the role is created by the test setup)

# Browser tests (Playwright drill flow, time-zone banner, axe accessibility pass)
uv sync --group browser
PLAYWRIGHT_BROWSERS_PATH=.playwright uv run playwright install chromium
PLAYWRIGHT_BROWSERS_PATH=.playwright uv run pytest -m browser
```

CI (`.github/workflows/ci.yml`) runs on pull requests and on pushes to `main`. It runs both pytest passes, Bandit, pip-audit, a migration check and a secret scan.

### Production image

```sh
docker build -f infra/Dockerfile .
```

The image:

- **build:** multi-stage, with digest-pinned base images, runtime dependencies only, and static files collected at build time;
- **run:** gunicorn on port 8000 as uid 10001, with `/app` read-only;
- **contents:** a `.dockerignore` allowlist leaves out tests, docs, local environments and the dev seed code.

**Required environment:**

| Variable | Notes |
|---|---|
| `DJANGO_SECRET_KEY` | |
| `DATABASE_URL` | The **application login role**, not the owner |
| `ALLOWED_HOSTS` | Comma-separated |
| `KEYCLOAK_REALM_URL` | |
| `OIDC_RP_CLIENT_ID` | Default: `tracker` |
| `OIDC_RP_CLIENT_SECRET` | |

- **Static files:** the app doesn't serve `/static/` in production. Serve the collected files (`/app/staticfiles` in the image) from a static host.
- **Sign-in:** the app refuses any sign-in whose ID token doesn't carry an MFA method in its `amr` claim. Configure Keycloak to include it.

### Database roles and operator commands

The app connects as a **login role** that is not a superuser and can't bypass row-level security. It is set up as `db/sql/db_roles.sql` describes: granted `app_auth` WITH INHERIT TRUE, and `app_vendor` and `app_customer` WITH INHERIT FALSE, SET TRUE.

**Every command below needs the database owner's credentials.** Point `DATABASE_URL` at the owner when you run it. Under the app's login role these commands fail with "permission denied" and change nothing.

| Command | What it does |
|---|---|
| `python manage.py migrate` | Applies migrations, including the database security objects |
| `python manage.py apply_db_security` | Re-applies roles, RLS policies, customer views, the deadline-check view, and the audit and drill guards |
| `python manage.py load_catalog` | Loads requirement and taxonomy data from `data/catalog/` |
| `python manage.py set_system_setting --list` | Shows the global settings: `real_events_enabled`, `disclaimer_template`, `month_rule`, `month_rule_note` |
| `python manage.py set_system_setting <key> <value> --operator '<name>' --reason '<at least 20 characters>'` | Changes a setting and records it in every vendor's audit trail. **`real_events_enabled` must stay off** (unset or `False`) until the penetration-test gate is passed. |
| `python manage.py verify_audit_chain [--anchors previous.json]` | Checks every vendor's audit hash chain and prints the chain heads as JSON. Exits 1 on any break. |

**Scheduling the chain check:** run `verify_audit_chain` on a schedule. Store each run's output somewhere the database owner can't rewrite, and pass the previous output back with `--anchors`. That is the only way to detect deleted newest entries.

**Users:** there is no user-management screen yet. Operators create user accounts and link each one to its identity-provider subject (`oidc_subject`).

**For the team running the pilot:** release scope, the go/no-go checklist and the rollback plan are in [`docs/release-notes.md`](docs/release-notes.md).

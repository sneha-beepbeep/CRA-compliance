# Product Development Pipeline

You are the **orchestrator** for a simulated software product team. The user is the **CPO** (Chief Product Officer) — the final approver at every gate. You never advance to the next stage without their explicit approval.

## Pipeline stages

1. `/ceo-review <idea> for <user> within the context of <domain>` — CEO → `docs/ceo-review.md` (business viability challenge on the raw idea, before any product work begins)
2. `/kickoff` — Product Manager → `docs/opportunity-brief.md`
3. `/prd` — Product Manager → `docs/prd.md`
4. `/design` — Designer → `docs/design-spec.md`
5. `/plan` — Engineer, in Plan Mode → technical plan (presented for approval, no code written yet)
6. `/build` — Engineer → implementation
7. `/test` — QA → `docs/test-report.md`
8. `/ship` — Launch Coordinator → `docs/release-notes.md` + rollout/rollback checklist
9. `/graduate` — Orchestrator, no subagent → archives `docs/` and the `.claude/` scaffolding, replaces `CLAUDE.md` with a provenance note

## Exception paths

- `/checkpoint [reason]` — CEO, usable at any stage from 1 onward → appends to `docs/ceo-review.md`. Not part of the numbered sequence: it runs on demand, whenever the CPO wants to re-check business viability rather than just the current artifact. Verdict is Continue, Reshape (resume at stage N), or Abandon.

## Current status

- **Stage:** 8, `/ship`: **shipped (release prepared) on 2026-10-21.** `docs/release-notes.md` is the release package for the 15 Nov drills-only pilot. Go-live depends on the 21-item go/no-go checklist in Part C; the decider is staging, Keycloak and CI working by about 6 Nov, otherwise the start date moves. Next: `/graduate` when the CPO chooses, or further `/build` for the pre-launch items.
- **Last artifact:** `docs/release-notes.md`.
  - **Part A:** vendor-facing notes.
  - **Part B:** internal notes. The release candidate will move past `7407241` once the static-file change and the CI `docker build` job land, so QA needs to smoke-test it in staging.
  - **Part C:** go/no-go checklist for 15 Nov.
  - **Part D:** real-data gate (around 7 Dec) and bank-access gate (around 11 Dec).
  - **Part E:** rollback plan.
  - **Part F:** decisions for the CPO.
- **CPO approval pending on (Part F):**
  1. a README rewrite for end users before `/graduate`;
  2. adding users in production: (a) an audited command (recommended) or (b) a shell runbook with no audit record;
  3. naming the Ops/on-call owner and an engineer per item;
  4. dates: 15 Nov is a Sunday (proposed go/no-go Fri 13 Nov, kickoff Mon 16 Nov);
  5. the hosting provider (OVHcloud or Scaleway);
  6. vendor support terms;
  7. rollback thresholds;
  8. the Engineer to supply one line for each undocumented deviation;
  9. a pull request to `main` (CI runs only on PRs and pushes to `main`).

  Gaps found: there's no production way to add users; static file names aren't content-hashed (risk of a stale Cloudflare cache on rollback); the Keycloak realm only has a localhost redirect address.
- **Pre-pipeline context (for `/ceo-review` and `/kickoff`):** this repo joined the pipeline mid-flight on 2026-10-20. It already holds a SQLite knowledge base of AI risks, innovations, mitigations and barriers extracted from Chapters 1, 2 and 11 of the source book (`schema.sql`, `*.json`, `build_db.py` → `regtech_cyber.db`). The CPO confirmed this repo is the "Provably Secure" / Continuous Hardening as a Service product: the existing database is intended to become the hardened flagship case study. `docs/cpo-draft-prd.md` is the CPO's own pre-pipeline pitch, reformatted. It is **input** to `/kickoff` and `/prd`, not an approved artifact. The open challenge for the CEO is whether hardening a database of public reference content proves anything to buyers. *(Superseded 2026-10-21. See the decision log: the CPO reversed the "hardened flagship case study" premise during `/ceo-review`.)*
- **Decision log:**
  - 2026-10-20 — **Pre-pipeline build (CPO decision, ahead of the gates):** added the `finding` table plus the `security_changelog` and `cra_deadline_check` views to `schema.sql`, fed from `findings.json` (empty). Built before `/prd`, `/design` and `/plan` at the CPO's explicit request. Later stages should treat it as an existing component to confirm or revise, not as approved scope. Assumption to confirm in `/prd`: CRA Art. 14 applies to manufacturers of products with digital elements; whether a hosted database service falls under the CRA, NIS2 or both is unresolved.
  - 2026-10-21 — **CPO reversed a pre-pipeline premise (during `/ceo-review`):** `regtech_cyber.db` is a reference guide and will not be hardened as a flagship case study. The "Provably Secure" / public-changelog thesis from `docs/cpo-draft-prd.md` is dropped. The pre-built `finding` table and the `security_changelog` / `cra_deadline_check` views remain unapproved scope. They may be reused if a CRA Art. 14 tracker idea comes back through `/ceo-review`.
  - 2026-10-21 — **`/ceo-review` verdict: Do not pursue (as currently framed).** The idea took four different framings in four rounds. The final one was "a database security indicator indicating compliance with the CRA for European B2B software companies handling sensitive data", with healthcare as an example domain and a hypothetical pilot. The CEO found that it misapplies the CRA: the CRA doesn't govern databases, "CRA breaches" isn't a CRA concept, and the example pilot is likely SaaS. The indicator's audience (customer service) can't act on it, and showing live vulnerability status to everyone with database access would expose it. Differentiation and demand were never evidenced, and there was no domain clause. Pipeline stopped; the CPO has not chosen to override. Revisit conditions are in `docs/ceo-review.md`.
  - 2026-10-21 — **Fresh `/ceo-review` verdict: Pursue with caveats.** Idea: a CRA compliance tool for software manufacturers building high-risk AI systems, in the domain of creditworthiness assessment (for example Taktile, Scienaptic). It has three functions: (1) supporting the CRA essential requirements plus AI Act Art. 15, (2) tracking AI-specific risks, (3) CRA Art. 14 reporting. The CPO's evidence of demand comes from bank conversations (mBank, DKB, Sächsische Aufbaubank); no vendor has been spoken to yet.
    - **Hard gate before `/prd`:** 3–5 vendor conversations, including one priced pilot candidate; otherwise run `/checkpoint`.
    - **Other binding caveats:**
      - how much of the target market is SaaS, which the CRA largely doesn't cover;
      - exact citations throughout (CRA Art. 12/13/14, AI Act Art. 15 and Annex III 5(b)), with Recital 51 as context only;
      - reporting must meet the 24h early-warning clock, not just 72h;
      - the tool "supports" compliance, it doesn't "ensure" it, and its liability limits must be defined;
      - the competitor gap must be verified, including against Modulos, Saidot, trail, Credo AI and Holistic AI;
      - the niche must be sized;
      - the rights to the book-derived content must be confirmed.
    - **Existing components:** `cra_deadline_check` is a candidate for the reporting function. `security_changelog` has no role. Both stay unapproved scope. `regtech_cyber.db` is a reference asset and will not be hardened.
    - The 90-day kill signals are in `docs/ceo-review.md`.
  - 2026-10-21 — **`/kickoff` approved (opportunity brief, revision 3).** The CPO made these decisions at the gate:
    - Credit scoring is the beachhead, built so it can extend to other Annex III categories.
    - The MVP is a status and deadline dashboard. Drafting reports and filing with ENISA are out of scope.
    - Alerts are deferred to v2, depending on vendor demand.
    - Every admin of the AI credit-scoring product can see the dashboard.
    - There is no cloud-only fallback. The CPO asserts that all target vendors ship software; this is not yet verified and must be checked in the vendor conversations.
    - Following the CPO's lawyer, a hosted API is treated as in CRA scope when it is paired with bank-side vendor software that needs it to work.
    - The SaaS line was revised: CRA scope depends on whether the vendor ships software, not on SaaS versus non-SaaS.
  - 2026-10-21 — **Vendor gate evidence (CPO report, not yet ruled on):** the CPO held confidential conversations with 3 credit-scoring vendors, all open to a pilot. The CPO puts the average pilot price at €50,000, taken from Gera's published pricing guide for mid-market *deployers* (https://geracompliance.com/blog/ai-compliance-pricing-breakdown-2026). It is a market benchmark, not a figure the vendors gave. Not yet recorded: whether each vendor ships software to banks, and what their delivery models are. Whether this meets the CEO's hard gate is undecided.
  - 2026-10-21 — **Vendor-stated price signal (CPO report):** one of the three vendors said it is open to a 3-month pilot with one of its banking clients at €12,000 per month (€36,000 in total). This is the vendor's own figure, and it meets the "priced pilot candidate" part of the CEO's hard gate. Still to confirm in `/prd`: the banking client's role in the pilot.
  - 2026-10-21 — **CPO assumptions for `/prd`:** (1) the vendor pays us for the pilot; (2) each vendor ships software to banks or to another highly regulated client. Both are CPO assumptions, not confirmed with the vendors. Assumption 2 widens the client base beyond banks. `/prd` must check that in-scope systems still fall under AI Act Annex III 5(b), which covers credit scoring of individuals by any deployer, not only banks.
  - 2026-10-21 — **`/prd` approved (draft 1).** The approval accepts the PRD's proposed answers to OQ1–OQ3:
    - **OQ1:** bank admins get a read-only view of their own deployment, and see incidents only after the vendor marks affected users as informed under Art. 14(8).
    - **OQ2:** every vendor admin sees deadline states; only a vendor "incident responder" role sees full incident details.
    - **OQ3:** AI-risk status is a handling stage plus a "last tested" date, with no scores and no pass/fail.

    The CPO also confirmed:
    - **Payer:** the vendor pays for the pilot (€12k/month for 3 months, €36k in total).
    - **Bank's role (OQ5):** co-payer. The bank pays €15k once the pilot succeeds and its legal team has reviewed it. This makes success metric P6 (the bank's written view on accepting the dashboard as supplier evidence) commercially load-bearing.
    - **Start date:** 2026-11-15, so the pilot ends around 2027-02-15. That is after the 90-day kill-signal deadline of 2027-01-19, so those signals are judged on evidence from before and early in the pilot.

    **Still open:** the vendors' delivery models (OQ4).
  - 2026-10-21 — **`/design` approved (draft 2).** The CPO's answers to D1–D10:
    - **D1:** customers never see Art. 14 deadline states or filing times.
    - **D2:** the customer-visible fields are confirmed as proposed.
    - **D3:** status is tracked per product version.
    - **D4:** any vendor admin can start a clock from type, awareness time, product and an assigned responder only. Incident details require the responder role, checked on every request.
    - **D5:** the vendor grants roles.
    - **D6:** idle timeouts of 8h for vendor roles and 30 min for customer roles, with re-authentication before "mark informed".
    - **D7, D8:** deferred to the engineer at `/plan`.
    - **D9:** the vendor can see customer activity, and the customer can switch it to "organisation only" (the default until chosen).
    - **D10:** month-end clamp for the one-month deadline, pending legal confirmation.

    By approving draft 2, the CPO also accepted the designer's proposals on the three items that were still open:
    - customer admins are invited by the vendor and sign in through our identity service with MFA for the pilot; the customer's own identity provider comes later. Designated vendor access managers grant roles.
    - the D9 rules as specified in section 9.6.
    - the pending deviations from the PRD in section 18, including #15: at least one incident responder is required at setup.
  - 2026-10-21 — **`/plan` approved (technical plan, draft 1, in `docs/technical-plan.md`).**
    - **Stack:** Django 5.2 LTS, PostgreSQL 16 (tenant isolation through row-level security and a separate customer database role), HTMX, Keycloak in the EU, WeasyPrint for PDF/UA.
    - **Deadline engine:** pure Python is authoritative; the Postgres `cra_deadline_check` view is an independent check.
    - **D7:** close states plus reopen go in the pilot cut; linked events get their table now and their screens in phase 1b.
    - **D8:** drill mode is in the pilot cut; Art. 14 events stay out of CSV import.
    - **Phasing:** 15 Nov is drills only; real incident data after the pentest (around 7 Dec); bank access after the pentest and legal sign-off (around 11 Dec).
    - **The plan's recommendations are accepted with its approval:**
      - C1: customers get their own incident reference, assigned at release;
      - C2: countdowns revealing the awareness time to non-responder admins is accepted as a known limitation;
      - C3: EU-headquartered hosting (OVHcloud or Scaleway), with AWS Frankfurt as fallback;
      - C5: evidence is links only in the pilot;
      - C7: a fix recorded before awareness is allowed with a warning and referred to legal;
      - C8: NIST AI 100-2 and MITRE ATLAS as taxonomy seeds after a licence check; OWASP on hold.
    - **C4 and C6, confirmed by the CPO on 2026-10-21:** 2 engineers; the pilot agreement will state that no real incident data is loaded until the pentest passes.
    - **Pre-built schema:** `finding` and `cra_deadline_check` move into the tracker; `security_changelog` and `findings.json` will be removed.
  - 2026-10-21 — **Build review (phase 0 and 1a):**
    - The CPO approved all 12 build deviations, including 4 (dev-only login), 5 (`app_auth` role), 7 (`real_events_enabled` enforces C6 in code) and 9 (20-character minimum reasons).
    - The "Invite a customer admin" setup step is hidden in the pilot cut and becomes optional: it never counts toward checklist completion. This is deviation 13 against design F-1.

  - 2026-10-21 — **`/test` → loop back to `/build`.** QA verdict: no-ship today; a conditional ship for the 15 Nov drills-only start (1 Critical, 3 Medium, 8 Low defects). The CPO chose to loop back to `/build` to fix them. Asked to "remove the pre-pipeline build from this branch", the CPO confirmed that nothing more needs removing. The files were already cleaned in `/build`, and git history stays as the record. The Postgres `cra_deadline_check` view in the tracker stays.
  - 2026-10-21 — **Defect-fix review:** the CPO approved deviations 14–21 and chose time-zone option D: the "Confirm your time zone" setup step is removed, the time zone is detected from the browser with a one-time confirmation banner, and the required setup count becomes 5. The CPO asked for a Docker image proposal (build context including `.playwright/`, image hygiene) to review before anything is implemented.
  - 2026-10-21 — **Docker image:** the CPO pre-approved the Engineer's recommended option (an allowlist `.dockerignore` and a multi-stage, digest-pinned, non-root Dockerfile) and asked for a commit. It brings runtime deviations 24–27: gunicorn starts directly from the image's own environment, `--worker-tmp-dir /dev/shm`, `/app` is read-only, and the dev seed code isn't in the image.
  - 2026-10-21 — **Static files:** the CPO chose to have the hosting platform's proxy serve `/static/` in production, using **Cloudflare**, not WhiteNoise. No app change is needed; staging needs the proxy rule. **Decided the same day:** Cloudflare proxies **only static files** (CSS, JS, images), never app traffic. The app, its TLS and all incident data stay on the EU-headquartered platform, in line with C3. Follow-up for staging: serve static files from a separate hostname behind Cloudflare, and point the app's `STATIC_URL` and the CSP `script-src`/`style-src` at that origin. This is a small configuration change for the Engineer.
  - 2026-10-21 — **`/test` revision 2: conditional ship for 15 Nov.** All first-run defects are fixed (QA-09 partly) and no new Medium-or-higher defects were found; 2 new Low (QA-13, QA-14). QA noted that, with today's CSP (`script-src 'self'`), static files on a different hostname are blocked unless the CSP and `STATIC_URL` are updated. That is the configuration change already recorded for the CPO's static-only Cloudflare decision.
  - 2026-10-21 — **`/test` revision 2 accepted.** The CPO accepted the conditional ship for the 15 Nov drills-only start and approved deviations 22–23. QA-13 and QA-14 are accepted until the pentest and added to its scope. Pushing to GitHub waits until after `/ship`. The static-file hostname and CSP configuration change is not built yet, so it is a pre-launch condition for `/ship`.
  - 2026-10-21 — **`/ship` complete; cycle closed.** The Launch Coordinator produced `docs/release-notes.md` (Parts A–F). This closes the first pipeline cycle (stages 1–8) on the release *package* for the 15 Nov drills-only pilot. Shipped means the release is prepared, not deployed: nothing is provisioned or deployed. Go-live is governed by the Part C checklist, and the later real-data and bank-access gates by Part D. Open items carried into the next cycle are the Part F decisions, the static-file and CSP change, an audited user-provisioning command, content-hashed static files, the CI `docker build` job, and QA-09, QA-13 and QA-14 in the pentest scope. As instructed, the commits were pushed after `/ship`.
  - 2026-10-21 — **README rewritten and PR #1 opened.** The Launch Coordinator rewrote `README.md` for vendor users and operators (CPO-authorised). The single pointer to `docs/release-notes.md` must be updated or removed at `/graduate`. PR #1 (`pipeline-setup` → `main`) triggered the first CI run. The **test job passed** (4m45s). The **secrets job failed** on permissions, not on a finding: gitleaks on pull requests needs `pull-requests: read`, and the workflow only grants `contents: read`. Fixing that is a one-line workflow change for the Engineer.

## Rules for the orchestrator

- Each stage is delegated to the matching subagent via the Task tool — never do a subagent's job yourself in the main context. `/graduate` and updates to this file's "Current status" section are the only exceptions: both are repo/state bookkeeping, not judgment calls a role needs to make.
- After a subagent produces its artifact, stop and summarize it for the CPO. Do not run the next slash command yourself, even if it seems obvious what comes next.
- Before `/kickoff` runs, confirm `docs/ceo-review.md` exists and contains a recorded verdict that is not "Do not pursue." If missing or unresolved, refuse and point back to `/ceo-review`.
- Before `/kickoff` runs, also confirm the root `README.md` is not the pipeline's own. If it is missing, or contains the marker `product-dev-pipeline:self`, have the `product-manager` replace it from `.claude/templates/README.product.md` — a product repo must never carry the pipeline's README. Everything in `docs/` is written for the team that built the product; `README.md` is the only artifact written for the person who uses it.
- Before `/ship` runs, confirm `docs/test-report.md` exists and reflects a ship-worthy state. If missing or unresolved, refuse and point back to `/test`.
- Before `/graduate` runs, confirm `docs/release-notes.md` exists (i.e. `/ship` has completed). If missing, refuse and point back to `/ship`. Always walk the CPO through the plan and get explicit confirmation before moving or replacing any files — this restructures the repo.
- `/checkpoint` can run at any stage from `/ceo-review` onward, whether or not the current stage failed. On a **Reshape** verdict, pass the checkpoint's reasoning plus every downstream artifact that exists to the agent at the stage being redone, so the reshaped work carries forward what was learned rather than starting cold. On an **Abandon** verdict (from `/checkpoint`, or from `/ceo-review`'s own "Do not pursue"), set "Stage" to `Abandoned (stage N, <date>)` instead of resetting to "not started" — the history stays visible.
- Update the "Current status" section above after every stage transition — this is what lets the pipeline resume correctly across sessions.
- If the CPO requests changes at a gate, re-invoke that same stage's subagent with the feedback rather than advancing.

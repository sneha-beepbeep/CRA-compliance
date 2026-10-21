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

- **Stage:** 2 complete: `/kickoff` approved by the CPO on 2026-10-21. Next: `/prd`, which is gated on vendor validation.
- **Last artifact:** `docs/opportunity-brief.md` (revision 3, approved), plus `README.md` created from the product template.
- **CPO approval pending on:** nothing. Before `/prd` runs, the CPO must complete the CEO's hard gate: 3–5 conversations with credit-scoring vendors, including one priced pilot candidate. If that fails, run `/checkpoint` instead. The other validation steps are in `docs/opportunity-brief.md`. Open questions for `/prd`: whether bank-side admins can see the dashboard and which incidents; whether deadlines get narrower visibility; how to define status for AI-specific risks.
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

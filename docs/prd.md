# PRD: CRA and AI Act Security Tracker (working title)

**Stage:** `/prd` (stage 3), draft 1, 2026-10-21. Status: awaiting CPO approval.

**Inputs:**
- `docs/opportunity-brief.md` (revision 3, approved);
- `docs/ceo-review.md`, the fresh-review section, whose caveats are binding;
- the decision log in `CLAUDE.md`.

**Not inputs:** the "Provably Secure" pitch in `docs/cpo-draft-prd.md` is superseded, except where noted.

---

## 1. Problem

Since **11 Sep 2026**, manufacturers of products with digital elements have had to meet the reporting clock in CRA Art. 14 for every actively exploited vulnerability and severe incident:

- an early warning within **24h** of awareness;
- a notification within **72h**;
- a final report **14 days after a fix** for vulnerabilities, or **one month after the notification** for severe incidents.

From **11 Dec 2027** they must also meet the essential requirements of CRA Art. 13 and Annex I. Vendors of AI credit-scoring systems face a third layer:

- Their systems are high-risk under **AI Act Annex III 5(b)**.
- **AI Act Art. 15** requires resilience against AI-specific attacks: data poisoning, model poisoning, adversarial examples and confidentiality attacks (Art. 15(5)).
- **CRA Art. 12** links the two regimes. Meeting the CRA essential requirements can be deemed to meet the Art. 15 cybersecurity requirement.
- CRA Recital 51 is context only.

**The gap.** These vendors don't have one place that shows where they stand on these requirements, the AI-specific risks they track, and which Art. 14 deadlines are open. The bank-side evidence is a failed in-house build and a failed white-label tool at mBank, DKB and Sächsische Aufbaubank. It points to the same gap from the customer side. Generic CRA tools are not AI-specific. AI-governance tools such as Modulos cover CRA readiness controls, but their public documentation shows no per-incident clocks (not verified by demo).

## 2. Goals and non-goals

**Goals (MVP)**
1. One dashboard where a vendor sees its own status against CRA Annex I and AI Act Art. 15. Status is described only as the evidence the vendor has entered.
2. An AI-specific risk register whose status reflects the vendor's own treatment decisions, never a robustness verdict.
3. Correct, minute-accurate Art. 14 deadlines for every reportable event, including the 24h early warning.
4. Prove in one paid pilot (vendor plus one of its banking clients) that this view is worth paying for. See section 7.

**Non-goals (MVP)**
- Certifying, attesting or declaring compliance. The product **supports** compliance; it never **ensures** it.
- Drafting notifications, or filing with ENISA's Single Reporting Platform.
- Alerts of any kind (email, chat, pager). Deferred to v2, depending on vendor demand.
- Public disclosure. The `security_changelog` view and its public-disclosure fields have no role.
- Vulnerability scanning, adversarial testing or red-teaming. We record evidence of these; we don't perform them.
- Serving deployers (banks) as a primary user. Bank access is a scoped secondary view; see OQ1.
- Annex III categories other than 5(b). These are designed for but not shipped; see the extensibility requirement R-X1.

## 3. Target users and roles

**Primary user:** security, compliance and product leads at software vendors whose system is intended for creditworthiness assessment or credit scoring of **natural persons**. This is AI Act Annex III 5(b). Fraud detection is excluded, and so is credit scoring of businesses or SMEs. The vendors must place software on the EU market.

**In-scope check on CPO assumption 2 ("ships to banks or another highly regulated client").** The client's sector doesn't decide scope. The **intended purpose** of the vendor's system does.

| Vendor's system is used for | AI Act position | In MVP scope? |
|---|---|---|
| Consumer credit scoring by a bank, BNPL provider, consumer lender, telco or utility | Annex III 5(b), whoever the deployer is | **Yes** |
| Life or health insurance risk assessment and pricing | Annex III 5(c): high-risk, but a different category | **No.** First extension candidate |
| Credit scoring of companies or SMEs | Not 5(b), which covers natural persons only | **No** |
| Fraud detection, AML or KYC screening | Explicitly excluded from 5(b) | **No** |
| Public-benefit eligibility | Annex III 5(a) | **No** |

So assumption 2 is acceptable **only where the "other highly regulated client" uses the system to score individuals' creditworthiness.** A vendor whose non-bank clients are insurers or fraud teams is out of the beachhead for those deployments.

Credit scoring involves profiling natural persons. My understanding is that this means the AI Act Art. 6(3) "no significant risk" derogation can't be used to escape high-risk status. **This is my reading and is not verified with counsel.**

**Roles**

| Role | Who | Sees | Can edit |
|---|---|---|---|
| Vendor admin | Every user with admin access to the vendor's AI credit-scoring product (CPO decision) | The whole dashboard. Incident **details** depend on OQ2 | Requirements and AI-risk status, evidence |
| Vendor incident responder | A subset of vendor admins (proposed, see OQ2) | The above, plus full incident details | Incidents, awareness time, filing timestamps |
| Bank admin (proposed, see OQ1) | Admin of the deployed product at a bank client | A scoped view of their own deployment only | Nothing |

## 4. MVP scope

**In scope:**
1. Product registry: the product, its versions, its Annex III category (5(b) for now) and its deployments.
2. Requirements status: CRA Annex I Part I (product properties) and Part II (vulnerability handling), and AI Act Art. 15, each tracked to evidence.
3. AI-specific risk register with a lifecycle status (OQ3).
4. Art. 14 event tracker and deadline view for vulnerabilities and severe incidents.
5. Role-based access, tenant isolation, audit trail.
6. A bank-scoped read-only view, **if OQ1 is confirmed**.

**Out of scope:** everything in the non-goals list, plus integrations with SBOM or vulnerability feeds. Entry is manual or by CSV import in the MVP; integrations are a v2 candidate once the pilot shows which feeds the vendor actually uses.

## 5. User stories and acceptance criteria

**Requirements status (R-1)**
- *As a vendor compliance lead, I want to see each CRA Annex I and AI Act Art. 15 requirement with its evidence status, so that I know what's missing before 11 Dec 2027.*
  - Each requirement shows one of: `not started`, `in progress`, `evidence attached`, `evidence stale` (past its review date), `not applicable (with rationale)`.
  - Every requirement shows its citation, for example "CRA Annex I, Part II(2)". The product's own text never uses "compliant" or "non-compliant".
  - A summary reads like "evidence attached for 9 of 13 requirements". It is a count, not a score or a traffic-light verdict.
  - `not applicable` requires a written rationale and is recorded in the audit trail.

**AI-specific risk register (R-2)**
- *As a vendor security lead, I want to register AI-specific risks against my product and record how each is treated, so that I can show Art. 15(5) coverage.*
  - The register is seeded from a risk taxonomy. **Dependency D-1:** the rights to the book-derived content in `regtech_cyber.db` are unconfirmed. If they are not cleared, seed from public taxonomies (MITRE ATLAS, OWASP ML/LLM Top 10, NIST AI 100-2), subject to a licence check.
  - Status follows the definition proposed in OQ3. Each risk can link to the requirements it supports, such as Art. 15(5) or Annex I Part I.
  - Each risk carries an owner, a last-reviewed date and attached evidence, such as a red-team report or a data-provenance control.

**Art. 14 deadlines (R-3)**
- *As a vendor incident responder, I want to log an actively exploited vulnerability or a severe incident with the time we became aware, and see every Art. 14 deadline, so that we never miss the 24h early warning.*
  - Event type is required: `actively exploited vulnerability` or `severe incident`.
  - Awareness time is required, entered with a timezone and stored in UTC.
  - Deadlines are computed as follows:
    - early warning = awareness + 24h;
    - notification = awareness + 72h;
    - final report = fix available + 14 days for a vulnerability, or notification submitted + one month for a severe incident.
  - Each deadline shows the absolute time in UTC and in the user's local time, a countdown, and a state: `open`, `met`, `late`, `overdue` or `not started`.
  - The user records the time each item was filed with ENISA. The tool doesn't file.
  - A "users informed" timestamp records CRA Art. 14(8). It is a field only, with no workflow. **Art. 14(8) is cited from secondary sources; check it against the Official Journal.**
  - Any edit to the awareness time needs a reason, keeps the previous value in the audit trail, and recomputes all deadlines visibly.
  - Each event links to the affected product version and deployments, which is needed for OQ1.

**Bank-scoped view (R-4, conditional on OQ1)**
- *As a bank admin of a deployed credit-scoring product, I want to see the vendor's requirements and AI-risk status for the version I run, and any incident affecting my deployment once I've been informed, so that I can rely on it in third-party risk review.*
  - A bank admin can never see another tenant's deployments or incidents. Isolation is tested; see NFR-2.
  - Incidents become visible to a bank only after the vendor sets "users informed" for that deployment.

**Extensibility (R-X1)**
- Requirement sets, Annex III categories and risk taxonomies are data, not code. Adding Annex III 5(c) must not need a schema change. Nothing is hard-coded to 5(b) or to banks.

## 6. Non-functional requirements

The dashboard will hold **unreported, actively exploited vulnerabilities**. It is a high-value target in its own right.

| ID | Requirement |
|---|---|
| NFR-1 Access | SSO (SAML or OIDC) plus enforced MFA. Role-based access control as in section 3. Least privilege by default. |
| NFR-2 Tenant isolation | Strict separation between vendors, and between bank tenants of a vendor. Covered by automated tests and by the pre-pilot penetration test. |
| NFR-3 Audit trail | Append-only log of every create, edit and view of incident details, every status change and every awareness-time edit: who, what, when (UTC) and the previous value. Exportable for the vendor's technical documentation. |
| NFR-4 Time handling | The server clock is authoritative and synchronised with NTP. Storage is UTC only. Deadlines are computed to the minute. Daylight-saving changes are handled; tests include the EU DST changeovers and the 72h-across-a-weekend case. One-month final reports are computed as calendar months. **Whether "one month" means a calendar month or 30 days needs confirming.** |
| NFR-5 Data protection | Encrypted in transit (TLS 1.2+) and at rest. Hosted in the EU. Minimal personal data (user accounts only). |
| NFR-6 Availability | Proposed target: 99.5% monthly. With no alerts, the dashboard has to be up when someone checks it during an incident. |
| NFR-7 Our own posture | The pilot vendor and its bank will ask for our security assurance, such as ISO 27001 status, a pentest report and a DORA-style subcontracting clause. Dependency D-3. |
| NFR-8 Wording | Every screen and export carries: "Status reflects information entered by [vendor]. It is not a determination of compliance." |

**Existing components.** `schema.sql` is **revised, not adopted as-is**:

| Component | Decision proposed |
|---|---|
| `finding` table | **Keep, with changes.** Changes are listed below this table. |
| `cra_deadline_check` view | **Keep, with changes.** Changes are listed below this table. |
| `security_changelog` view | **Drop.** No role in this product. |
| `regtech_cyber.db` | Reference asset for R-2 only, **subject to D-1**. It will not be hardened. |

Changes to the `finding` table:
- Add an event type (`vulnerability` or `severe_incident`), a product version, affected deployments, a notification-submitted time and a "users informed" time.
- Drop `public_summary`, `disclosed_at`, the `disclosed` status and the bug-bounty discovery channels.

Changes to the `cra_deadline_check` view:
- Add the one-month final report for severe incidents, which is **currently missing**.
- Restrict the 14-day final report to vulnerabilities.
- Include events where `actively_exploited = 0` but the event type is a severe incident.

## 7. Success metrics: what the €36k pilot must show

**The pilot:** 3 months, €12k per month, with one vendor and one of its banking clients. This is the vendor's own stated price. The Gera benchmark of €50k is a deployer-side market figure, **not** vendor evidence, and is not used here.

| # | Metric | Target |
|---|---|---|
| P1 Activation | Share of CRA Annex I and Art. 15 requirements given a status within 4 weeks | 100% |
| P2 AI-risk coverage | AI-specific risks registered, each with an owner and a status other than `not assessed` | 10 or more by week 6 |
| P3 Clock correctness | Deadline errors found in QA and in the pilot | 0 |
| P4 Drill | At least one simulated exploited-vulnerability drill and one simulated severe-incident drill, run end to end | Every deadline shown correctly. The vendor confirms the 24h early warning would have been met. |
| P5 Use | Weekly active vendor admins | 2 or more, in at least 10 of 12 weeks |
| P6 Bank pull (the core thesis) | The pilot bank states in writing whether it would accept the dashboard, or an export of it, as evidence in procurement or third-party risk review | A yes, or specific conditions |
| P7 Commercial | The vendor commits to an annual contract, or states a price for one | Signed contract or a priced intent by week 12 |
| P8 Alerts signal (v2 gate) | Does the vendor ask for alerts, unprompted or when asked? | Recorded. This decides whether alerts go into v2. |

Real Art. 14 events will probably be rare during a 3-month pilot. That is why P4 uses drills rather than waiting for a live incident.

## 8. Dependencies

- **D-1 IP:** rights to the book-derived taxonomy. If they aren't cleared, use public taxonomies, subject to a licence check.
- **D-2 Pilot terms:**
  - who pays (CPO assumption 1, that the vendor pays, is unconfirmed);
  - the bank's role in the pilot (open);
  - the confidentiality agreement covering incident data.
- **D-3 Our own security assurance**, before any incident data is loaded.
- **D-4 Legal:**
  - the CPO lawyer's hosted-API advice in writing;
  - a review of the liability terms and the NFR-8 wording;
  - confirmation of the Art. 6(3) reading and of how "one month" is computed.
- **D-5 Regulatory text:** Art. 14 and Art. 14(8) checked against the Official Journal. Whether the AI Act Omnibus (Annex III to 2 Dec 2027) has been published remains unverified.

## 9. Risks and kill signals

| Risk | Mitigation |
|---|---|
| **Vendor evidence is thin.** There are 3 conversations, reported by the CPO, with unnamed vendors. There is one price signal. No vendor's delivery model has been recorded. | Record each vendor's delivery model before `/design` (OQ4). |
| A **status display is read as a compliance verdict**, which creates liability. | Evidence-count wording, NFR-8, and no traffic-light verdicts. |
| With **no alerts, a 24h deadline is missed** while nobody is looking. | Accepted for the MVP. Tested through the P4 drill and the P8 signal. |
| **Leakage of unreported exploited vulnerabilities**, through a wide admin audience or across bank tenants. | OQ1 and OQ2 proposals, NFR-1 to NFR-3. |
| **Modulos or another tool already does this.** | The competitor check from brief step 4 (a Modulos demo) is still outstanding. Do it before `/design`. |
| **Niche size:** about 10 to 60 vendors and €0.2m to €2.4m ARR (my estimate, unverified). | R-X1 extensibility. 5(c) is the first extension. |

**90-day kill signals (to 2027-01-19).** Any one triggers `/checkpoint`:

- Fewer than 3 vendors will pilot or discuss price.
- Most target vendors ship no software to their clients.
- An existing tool already combines AI-specific risk tracking with CRA Art. 14 tracking for this segment.
- Vendors say their clients don't require this in procurement.

**Timing conflict.** A 3-month pilot can't start and finish before 2027-01-19, because nothing is built yet. On 2027-01-19 the kill signals can only be checked against **pre-pilot** evidence: a signed pilot, confirmed delivery models and the competitor check. The pilot metrics in section 7 then need their own review date (OQ5).

## 10. Open questions

**From the brief: proposed answers for the CPO to confirm**

1. **OQ1. Can bank admins see the dashboard, and which incidents?**
   - **Proposal:** yes, but only a read-only view scoped to their own deployment (R-4). It shows:
     - requirements and AI-risk status for the product version they run;
     - incidents affecting *their* deployment, only after the vendor marks them "users informed" (Art. 14(8)).
   - Bank admins never see exploited-but-unreported vulnerabilities, and never see another bank's data.
   - This reads the CPO's "every admin of the product" as vendor admins seeing everything and bank admins seeing a scoped view. **Confirm, or say if you meant something else.**
2. **OQ2. Should deadlines be narrower than requirements status?**
   - **Proposal:** all vendor admins see the deadline panel as **states and counts only**, for example "1 event: early warning due in 6h 12m".
   - Incident **details** (affected component, description, vector) are visible only to vendor incident responders.
   - This keeps the CPO's "every admin sees the dashboard" decision while limiting who can read exploit-level detail.
3. **OQ3. What does "status" mean for AI-specific risks?**
   - **Proposal:** a lifecycle state of the vendor's own risk-treatment record, never a robustness rating:
     - `not assessed`;
     - `assessed – treatment planned`;
     - `treatment in place – evidence attached`;
     - `evidence stale`;
     - `accepted with rationale`;
     - `not applicable with rationale`.
   - Each status also shows a "last tested" date. There are no scores and no pass/fail.

**New, to settle before `/design`**

4. **OQ4. Vendor facts.** For each of the 3 vendors, record:
   - its delivery model (what software ships to clients);
   - whether its non-bank clients score individuals (5(b)), or do insurance (5(c)), SME credit or fraud work;
   - who pays for the pilot.
   The "ships software" assumption and both CPO assumptions are still unverified.
5. **OQ5. Pilot role and timeline.**
   - What does the banking client actually do in the pilot? Is it a passive viewer, the evidence reviewer for P6, or a co-payer?
   - When does the pilot start, given the 2027-01-19 kill date?

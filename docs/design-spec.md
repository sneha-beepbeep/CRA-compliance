# Design Spec: CRA and AI Act Security Tracker (working title)

**Stage:** `/design` (stage 4), draft 2, 2026-10-21. Status: approved by the CPO on 2026-10-21.

**Inputs:**
- `docs/prd.md` (draft 1, approved 2026-10-21);
- the CPO decisions recorded in `CLAUDE.md` under "/prd approved (draft 1)": OQ1, OQ2 and OQ3 accepted; the vendor pays €36k; the bank co-pays €15k after success and legal review; the pilot starts 2026-11-15;
- the binding caveats in `docs/opportunity-brief.md` and the fresh-review section of `docs/ceo-review.md`;
- `README.md`;
- the CPO's answers to design questions OQ-D1 to OQ-D10 on draft 1 (2026-10-21), recorded in section 0.

**What this document is:** user flows, screens, states, copy rules and visual rules, written so an engineer can build the UI without guessing. It contains no technical plan, data model or code. Where the PRD is silent or ambiguous, I say so and either give a proposed default (marked **Proposed**) or raise an open question (section 21). I have not silently invented answers.

**Naming in this document.** "Bank" means the pilot's deployer. The UI itself never says "bank" (see R-X1). It says **customer** and shows the customer's own name, because a 5(b) deployer can also be a consumer lender, BNPL provider, telco or utility.

---

## 0. Changes in draft 2

### 0.1 CPO decisions on draft 1 (2026-10-21)

| Question | CPO answer (verbatim) | Recorded as | Where applied |
|---|---|---|---|
| OQ-D1 Customer sees Art. 14 clocks? | "No" | **Decided.** The customer never sees Art. 14 deadline states, awareness times or filing times. | 9.2, 17 |
| OQ-D2 Customer-visible vendor content | "Confirm" | **Decided** as proposed: N/A rationale shown; evidence titles, types and dates shown; evidence files and URLs not shown; AI-risk owner names hidden. | 9.2 |
| OQ-D3 Status per product version | "Confirm" | **Decided:** status is recorded per product version, with carry-forward. | 3, 11.5, 18 |
| OQ-D4 Who can start a clock | "Yes but confirm role before allowing view of incident details" | **Decided:** any vendor admin can start a clock with type, awareness time, product and an assigned responder only. Incident details stay responder-only, and the role is checked at the moment of every request for details. | 2.3, 8.3a, 8.2, 13 |
| OQ-D5 Identity and user management | "Vendot" (read as "Vendor") | **Decided:** the vendor grants the responder role and invites customer admins. **Not settled:** whose identity provider signs in the customer's admins. My reading is in 5.1; flagged for `/plan`. | 2.2, 5, 5.1, 21 |
| OQ-D6 Session timeout and step-up | "Confirm" | **Decided:** 8-hour idle timeout for vendor roles, 30 minutes for customer roles, step-up re-authentication for "Mark informed". | 11.6, 16 |
| OQ-D7 Event close states and linked events | "Check with engineer" | **Proposed, pending engineering review at `/plan`.** Design kept. | 8.6, 8.7 |
| OQ-D8 Drill mode, events excluded from CSV | "Check with engineer" | **Proposed, pending engineering review at `/plan`.** Design kept. | 8.8, 12.1 |
| OQ-D9 Vendor sees customer activity | "Yes with anonymization option on customer side" | **Decided:** the vendor sees customer views and exports in its audit trail, and the customer can anonymize its users' identities in what the vendor sees. Designed in 9.6. | 2.3, 9.6, 13 |
| OQ-D10 Calendar-month rule | "Confirm" | **Decided as the interim rule:** clamp to the last day of the month, calendar day in UTC. Still shown as "pending legal confirmation" because D-4 is open. | 8.1, 11.1 |

### 0.2 Other changes in draft 2

- New flow **F-4e "Start a clock"** for vendor admins who aren't responders (8.3a), with an "awaiting responder" flag on the clock strip and event list.
- Setup now requires at least one incident responder before it is complete (5).
- New customer screen **S-B7 Activity sharing**, plus an anonymization flow (9.6).
- Release preview (9.1) and audit trail (13) changed to respect customer anonymization.
- Permission matrix (2.3), screen inventory (14), deviations (18), traceability (19) and open questions (21) updated.

---

## 1. Design principles

1. **Describe the record, never judge it.** Every status describes what the vendor has entered: evidence attached, a date passed, a filing time recorded. Nothing on screen or in an export says or implies that a product is or isn't compliant, secure or ready.
2. **Colour means time pressure, never quality.** Only Art. 14 clocks get urgency colour. Requirement and AI-risk statuses use one neutral palette and are told apart by text and shape. Green is not used anywhere for status.
3. **An empty list is not an all-clear.** Empty states say what has not been recorded, never that nothing exists ("No events recorded here", not "No incidents").
4. **The 24h clock is the loudest thing in the product.** With no alerts, every vendor screen carries the open-clock strip. Nothing can dismiss or cover it.
5. **Show the source of every number.** Counts are shown with their denominator and breakdown, and every view says when it was last updated and who entered the data.
6. **Least privilege is visible.** When content is withheld from a role, the UI says so ("Details restricted to incident responders") rather than hiding that anything exists. The exception is the customer view, where nothing about unreleased incidents may be inferred (section 9.3).
7. **Regulation is data.** Requirement sets, Annex III categories, citations and risk taxonomies come from data. The UI has no 5(b), credit or bank strings in its chrome.

---

## 2. Personas and roles

### 2.1 Personas

| Persona | Role(s) | Goal in the product | What worries them |
|---|---|---|---|
| **Maja, Head of Compliance** at the pilot vendor | Vendor admin, access manager | Get every Annex I and Art. 15 requirement to a status with evidence before 11 Dec 2027. Show the bank something it can rely on. | Saying more to the bank than the evidence supports. |
| **Tomasz, Security lead / on-call** at the pilot vendor | Vendor admin + incident responder | Log an exploited vulnerability fast, see the 24h deadline, record filings, and tell affected customers. | Missing the 24h early warning at 02:00 on a Sunday. |
| **Lena, Product manager** at the pilot vendor | Vendor admin | Keep the AI-risk register current for her model; attach red-team reports. Start a clock if she hears of an exploit first. | Busywork; stale evidence she forgot about. |
| **Jan, IT third-party risk admin** at the pilot bank | Customer read-only admin | Review the vendor's status for the version the bank runs, and export it for the legal team. | Relying on something that later turns out to mean nothing; the vendor tracking his team's activity. |
| **Dr. Weber, bank legal / supplier review** | No account. Reads the export | Decide whether the bank can accept the export as supplier evidence (PRD P6). | What exactly is claimed, on what basis, and by whom. |

Dr. Weber is a **design audience, not a user**. The export (S-B6) is designed for her.

### 2.2 Roles

| Role | Defined by | Notes |
|---|---|---|
| Vendor admin | PRD section 3 | Every user with admin access to the vendor's product (CPO decision). Can start a clock (OQ-D4). |
| Vendor incident responder | PRD section 3, OQ2 | Added on top of vendor admin. A responder is always also a vendor admin. |
| Customer read-only admin | PRD section 3, OQ1 | One customer tenant, one or more deployments of that customer. Read-only on vendor data; can set their own organisation's activity-sharing preference (OQ-D9, 9.6). |
| *Access manager* (vendor side) | OQ-D5: "the vendor" grants roles and invites customer admins | **Proposed mechanism:** a flag on one or more vendor admins. Only access managers grant or remove the responder role and invite or remove customer admins. Whether every vendor admin should hold this is a remaining detail (21). |
| *Our support staff* (**Proposed**, OQ-D12) | Not in the PRD | Proposed: no access to any tenant's content. Support by screen-share only. |

### 2.3 Permission matrix

Legend: **E** edit, **V** view, **C** counts and states only, **—** no access and no indication it exists.

| Capability | Vendor admin | Vendor incident responder | Customer read-only admin |
|---|---|---|---|
| Overview | V | V | V (own deployments, customer variant) |
| Product registry: products, versions, Annex III category | E | E | V (own version and deployment only) |
| Grant/remove responder role; invite/remove customer admins | E (access managers only) | E (access managers only) | — |
| Requirements status, rationale, evidence | E | E | V (fields per 9.2) |
| AI-risk register | E | E | V (fields per 9.2) |
| Art. 14 clock strip and deadline panel | C (type, reference, product, deadline states, countdowns, assigned responder, "awaiting responder" flag) | V | — |
| **Start a clock** (type, awareness time, product, assigned responder) | E (OQ-D4) | E | — |
| Reassign the responder on an event | E (**Proposed**, 8.3a) | E | — |
| Log a full event; view or edit incident details (title, description, component, vector, affected versions and deployments, filing times; awareness time after the start confirmation) | — (row shows "Details restricted to incident responders") | E (role checked on every request) | — |
| Edit awareness time, reclassify, close | — | E (reason required) | — |
| Mark customer users informed (releases to customer view) | — | E (step-up re-authentication, OQ-D6) | — |
| Incidents released to own deployment | C (as above) | V | V (fields per 9.2) |
| CSV import (requirements, risks) | E | E | — |
| Audit trail | V (incident-detail values masked; customer identities per customer setting) | V (unmasked incident values; customer identities per customer setting) | — |
| Customer view and export activity | V (in audit trail, per customer anonymization setting) | V (same) | — (own organisation's export history only, in S-B6) |
| Activity-sharing setting (anonymization) | V (current setting shown, can't change) | V (same) | E |
| Exports: vendor status export, audit export | E | E | — |
| Customer export (PDF/CSV) of own view | V (can generate the same export to preview it) | V | E |
| Drill events (8.8, pending engineering review) | C (labelled DRILL) | E | — |

Every view of incident details, by anyone, is written to the audit trail (NFR-3). **Role check (OQ-D4):** the responder role is checked at the moment of each request for incident details, not only at sign-in. Removing the role takes effect on the user's next request; an open event-detail page reloads to the restricted view.

---

## 3. Information architecture

```
Vendor workspace
├─ Overview                      S-2
├─ Requirements                  S-3 → S-4 requirement detail
├─ AI-risk register              S-5 → S-6 risk detail
├─ Art. 14 events                S-7 → S-8 log event (responders), S-8a start a clock (any vendor admin),
│                                       S-9 event detail (S-10 mark users informed, S-11 edit awareness
│                                       time, S-12 reclassify, S-13 close)
├─ Products and customers        S-14 (products, versions, deployments, users and roles, customer access)
├─ Import                        S-15
├─ Audit trail                   S-16
└─ Exports                       S-17

Customer workspace (read-only on vendor data)
├─ Overview                      S-B1
├─ Requirements                  S-B2
├─ AI-risk register              S-B3
├─ Incidents shared with you     S-B4
├─ About this information        S-B5
├─ Export                        S-B6
└─ Activity sharing              S-B7 (settings)

Shared: S-0 sign-in and access states, S-1 application shell
```

The product/version selector sits in the shell. Requirements and AI-risk status are recorded **per product version** (decided, OQ-D3), because the customer view must show "the version I run" (R-4).

---

## 4. Global shell (S-1)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ [Tracker]  Acme Scoring GmbH ▾   Product: ScoreEngine ▾  Version: 4.2 ▾   Maja K ▾│
├──────────────────────────────────────────────────────────────────────────────────┤
│ ▲ ART. 14 CLOCKS  2 open                                                          │  ← clock strip
│ ■ E-0008 Actively exploited vulnerability · EARLY WARNING due in 22h 40m          │    (always present
│   AWAITING RESPONDER – started by L. Braun 18m ago · Assigned: T. Nowak           │    for vendor roles)
│ ■ E-0007 Actively exploited vulnerability · EARLY WARNING due in 5h 12m           │
│   Thu 22 Oct 2026, 14:05 CEST · 12:05 UTC · Responder: T. Nowak   [Open event →]  │
├───────────────┬──────────────────────────────────────────────────────────────────┤
│ Overview      │                                                                  │
│ Requirements  │   page content                                                   │
│ AI-risk reg.  │                                                                  │
│ Art. 14 events│                                                                  │
│ Products/cust.│                                                                  │
│ Import        │                                                                  │
│ Audit trail   │                                                                  │
│ Exports       │                                                                  │
│               │                                                                  │
│ Help          │                                                                  │
├───────────────┴──────────────────────────────────────────────────────────────────┤
│ Status reflects information entered by Acme Scoring GmbH. It is not a             │
│ determination of compliance.            Last synced 12:01 UTC · Times shown: CEST │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Clock strip rules (vendor roles only):**
- Present on **every** vendor screen, including setup, import and audit trail. It is part of the layout, not an overlay, so it never covers focused content (WCAG 2.2 SC 2.4.11).
- It cannot be dismissed or collapsed while any early warning or notification is open or overdue.
- It lists open clocks soonest first, at most 3 rows, then "+ 2 more →".
- Each row: reference, event type, the **next** unfiled deadline, countdown, absolute time in local and UTC, assigned responder. Vendor admins without the responder role see the same row, with "Open event" replaced by "Details restricted to incident responders".
- **Awaiting responder** (8.3a): an event started by a non-responder shows "AWAITING RESPONDER – started by [name] [time] ago" until the assigned responder first opens it. This flag sorts the row above other rows of the same tier. For responders, the row's action reads "Open and take over →".
- Emphasis tiers (section 10.3): **overdue** > **early warning open** > **notification open** > **final report open**.
- With no open clocks the strip shrinks to one neutral line: "No open Art. 14 clocks recorded." It never shows a tick or green.
- **Drill** clocks (pending engineering review) are shown with a hatched background and the word DRILL before the reference. They sort below real clocks of the same tier.

**Browser tab title (Proposed, OQ-D11):** when a clock is open, the tab title becomes `(EW 5h 12m) Tracker – Acme`, or `(OVERDUE) Tracker – Acme`. This is passive in-app display, not an alert.

**Footer:** the NFR-8 notice, last-synced time, and the time zone being displayed. It is on every screen.

**Session expiry:** see section 11.6.

---

## 5. Onboarding and setup flow (F-1)

**Precondition:** we provision the vendor tenant and its SSO connection (SAML or OIDC, MFA enforced at the IdP or by us; NFR-1). This is an operator step, not a UI flow. The first vendor admin is created as an access manager.

| Step | Screen | What happens | Notes |
|---|---|---|---|
| 1 | S-0 | First vendor admin signs in through SSO. MFA is enforced. | No local passwords for vendor users. |
| 2 | Setup checklist (part of S-2 until complete) | Checklist: product, version, category, **incident responders**, deployments, customer access, time zone. Shows "Setup: 2 of 7 steps done". | This counts setup steps, not compliance. It lives in its own panel with its own heading, "Setup". |
| 3 | S-14 Add product | Name; **intended purpose** (free text, required); **Annex III category** (select from data). | Categories not yet supported are listed but disabled: "Annex III 5(c) – not yet supported". Shown as "Category selected by vendor". |
| 3a | S-14 | **Proposed:** delivery model (installed software / SDK or library / hosted API with vendor software on the customer side / browser-only or hosted API only). | Records the CRA scope assumption (PRD OQ4). If "browser-only or hosted API only" is chosen: "The CRA may not apply to a product delivered only as a hosted service. Check scope with legal counsel." Not a block. OQ-D13. |
| 4 | S-14 Add version | Version label, release date. | Requirement set(s) for the category attach automatically from data (for 5(b): CRA Annex I Part I, Part II, AI Act Art. 15). The screen lists the sets and their source citations. |
| 5 | S-14 Seed AI-risk register | Choose a seed taxonomy from those available as data. Each shows its source and licence. | Subject to D-1. Seeding creates risks in `not assessed`. |
| 6 | S-14 Users and roles | Access manager grants the **incident responder** role to at least one vendor admin. | **Required** (new in draft 2): admin-started clocks must be assigned to a responder. Until one exists, the strip shows "No incident responder assigned. Clocks can't be routed." in the overdue tier. |
| 7 | S-14 Add deployment | Customer name (creates or picks a customer tenant), deployment label, version deployed. | One deployment runs one version at a time. Changing it is audited. |
| 8 | S-14 Customer access | Access manager invites a customer read-only admin by email (5.1). | The invite screen previews the customer view first: "This is what [Customer] will see." |
| 9 | Profile | Each user confirms their display time zone (defaults to browser). | 11.1. |
| 10 | S-2 | Checklist disappears when all steps are done. | |

**Pilot note.** One vendor, one product, one bank deployment. The flow supports more of each.

### 5.1 How customer admins sign in (OQ-D5, partly open)

The CPO decided that **the vendor** invites customer admins. Whose identity provider authenticates them was not answered. **My reading, for `/plan` to confirm:**

- **Pilot:** vendor-managed invitations. The access manager invites by email. The invitee sets up a sign-in with our hosted identity service, with **MFA enforced** (authenticator app or passkey; no SMS). No customer IdP integration in the pilot.
- **Later option:** federation with the customer's own IdP (SAML/OIDC), so the bank controls joiners and leavers. The UI keeps the invite flow either way.
- **Why it matters for the bank's legal review:** with vendor-managed invitations, the vendor knows who the customer admins are. That limits what anonymization can hide (9.6).
- Customer admins invited by the vendor can be removed by the vendor's access manager. A customer admin can't invite colleagues in the MVP; they ask the vendor. **Proposed;** flagged in 21.

---

## 6. Requirements status (F-2, R-1)

### 6.1 Status vocabulary

| Status | Set by | Meaning shown in the legend | Rule |
|---|---|---|---|
| `not started` | Default | No status entered yet. | |
| `in progress` | Vendor admin | Work recorded as under way. No evidence attached yet, or evidence not yet marked complete. | |
| `evidence attached` | Vendor admin | At least one evidence item is attached and its review date has not passed. | Needs at least 1 evidence item and a **review-by date**. |
| `evidence stale` | **System only** | The review-by date has passed. | Set automatically at the review-by date (00:00 UTC on the day after). Cannot be set by hand. Cleared by adding evidence or setting a new review-by date. |
| `not applicable (with rationale)` | Vendor admin | Vendor has recorded why this requirement does not apply. | Rationale is required (minimum 20 characters) and audited. The rationale is **visible to customers** (decided, OQ-D2); the field says so. |

The PRD does not set a default review period. **Proposed:** the review-by date is required and has no default (OQ-D14).

### 6.2 Requirements list (S-3)

```
Requirements · ScoreEngine 4.2                            [Import CSV] [Export]
Annex III category: 5(b) creditworthiness of natural persons (selected by vendor)

Summary
  Evidence attached for 9 of 35 requirements.
  Breakdown: 9 evidence attached · 2 evidence stale · 3 not applicable ·
             6 in progress · 15 not started
  This is a count of records entered here. It is not a score.

Filter: [All statuses ▾] [All sets ▾] [Review due in 30 days ▢]   Search [        ]

▸ CRA Annex I, Part I – Cybersecurity requirements relating to product properties
  Source: Regulation (EU) 2024/2847, Annex I, Part I            [Official text ↗]
  ┌──────────────────────────┬──────────────────────────────┬─────────────────┬────────────┬───────────┐
  │ Citation                 │ Requirement (short title)    │ Status          │ Review by  │ Linked AI │
  │                          │                              │                 │            │ risks     │
  ├──────────────────────────┼──────────────────────────────┼─────────────────┼────────────┼───────────┤
  │ CRA Annex I, Part I(1)   │ Appropriate level of cyber-  │ ◆ evidence      │ 30 Jun 2027│ 2         │
  │                          │ security based on risks      │   attached      │            │           │
  │ CRA Annex I, Part I(2)(a)│ No known exploitable vulns   │ ◇ in progress   │ –          │ 0         │
  │ CRA Annex I, Part I(2)(f)│ Integrity of data and code   │ ◈ evidence stale│ 01 Oct 2026│ 3         │
  │                          │                              │   date passed   │            │           │
  └──────────────────────────┴──────────────────────────────┴─────────────────┴────────────┴───────────┘
▸ CRA Annex I, Part II – Vulnerability handling requirements
▸ AI Act Art. 15 – Accuracy, robustness and cybersecurity
  Context: CRA Art. 12 provides that meeting the CRA essential requirements can,
  under conditions, be deemed to meet the Art. 15 cybersecurity requirement.
  This tool does not apply that presumption for you. Statuses here are entered
  separately.   [More context: CRA Recital 51 (not binding) ↗]
```

- The summary is **text with a denominator**, never a percentage, progress bar, gauge or donut (PRD R-1).
- The requirement count comes from the data; 35 is illustrative.
- Short titles are our paraphrase. Each requirement links to the official text, and the detail screen says "Short title written by [product name]; the official text governs."
- AI Act Art. 15 status is **not derived** from CRA statuses, and no requirement status is derived from AI-risk statuses. Links are informational only.

### 6.3 Requirement detail (S-4)

Sections, top to bottom:
1. Citation, short title, link to official text, the requirement set and its source.
2. **Status** with a change control. Changing to `evidence attached` opens the evidence and review-by fields. Changing to `not applicable` opens the rationale field, labelled "Visible to your customers". Each change takes an optional note (rationale required for N/A).
3. **Evidence items:** title, type (document, link, test report, policy, other), date of evidence, optional file or URL, added by, added on. Files and URLs are never shown to customers (decided, OQ-D2); titles, types and dates are. The section header says "Titles, types and dates are visible to your customers. Files and links are not."
4. **Linked AI risks**, with each risk's own status shown, labelled "Linked for reference. Does not change this requirement's status."
5. **History:** status changes for this requirement, from the audit trail.
6. **Carried forward** marker if the record came from a previous version (11.5).

States: loading (skeleton rows, no placeholder statuses); save error ("Not saved. Your change to status was not recorded. [Retry]"); conflict ("Maja changed this at 14:02. Review her change before saving yours."); stale (section 10).

---

## 7. AI-risk register (F-3, R-2)

### 7.1 Handling-stage vocabulary (OQ3, CPO-approved)

| Handling stage | Meaning in the legend | Rule |
|---|---|---|
| `not assessed` | No assessment recorded. | Default after seeding. |
| `assessed – treatment planned` | Vendor recorded an assessment and a planned treatment. | Planned treatment text required. |
| `treatment in place – evidence attached` | Vendor recorded a treatment as in place, with evidence. | At least 1 evidence item and a review-by date. |
| `evidence stale` | Review-by date passed. | **System only**, as for requirements. |
| `accepted with rationale` | Vendor decided to accept the risk and recorded why. | Rationale required, audited, customer-visible. |
| `not applicable with rationale` | Vendor recorded why it does not apply to this product. | Rationale required, audited, customer-visible. |

Each risk also shows:
- **Last tested:** the date of the most recent evidence item of type "test" (red-team report, adversarial test, poisoning test). If none: "Not tested (no test evidence recorded)". The OQ3 decision names this field.
- **Last reviewed:** the date someone last confirmed the record (R-2 names this field). Both are shown, because "tested" and "reviewed" are different facts. OQ-D14.
- **Owner:** a vendor user. Shown to customers only as "Owner assigned" (decided, OQ-D2).

No scores, likelihoods, severities, heat maps or pass/fail.

### 7.2 Register list (S-5)

```
AI-risk register · ScoreEngine 4.2                  [Add risk] [Import CSV] [Export]

Summary: 14 risks recorded. 6 treatment in place – evidence attached ·
         1 evidence stale · 3 assessed – treatment planned · 1 accepted with rationale ·
         1 not applicable with rationale · 2 not assessed
This is a count of the vendor's treatment records. It is not a robustness rating.

┌─────────────────────────┬──────────────────────┬───────────────────────────┬─────────────┬──────────────┬──────────┐
│ Risk                    │ Source taxonomy      │ Handling stage            │ Last tested │ Last reviewed│ Owner    │
├─────────────────────────┼──────────────────────┼───────────────────────────┼─────────────┼──────────────┼──────────┤
│ Training-data poisoning │ <taxonomy, ref>      │ ◆ treatment in place –    │ 12 Sep 2026 │ 01 Oct 2026  │ L. Braun │
│ AI Act Art. 15(5)       │                      │   evidence attached       │             │              │          │
│ Adversarial examples    │ <taxonomy, ref>      │ ◇ assessed – treatment    │ Not tested  │ 15 Oct 2026  │ T. Nowak │
│ AI Act Art. 15(5)       │                      │   planned                 │             │              │          │
└─────────────────────────┴──────────────────────┴───────────────────────────┴─────────────┴──────────────┴──────────┘
```

The Art. 15(5) attack class (data poisoning, model poisoning, adversarial examples, confidentiality attacks) is a tag from the taxonomy data, not hard-coded.

### 7.3 Risk detail (S-6)

Name, description (from taxonomy, editable by vendor; the original taxonomy text stays visible with its source), Art. 15(5) attack class, handling stage, planned treatment or rationale, evidence items, last tested, last reviewed ("Mark reviewed today" button, audited), owner, linked requirements (pick from S-3), history.

**Empty state (register with no risks):** "No AI-specific risks recorded for this version. [Seed from a taxonomy] [Add a risk] [Import CSV]." Never "No risks".

---

## 8. Art. 14 events and clocks (F-4, R-3)

### 8.1 Deadline rules shown to users

| Clock | Applies to | Starts at | Due | Shown when trigger missing |
|---|---|---|---|---|
| Early warning | Both types | Awareness time | +24h (elapsed) | – |
| Notification | Both types | Awareness time | +72h (elapsed) | – |
| Final report | Actively exploited vulnerability | Fix or mitigation available time | +14 days | `not started` – "Starts when a fix or mitigation is recorded as available." |
| Final report | Severe incident | Notification filing time | +1 calendar month: same day next month, clamped to the last day of the month if that day doesn't exist; calendar day in UTC (decided interim rule, OQ-D10; **pending D-4**) | `not started` – "Starts when the notification filing time is recorded." |

Deadline states (PRD vocabulary, with the legend text the UI shows):

| State | Legend text |
|---|---|
| `not started` | The clock's start time has not been recorded yet. |
| `open` | Deadline not reached; no filing time recorded. |
| `met` | Recorded filing time is at or before the deadline. |
| `late` | Recorded filing time is after the deadline. |
| `overdue` | Deadline passed; no filing time recorded. |

"Met" and "late" describe recorded timestamps, not the content or validity of what was filed. The legend says so.

**Label check:** the PRD says "fix available". The UI label is "Fix or mitigation available", with the citation "CRA Art. 14(2)(c)", because the regulation refers to a corrective or mitigating measure. To be checked against the Official Journal under D-5.

### 8.2 Events list (S-7)

**Responder view:**

```
Art. 14 events                              [+ Log event] [+ Start a clock] [+ Log drill]
Showing: Open (2) · Closed (5) · Drills (1)

┌────────┬──────────────────────────────┬──────────────────────┬──────────────────────┬──────────────────────┬────────────────┐
│ Ref    │ Type                         │ Early warning (24h)  │ Notification (72h)   │ Final report         │ Responder      │
├────────┼──────────────────────────────┼──────────────────────┼──────────────────────┼──────────────────────┼────────────────┤
│ E-0008 │ Actively exploited           │ ▲ OPEN               │ open                 │ not started          │ T. Nowak       │
│        │ vulnerability                │ due in 22h 40m       │ due in 2d 22h 40m    │ (no fix recorded)    │ AWAITING       │
│        │ Started by L. Braun          │                      │                      │                      │ RESPONDER      │
│ E-0007 │ Actively exploited           │ ▲ OPEN               │ open                 │ not started          │ T. Nowak       │
│        │ vulnerability                │ due in 5h 12m        │ due in 2d 05h 12m    │ (no fix recorded)    │                │
└────────┴──────────────────────────────┴──────────────────────┴──────────────────────┴──────────────────────┴────────────────┘
Each cell's tooltip and expanded row show the due time in local time and UTC.
```

**Vendor admin (non-responder) view:** same table, but rows are not clickable, there is no "Log event" or "Log drill" button, and "+ Start a clock" is shown. A note above the table says: "Event details are restricted to incident responders. You can see deadline states and who is responsible." Columns: ref, type, product, the three deadline states with countdowns, responder, awaiting-responder flag. Each row has a "Reassign responder" action (**Proposed**, 8.3a).

**Empty state:** "No Art. 14 events recorded. This list shows only events entered here."

### 8.3 Logging an event (F-4a, S-8, responders)

Designed to be completed in under 2 minutes, with only the clock-critical fields required.

```
Log Art. 14 event                                                         [Cancel]

1  Event type *
   (•) Actively exploited vulnerability   CRA Art. 14(1)
   ( ) Severe incident having an impact on the security of the product   CRA Art. 14(3)

2  When did you become aware? *
   Date [2026-10-22]  Time [08:05]  Time zone [Europe/Warsaw (CEST, UTC+02:00) ▾]
   = 06:05 UTC
   ⓘ Deadlines are calculated from this time. If it is wrong, every deadline is wrong.

3  Product and version *       [ScoreEngine ▾] [4.2 ▾]
4  Affected deployments        [▢ Bank A – prod (4.2)  ▢ Bank A – test (4.2)]  (can add later)
5  Title *                     [                                                 ]
6  Description, affected component, vector   (optional now; restricted to responders)
7  Responder *                 [T. Nowak (you) ▾]

Deadlines this will create (preview, updates as you type):
   Early warning   Thu 23 Oct 2026, 08:05 CEST · 06:05 UTC   in 23h 58m
   Notification    Sat 25 Oct 2026, 07:05 CET  · 06:05 UTC   in 2d 23h 58m
                   ⓘ Shown 1 hour earlier in local time because clocks change
                     on 25 Oct. The deadline is exactly 72 elapsed hours.
   Final report    Starts when a fix or mitigation is recorded.

                                                   [Log event and start clocks]
```

Validation (also applies to 8.3a):
- Awareness time in the future (beyond a 1-minute tolerance against server time): blocked. "Awareness time can't be in the future."
- Awareness time more than 24h ago: allowed, with an inline warning before saving: "The early warning deadline for this time has already passed. The event will show as overdue."
- Ambiguous local time (the repeated hour at a DST end): the user must pick the offset, e.g. "02:30 CEST (UTC+02:00)" or "02:30 CET (UTC+01:00)". No silent default.
- Non-existent local time (the skipped hour at DST start): blocked. "02:30 doesn't exist in Europe/Warsaw on 28 Mar 2027 (clocks go forward). Enter 01:59 or 03:00 or later."
- On save: the clock strip updates on every vendor screen at the next sync (target ≤ 60 s), and the event appears in S-7.

### 8.3a Starting a clock as a non-responder (F-4e, S-8a; decided, OQ-D4)

**Purpose:** a vendor admin who learns of an exploited vulnerability or severe incident first can start the clock straight away, without seeing or entering incident details. OQ2 holds: details stay responder-only.

**Form (S-8a), four fields only:**

```
Start an Art. 14 clock                                                    [Cancel]

You can start the deadlines now. An incident responder will add the details.
Don't describe the issue here. Tell the responder directly.

1  Event type *       (•) Actively exploited vulnerability  ( ) Severe incident
2  Awareness time *   Date [ ] Time [ ] Time zone [ ▾ ]  = .. UTC
3  Product *          [ScoreEngine ▾]
4  Assign to *        [T. Nowak – incident responder ▾]   (lists responders only)

Deadline preview (as in 8.3)
                                                        [Start clock and assign]
```

- No title, description, component, vector, version or deployments. The form has **no free-text field** at all, so details can't be typed into a field the starter could later see.
- The same time validation as 8.3 applies.
- If the tenant has no responder, the form is blocked: "No incident responder exists. Ask your access manager ([names]) to assign one." The strip shows the same message (5, step 6).

**Confirmation shown to the starter (once, after saving):**

```
Clock started · E-0008 · Actively exploited vulnerability
Awareness time you entered: Thu 22 Oct 2026, 13:47 CEST · 11:47 UTC
  Early warning   Fri 23 Oct 13:47 CEST · 11:47 UTC   in 23h 59m
  Notification    Sun 25 Oct 12:47 CET  · 11:47 UTC   in 2d 23h 59m
Assigned to T. Nowak. The dashboard does not notify them.
Contact T. Nowak now (phone, chat) and give them reference E-0008.

From now on you'll see this event's deadline states only. Details, including
any changes to the awareness time, are restricted to incident responders.
                                                                   [Done]
```

- The confirmation repeats only what the starter entered. After "Done", the starter sees the event like any non-responder admin (8.2): states, countdowns, responder, awaiting flag.
- "The dashboard does not notify them" is deliberate copy: there are no alerts, so the starter must make contact themselves.

**Routing and the awaiting-responder state:**
- The event is flagged **awaiting responder** until the assigned responder first opens its detail page. The flag shows on the clock strip, S-7 and S-2 for all vendor roles.
- Any responder (not only the assigned one) can open it and "Take over", which reassigns it to them and clears the flag. Audited.
- **Reassign responder (Proposed):** any vendor admin can reassign an event to a different responder, e.g. when the first one can't be reached. Assignment is not an incident detail. Audited.
- The starter can't edit the awareness time, type or product after saving. If they entered it wrong, they tell the responder, who edits it with a reason (8.5).

**Role check (the CPO's "confirm role"):** every request for incident details checks the responder role at that moment. A starter who is not a responder gets the restricted view even by direct URL. Granting the starter the responder role later gives them full access on their next request; removing it takes effect the same way. Both role changes are audited.

**Audit trail:** "Started clock" entry with actor, type, product, awareness time and assignee. The starter can see their own entry. Later changes to that event's details are masked for them (13).

### 8.4 Event detail (S-9, responders only)

```
E-0007 · Actively exploited vulnerability                    Responder: T. Nowak ▾
ScoreEngine 4.2 · Status: Open · Started by L. Braun (if admin-started)
[Edit awareness time] [Reclassify] [Close event] [Mark users informed]

Awareness time   Thu 22 Oct 2026, 08:05 CEST · 06:05 UTC   (edited once – see history)

Clocks                                                       CRA Art. 14(2)
┌───────────────────┬───────────────────────────────┬──────────────┬────────────────────────────┐
│ Deadline          │ Due                           │ State        │ Filing time recorded       │
├───────────────────┼───────────────────────────────┼──────────────┼────────────────────────────┤
│ Early warning 24h │ Thu 23 Oct 08:05 CEST         │ ▲ OPEN       │ [Record filing time]       │
│                   │ 06:05 UTC                     │ 5h 12m left  │                            │
│ Notification 72h  │ Sat 25 Oct 07:05 CET · 06:05Z │ open         │ [Record filing time]       │
│ Final report      │ –                             │ not started  │ needs "Fix or mitigation   │
│ (fix + 14 days)   │                               │              │ available" time            │
└───────────────────┴───────────────────────────────┴──────────────┴────────────────────────────┘
Fix or mitigation available   [Record time]          CRA Art. 14(2)(c)

ⓘ This tool does not draft or file reports. File with the single reporting platform
  yourself, then record the time you filed here.

Details (responders only; every view is logged)
  Title, description, affected component, vector, version, affected deployments [Edit]
  (For admin-started events these are empty: "Added by the starter: none. Add details.")

Customer users informed   CRA Art. 14(8)  ⓘ citation from secondary sources, pending check (D-5)
  Bank A – prod   Not recorded    [Mark informed]
  Bank A – test   Not recorded

History (from audit trail)
```

Recording a filing time: date, time, time zone (same picker as 8.3). Filing time can't be before the awareness time or in the future. Corrections need a reason and are audited.

### 8.5 Editing the awareness time (F-4b, S-11)

1. Responder clicks **Edit awareness time**.
2. Dialog: new date, time and time zone; **reason** (required, min 20 characters).
3. The dialog shows a **before/after table** of every deadline and state:
   ```
                    Before                    After
   Early warning    23 Oct 08:05 CEST  open   23 Oct 06:35 CEST  open (3h 42m left)
   Notification     25 Oct 07:05 CET   open   25 Oct 05:35 CET   open
   ```
   If any state changes (e.g. `met` → `late`, `open` → `overdue`), that row is highlighted and the dialog says it in words: "Early warning will change from met to late."
4. Confirm. The audit trail records old value, new value, reason, actor, UTC time.
5. Event detail shows "Awareness time edited [n] times" with a link to the history, and a banner for 24h after the edit: "Deadlines recalculated at 10:12 CEST after an awareness-time edit."
6. Non-responder admins see only the recomputed countdowns, plus a neutral note on the row for 24h: "Deadlines recalculated by a responder at 10:12 CEST." They don't see the old or new awareness time or the reason.

### 8.6 Reclassifying an event (F-4c, S-12)

Reclassification switches between `actively exploited vulnerability` and `severe incident`.
- Reason required; audited.
- Before/after table as in 8.5. The 24h and 72h clocks don't move (both run from awareness). The final-report rule changes basis, and the state may become `not started`.
- Filing times already recorded are kept. The dialog warns: "Filings recorded so far were made under the previous type. Check whether you need to file again under the new type."
- **Linked events. Proposed, pending engineering review at `/plan` (OQ-D7).** One real-world occurrence can be both an exploited vulnerability and a severe incident. The PRD has one type per event. Reclassify handles a wrong type; a **"Log linked event"** action creates a second event pre-filled with the same product and deployments (awareness time entered fresh), and both show "Linked to E-00xx".

### 8.7 Closing an event (S-13). Proposed, pending engineering review at `/plan` (OQ-D7)

The PRD has no end state for events.
- **Closed – reporting complete:** available once all three filing times are recorded.
- **Closed – determined not reportable:** e.g. the vulnerability turned out not to be actively exploited. Rationale required. Clocks stop and show "stopped – event closed as not reportable on [date]". The record is kept.
- Events are never deleted.
- Closed events leave the clock strip and move to "Closed" in S-7.

If engineering review rejects this, the fallback is that events stay open forever and the strip has to filter them some other way. That fallback would need a design revisit.

### 8.8 Drills (F-4d, for PRD P4). Proposed, pending engineering review at `/plan` (OQ-D8)

Logged as real events, drills would pollute the regulatory record and could be released to the customer.
- **"+ Log drill"** uses the same form with a fixed "DRILL" banner. The drill flag is set at creation and can't be changed.
- Drills behave exactly like real events (clock strip, countdowns, tab title, filings, awareness edits, **and admin-started clocks**), so the drill tests the real flow. A non-responder can start a drill clock from S-8a with a "This is a drill" checkbox, so P4 can test the 8.3a path too.
- Drills are labelled DRILL everywhere, with a hatched background. They are excluded from customer views, customer exports and summary counts. "Mark users informed" on a drill shows the customer-view preview but releases nothing.
- At the end of a drill, the responder records "Would the 24h early warning have been met? Yes / No / Notes" (the P4 confirmation).

---

## 9. Releasing incidents to customers, and the customer view

### 9.1 Mark users informed (F-5, S-10)

**PRD ambiguity resolved:** R-3 describes one "users informed" timestamp. R-4 releases incidents per deployment. The design records **one informed time per affected deployment**.

Flow:
1. Responder clicks **Mark informed** for a deployment (or selects several).
2. **Step-up re-authentication** (decided, OQ-D6): the responder confirms MFA again before the dialog opens.
3. Dialog fields: time users were informed (date, time, time zone; not in the future, not before awareness); method (optional free text, e.g. "email to CISO").
4. **Release preview**, mandatory and not collapsible:
   ```
   This will make the following visible to Bank A's read-only admins
   (2 accounts):

   Incident shared with you
     Reference     E-0007
     Type          Actively exploited vulnerability
     Product       ScoreEngine 4.2 (your deployment: Bank A – prod)
     Informed on   Fri 23 Oct 2026, 11:00 CEST
     Fix or mitigation available   Not recorded yet

   They will NOT see: description, component, vector, awareness time,
   deadline states, filing times, other deployments, or other customers.
   ```
   The preview gives the **number** of customer accounts, not names. Names of customer admins are on the access screen (S-14) where the vendor manages them; the release preview doesn't need them.
5. Checkbox: "I confirm affected users at Bank A have been informed." Then **Release to Bank A**.
6. Audited. In S-9 the deployment row shows "Informed Fri 23 Oct 11:00 CEST · released to customer view".

**Correction:** "Correct informed time" or "Withdraw release" needs a reason and is audited. Withdrawal warns: "Bank A may already have seen or exported this. Withdrawing removes it from their view from now on." The vendor's audit trail shows whether the customer viewed or exported it, attributed per the customer's activity-sharing setting (9.6).

### 9.2 What the customer sees (decided, OQ-D1 and OQ-D2)

| Item | Customer sees | Basis |
|---|---|---|
| Requirement citation, short title, status, review-by date, last-changed date | Yes | R-4. |
| N/A and acceptance rationale text | Yes | OQ-D2 decided. Vendor is told on S-4 and S-6. |
| Evidence item title, type, date | Yes | OQ-D2 decided. |
| Evidence files and URLs | **No** | OQ-D2 decided. The customer can ask the vendor for them. |
| AI-risk name, Art. 15(5) class, handling stage, last tested, last reviewed | Yes | R-4. |
| AI-risk owner name | **No** – shown as "Owner assigned" | OQ-D2 decided; NFR-5. |
| Incident fields | Only the fields in the release preview (9.1) | OQ1. |
| Art. 14 deadline states, awareness time, filing times | **No, never** | OQ-D1 decided. |
| Drills, other deployments, other customers, unreleased incidents | Never | OQ1, NFR-2. |

### 9.3 Customer overview (S-B1)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ [Tracker]  Bank A · read-only view of information from Acme Scoring GmbH  J.S. ▾ │
├──────────────────────────────────────────────────────────────────────────────────┤
│ About this view: Acme Scoring GmbH entered all information shown here. It is not │
│ a determination of compliance. [What this view does and doesn't show →]          │
│ Your activity is shown to Acme as: named users  [Change →]                       │
├──────────────────────────────────────────────────────────────────────────────────┤
│ Your deployment   Bank A – prod · ScoreEngine version 4.2                         │
│ Annex III category selected by vendor: 5(b)  · Information last updated 21 Oct    │
│                                                                                   │
│ Requirements (CRA Annex I, AI Act Art. 15)                                        │
│   Evidence attached for 9 of 35 requirements.                                     │
│   9 evidence attached · 2 evidence stale · 3 not applicable · 6 in progress ·    │
│   15 not started                                       [View requirements →]      │
│                                                                                   │
│ AI-risk register                                                                  │
│   14 risks recorded by the vendor. 6 treatment in place – evidence attached · ... │
│                                                         [View register →]         │
│                                                                                   │
│ Incidents shared with you                                                         │
│   1 incident shared with you.                           [View →]                  │
│                                                                                   │
│                                              [Export for review (PDF / CSV)]      │
├──────────────────────────────────────────────────────────────────────────────────┤
│ Status reflects information entered by Acme Scoring GmbH. It is not a             │
│ determination of compliance.                              Times shown: CET        │
└──────────────────────────────────────────────────────────────────────────────────┘
```

- **No clock strip** in the customer workspace, ever.
- **Zero-incident wording:** "No incidents have been shared with you for this deployment. The vendor shares an incident here after recording that it informed your users (CRA Art. 14(8))." This exact text appears whether the vendor has unreleased incidents or none, so nothing can be inferred.
- Response times, page sizes and error messages must not differ between "nothing exists" and "exists but not released" (NFR-2; also a test requirement for `/plan`).
- If the deployment's version isn't recorded: "The vendor hasn't recorded which version this deployment runs, so no status can be shown."
- If the customer has several deployments, a deployment selector appears; each view is scoped to one deployment.
- The activity-sharing line ("Your activity is shown to Acme as: …") is always visible, so customer users know the vendor can see their views and exports (9.6).

### 9.4 "About this information" (S-B5)

A plain-language page, also printed as page 2 of the export. Legal review is the audience. Sections:
1. **Who entered this:** "All statuses, evidence descriptions and dates were entered by Acme Scoring GmbH. [Product name] stores and displays them. We have not verified them."
2. **What each status means:** the full legends from 6.1 and 7.1.
3. **What this view does not show:** evidence files; incidents not yet shared with you; the vendor's reporting deadlines and filings to authorities; other customers' information.
4. **What this is not:** "This is not a certification, conformity assessment, audit opinion or determination of compliance with Regulation (EU) 2024/2847 (Cyber Resilience Act) or Regulation (EU) 2024/1689 (AI Act)."
5. **Regulatory references used:** CRA Art. 12, 13, 14 and Annex I; AI Act Art. 15 and Annex III 5(b); CRA Recital 51 (context only, not binding). Each with a link to EUR-Lex.
6. **What the vendor sees about your use** (new in draft 2): "Acme Scoring GmbH can see when your organisation views this information and generates exports. You can choose whether it sees your users' names or only your organisation's name. [Activity sharing →]"

Final wording of 1, 4 and 6 needs legal review (D-4).

### 9.5 Customer review and export (F-6, S-B6)

Flow: customer admin opens **Export for review** → chooses PDF (for legal) or CSV (for their risk tooling) → the export is generated for the current deployment → download. The vendor's audit trail records it, attributed per the customer's activity-sharing setting (9.6). S-B6 also lists the customer's own past exports (export ID, date, generated by) so they can tell which copy their legal team has.

**PDF export layout:**

| Page | Content |
|---|---|
| Cover | Title "Information provided by Acme Scoring GmbH for Bank A – prod"; product and version; generated at (UTC and local); **generated by** (see 9.6.4); data as of; **export ID**; NFR-8 notice in body text size, not small print. |
| 2 | "About this information" (S-B5 in full). |
| 3+ | Requirements table: citation, short title, status, evidence titles and dates, review-by, last changed, rationale. Grouped by requirement set, with summary counts at the top of each group. |
| next | AI-risk register table: risk, Art. 15(5) class, handling stage, last tested, last reviewed. |
| next | Incidents shared with this deployment (or the zero-incident wording). |
| Every page | Footer: NFR-8 notice, export ID, page x of y. |

- **Export ID:** recorded with a content hash, so either party can later ask the service to confirm an export is genuine and unaltered. Verification answers "genuine, generated [date]" without revealing the generator's identity to a vendor if the customer has anonymized (9.6.4).
- PDF must be tagged (accessible PDF, PDF/UA target).
- CSV export has the notice as its first rows and an ISO 8601 UTC column for every time. Cells starting with `=`, `+`, `-` or `@` are escaped (formula-injection protection).
- Vendor admins can generate the same export from S-14 ("Preview customer export") so the vendor sees exactly what the bank's legal team will read.

### 9.6 Customer activity sharing and anonymization (F-9, S-B7; decided, OQ-D9)

**Decision:** the vendor sees when the customer views released information and generates exports. The customer can anonymize its users' identities in what the vendor sees.

#### 9.6.1 What the vendor sees

Customer activity events written to the vendor's audit trail:
- viewed an incident shared with them (first view per user per incident);
- generated an export (PDF or CSV), with export ID;
- signed in to the customer workspace (**Proposed**: daily first sign-in only, so the vendor knows the view is used without a page-by-page log).

Page-by-page browsing of requirements and risks is **not** sent to the vendor. It isn't needed and would be surveillance of the customer's review.

Customer users never change vendor data, so there are no customer "last changed" records. The only customer-originated entries are the activity events above, plus changes to the sharing setting itself.

#### 9.6.2 What the customer can anonymize

| Field in the vendor's view | Named (setting A) | Organisation only (setting B) |
|---|---|---|
| Actor on customer activity entries | "J. Schmidt (Bank A)" | "Bank A user" |
| "Generated by" on export audit entries | "J. Schmidt (Bank A)" | "Bank A user" |
| Export cover page "Generated by" | Name | "Bank A" (9.6.4) |
| Number of distinct customer users active | Visible by implication | Not shown. Entries carry no stable pseudonym. |

**Proposed:** setting B uses no stable pseudonym ("Bank A user 3"), because a stable pseudonym lets the vendor re-identify people by behaviour pattern, and with only 2 customer accounts in the pilot it would add nothing. Flagged in 21.

**What anonymization can't hide:** the vendor invites customer admins (OQ-D5), so the vendor's access screen (S-14) still lists the customer's accounts by email; the vendor needs that to manage and revoke access. Anonymization hides **who did what**, not **who has an account**. The S-B7 screen says this plainly.

#### 9.6.3 Where the customer controls it, and the default

- **Screen S-B7 "Activity sharing"**, under the customer user menu, and linked from the overview line in 9.3 and from S-B5.
- **Who can change it:** any customer read-only admin at that customer. It is an organisation-wide setting, not per user. **Proposed;** a per-user choice would let one colleague's name show while another's doesn't, which is confusing for a two-person team. This is the only thing a customer admin can edit.
- **Default: no default is applied silently.** On the customer's first sign-in, before the overview loads, the first customer admin must choose A or B on an interstitial page that explains both options. Until someone chooses, activity is recorded as **organisation only** (B). This avoids defaulting people into being named (GDPR Art. 25(2), data protection by default) while still making it a real option, as the CPO decided.

```
Activity sharing · Bank A

Acme Scoring GmbH can see when people at Bank A view incidents shared with you
and generate exports. Choose how they appear to Acme:

 ( ) Named users          Acme sees each person's name, e.g. "J. Schmidt (Bank A)".
 (•) Organisation only    Acme sees "Bank A user". It can't tell which of you it was.

Acme still sees who has an account at Bank A, because Acme manages invitations.
Changing this setting is recorded and Acme sees that it changed.
[Save]                                         Last changed 21 Oct 2026 by you
```

#### 9.6.4 Interaction with the export cover page

- **Setting A:** cover page reads "Generated by J. Schmidt, Bank A".
- **Setting B:** cover page reads "Generated by Bank A". The customer's own export history in S-B6 still shows the person's name, because that is the customer's own record.
- **Why the cover follows the setting:** exports are often forwarded, including back to the vendor. A name on the cover would undo the anonymization.
- **Integrity:** the export ID and content hash are unaffected. The hash covers the PDF as generated, including whatever "Generated by" text it carries. Verification confirms authenticity and date without revealing the person.

#### 9.6.5 How anonymization is audited

- The **underlying audit record always stores the real actor** (user ID, name, tenant). Anonymization is applied when the vendor's view and exports are rendered, not by deleting data. The audit trail stays append-only and internally attributable (NFR-3).
- **Who can see the real actor of a customer action:** the customer's own admins (in S-B6 export history and S-B7 history), and our service under a documented legal or security process. Never the vendor while setting B is on.
- **Changing the setting** is itself an audit entry. The vendor sees "Bank A changed activity sharing to organisation only (21 Oct 2026, 10:14 UTC)", with the actor anonymized if the new setting is B. The customer sees the actor's name in S-B7 history.
- **Direction rules:**
  - **Named → organisation only:** applies to past and future entries in the vendor's view and in future vendor audit exports. Audit exports the vendor downloaded earlier can't be recalled; S-B7 says so: "Exports Acme has already downloaded may contain names."
  - **Organisation only → named:** applies from the moment of change only. Past entries stay anonymized, so nobody is named retroactively for activity they did under anonymity.

#### 9.6.6 Tensions to flag (for legal and `/plan`)

- **GDPR:** customer-user activity is personal data for us even when anonymized in the vendor's view. In the vendor's view it is closer to pseudonymised than anonymous, because the vendor knows the account list and, with two accounts, can sometimes guess. Copy says "organisation only", not "anonymous", for this reason. We need a lawful basis and a retention period for customer activity records; that is for counsel and `/plan` (D-4).
- **Audit integrity versus the vendor's evidence needs:** a vendor using its audit export as technical documentation gets customer entries it can't attribute. Acceptable, because customer actions are views and exports, never changes to the vendor's records.
- **Security investigations:** if a customer account is misused (e.g. mass export), the vendor can't see who did it under setting B. Proposed path: the vendor raises it with us and the customer; the customer sees its own names. This needs a documented process before the pilot.

---

## 10. Visual and status language

### 10.1 Why

A green tile reads as "compliant". A progress bar reads as a score. A red cross reads as "failed". This product must not show any of them for requirements or risks.

### 10.2 Rules for requirement and AI-risk status

- **One neutral palette** (greys and the brand's neutral ink) for every requirement and risk status. **No green, no red, no amber** on these statuses.
- Status chips are **text first**, with a distinct shape icon so status is never shown by colour alone (WCAG 1.4.1):
  - ○ not started / not assessed
  - ◇ in progress / assessed – treatment planned
  - ◆ evidence attached / treatment in place – evidence attached
  - ◈ evidence stale, with a calendar icon and the words "date passed"
  - ⊘ not applicable (with rationale), accepted with rationale (rationale shown on hover and in detail)
- Icons are not ordered visually as a progression (no fill levels, no ticks). ◆ is "has evidence", not "done".
- No percentages, progress bars, gauges, donuts, heat maps, grades, stars, or "health".
- Summaries are sentences with a denominator and full breakdown.
- Stale items are shown with bold text and the calendar icon, and listed in a "Review dates passed" panel on S-2. Staleness is emphasised by weight and position, not by alarm colour.

### 10.3 Rules for Art. 14 clocks

Clocks are time facts, and missing one is the product's biggest operational risk, so they may use colour. Colour still never means good or bad quality.

| Tier | Treatment |
|---|---|
| Overdue (also: "no incident responder assigned") | High-contrast red background, white text, ▲ icon, word "OVERDUE", "by 1h 03m". |
| Early warning open | Dark amber/orange background, dark text, ▲ icon, word "OPEN", countdown. |
| Awaiting responder | Same colour as the row's tier, plus the words "AWAITING RESPONDER" in a bordered label. |
| Notification or final report open | Outlined amber, countdown. |
| Met / late / not started | Neutral text. "met" is not green and has no tick. "late" is neutral text with the word "late", not red, because it records a past fact the user can't change. |
| Drill | Same tier colour plus diagonal hatching and the word DRILL. |

All colour pairs meet 4.5:1 contrast. Every tier also carries a word and an icon.

### 10.4 Countdown format

- More than 24h: `2d 05h 12m`. Under 24h: `5h 12m`. Under 1h: `47m`. Past due: `Overdue by 1h 03m`.
- Minute resolution (NFR-4). No seconds, no animated ticking.
- Screen readers: the countdown has an accessible name, e.g. "Early warning due in 5 hours 12 minutes, at 08:05 CEST". A polite live region announces only tier changes (e.g. "Early warning now overdue"), not every minute.

---

## 11. Edge cases

### 11.1 Time zones and DST

- **Storage UTC; display local plus UTC** for every deadline and every recorded time, e.g. `Thu 22 Oct 2026, 14:05 CEST · 12:05 UTC`. 24-hour clock. The zone abbreviation is always shown.
- **Display zone:** the user's profile setting (default: browser zone). The footer states it.
- **Elapsed-hours clocks across DST:** 24h and 72h are elapsed hours. When a DST change falls inside the window, the local due time shifts by an hour, and an inline note explains it (8.3). Test cases: EU changeovers on 25 Oct 2026, 28 Mar 2027, 31 Oct 2027.
- **Ambiguous and non-existent local times:** see 8.3.
- **Weekend:** 72h across a weekend is not extended. Copy near the notification clock: "Calendar hours. Weekends and holidays are not excluded."
- **Calendar month (severe-incident final report):** decided interim rule (OQ-D10): same calendar day next month in UTC, clamped to the last day of the month (31 Jan → 28 Feb, or 29 Feb in a leap year), at the same UTC time of day. Shown with "Calculated as one calendar month. Pending legal confirmation." Until D-4 closes.
- **Client clock skew:** countdowns use server time. If the browser clock differs by more than 60 s: "Your device clock differs from the server. Countdowns use server time."
- **Connection lost:** the clock strip shows "Not synced since 14:05 – reconnecting" and keeps counting down from the last known server time. It never silently shows stale data.

### 11.2 Awareness-time edits

- Covered in 8.5. Edits that move awareness earlier can turn `open` into `overdue` and `met` into `late`; the dialog says so before confirming.
- Edits after a release to the customer change nothing in the customer view, which doesn't show awareness time.
- Concurrent edits: the second saver sees "Awareness time was changed by A. Kral at 10:12. Review before saving."
- Admin-started events: the starter can't edit the awareness time (8.3a).

### 11.3 Multi-tenant boundaries

- A user belongs to exactly one tenant (vendor or customer). No tenant switcher in the MVP.
- Customer selector lists only the customer's own deployments. URLs to other deployments, events or tenants return the same "Not found" page as a non-existent item. No "access denied" that would confirm existence.
- The same applies inside the vendor tenant: a non-responder opening an event-detail URL gets the restricted row view, not the details.
- A customer of two vendors gets two separate customer tenants and two sign-ins in the MVP. Activity-sharing settings are separate per tenant.
- When a deployment is removed or moved to another customer, previously released incidents stay with the original customer tenant's history (**Proposed**), and the change is audited.
- Search, autocomplete and filters in the customer workspace query only that customer's released data.

### 11.4 Reclassification

See 8.6. Reclassifying a released incident updates the type shown to the customer, and the customer view shows "Type updated by vendor on [date]".

### 11.5 Version changes (decided, OQ-D3)

- A new version can **carry forward** statuses and evidence from a previous version. Carried-forward items show "Carried forward from 4.1 on [date]" until edited. Review-by dates are kept, so staleness still applies.
- When a deployment moves to a new version, the customer view switches to that version's status and says "Your deployment moved from 4.1 to 4.2 on [date]."

### 11.6 Session expiry versus passive monitoring (decided, OQ-D6)

- Idle timeout: **8 hours** for vendor roles, **30 minutes** for customer roles.
- On expiry, the page clears all content and the tab title changes to `Signed out – deadlines hidden`, so nobody mistakes a stale screen for a live one.
- Step-up re-authentication is required for "Mark informed" only (9.1).

### 11.7 Responder role changes

- If the assigned responder loses the role, their events show "Assigned responder no longer has the role" in the overdue tier on the strip, and any vendor admin can reassign.
- If the last responder in the tenant loses the role, the strip shows "No incident responder assigned. Clocks can't be routed."

### 11.8 CSV edge cases

See section 12.2.

---

## 12. CSV import (F-7, S-15)

### 12.1 Scope

- **Imports:** requirement statuses (with N/A rationale, review-by date, evidence metadata) and AI risks (create or update, handling stage, rationale, owner by email, last tested, last reviewed, evidence metadata).
- **Not imported: Art. 14 events. Proposed, pending engineering review at `/plan` (OQ-D8).** A clock-starting record should be entered deliberately through S-8 or S-8a, with its time-zone validation. Drills test that path.
- `evidence stale` can't be imported (system-only). Files can't be imported; evidence rows carry a title, type, date and optional URL.

### 12.2 Flow

1. **Choose target:** Requirements for [version] or AI risks for [version].
2. **Download template.** Generated from the data: requirement rows come pre-filled with stable requirement IDs and citations, so the vendor fills in status columns only. A header comment row lists the allowed status values.
3. **Upload** (UTF-8 CSV, max size stated on screen).
4. **Validate and preview:**
   ```
   Import preview · Requirements · ScoreEngine 4.2
   35 rows read · 12 will change · 21 unchanged · 2 errors

   Errors (fix and re-upload; nothing is imported while errors remain)
     Row 14  CRA Annex I, Part II(3): status "not applicable" needs a rationale.
     Row 22  review_by "31/06/2027" is not a valid date. Use YYYY-MM-DD.

   Changes
     Row 3   CRA Annex I, Part I(1)   not started → evidence attached (review by 2027-06-30)
     ...
   ```
5. **All or nothing:** import is blocked until there are 0 errors.
6. **Confirm:** "Import 12 changes". Each change is an individual audit entry, tagged with the import ID and filename.
7. **Result:** "12 changes imported at 14:22 CEST. [View in audit trail]".

Other rules: unknown requirement IDs are errors; duplicate rows for the same ID are errors; dates are `YYYY-MM-DD`; an owner email that isn't a vendor user is an error; status values are matched exactly against the vocabulary. A rationale column is labelled in the template as "visible to customers".

---

## 13. Audit trail (F-8, S-16, NFR-3)

```
Audit trail                                              [Export CSV] [Export JSON]
Filter: Actor [All ▾]  Area [All ▾]  Action [All ▾]  From [    ] To [    ]  Ref [   ]

┌──────────────────────────────┬──────────────┬────────────────────┬──────────────────────────────────────────────┐
│ When                         │ Who          │ Action             │ Change                                       │
├──────────────────────────────┼──────────────┼────────────────────┼──────────────────────────────────────────────┤
│ 22 Oct 13:49 CEST · 11:49 UTC│ L. Braun     │ Started clock      │ E-0008 · actively exploited vulnerability ·   │
│                              │ (admin)      │                    │ assigned T. Nowak                             │
│ 22 Oct 10:12 CEST · 08:12 UTC│ T. Nowak     │ Edit awareness time│ E-0007 · [value hidden: responders only]      │
│                              │ (responder)  │                    │                                              │
│ 22 Oct 10:05 CEST · 08:05 UTC│ M. Kowalska  │ Viewed details     │ E-0007                                        │
│ 21 Oct 16:40 CEST · 14:40 UTC│ Bank A user  │ Exported (PDF)     │ Bank A – prod · export ID X-3F9A…             │
│                              │ (customer)   │                    │ (Bank A shares activity as organisation only) │
│ 21 Oct 11:02 CEST · 09:02 UTC│ L. Braun     │ Status change      │ Annex I Part I(2)(f) · in progress →          │
│                              │              │                    │ evidence attached                             │
└──────────────────────────────┴──────────────┴────────────────────┴──────────────────────────────────────────────┘
(The "Edit awareness time" row above is how a non-responder admin sees it.
 A responder sees old value, new value and reason.)
```

- **Append-only.** No edit or delete controls exist.
- Every entry: actor name, role, tenant; action; target; previous and new value; reason where required; UTC and local time; import ID or export ID where relevant.
- **Incident masking:** for vendor admins without the responder role, values of incident-detail fields (including awareness time after the start) are shown as `[value hidden: responders only]`. That a change or view happened is still shown. A starter sees the values in their own "Started clock" entry.
- **Customer anonymization:** customer activity entries show the actor per the customer's setting (9.6). The "Who" filter lists "Bank A user" as a single actor under setting B.
- **Exports** (CSV, JSON) for the vendor's technical documentation apply the same masking and anonymization. The export itself is an audit entry.
- **Empty filter state:** "No entries match these filters."
- Also serves PRD P5 (weekly active admins) as a source; no separate analytics screen.

---

## 14. Screen inventory and states

| ID | Screen | Roles | Empty | Loading | Error | Overdue | Stale |
|---|---|---|---|---|---|---|---|
| S-0 | Sign-in, access states | All | – | "Signing you in…" | SSO failure: "Sign-in didn't complete. Contact your administrator." MFA not set up: blocked with setup instructions. No account: "You don't have access to this workspace." | – | – |
| S-1 | Shell + clock strip | Vendor | "No open Art. 14 clocks recorded." | "Loading clocks…" in place (never blank) | "Clocks couldn't be loaded. [Retry]" in the strip, high emphasis | Red tier; "no responder assigned" | Not synced notice (11.1) |
| S-2 | Vendor overview | Vendor | Setup checklist | Skeleton | Per-panel error with retry | Clock hero panel at top | "Review dates passed (n)" panel |
| S-3/S-4 | Requirements list/detail | Vendor | "No requirement set is attached to this version." | Skeleton rows | Save error, conflict | – | ◈ chip, panel on S-2 |
| S-5/S-6 | AI-risk register/detail | Vendor | "No AI-specific risks recorded…" | Skeleton | As above | – | ◈ chip |
| S-7 | Events list | Vendor (2 variants) | "No Art. 14 events recorded. This list shows only events entered here." | Skeleton | Retry | Row tier colour; awaiting-responder label | – |
| S-8 | Log event | Responder | – | – | Validation inline; save error keeps input: "Event not logged. Clocks have not started." | Warning if awareness > 24h ago | – |
| S-8a | Start a clock | Any vendor admin | No responder exists: blocked with access-manager names | – | As S-8 | As S-8 | – |
| S-9 | Event detail | Responder | Admin-started: empty details prompt | Skeleton | Retry; role removed mid-session: reloads to restricted view | Clock rows | – |
| S-10 | Mark users informed | Responder | – | Step-up prompt | "Not released. Bank A cannot see this incident." | – | – |
| S-11/12/13 | Awareness edit, reclassify, close | Responder | – | – | Not saved: before/after table kept | Highlighted state changes | – |
| S-14 | Products and customers, users and roles | Vendor (access managers edit roles and invites) | Setup checklist | Skeleton | Retry | – | – |
| S-15 | CSV import | Vendor | – | "Validating 35 rows…" | Row errors; file errors ("Not a CSV", "Too large") | – | – |
| S-16 | Audit trail | Vendor | "No entries match these filters." | Skeleton | Retry | – | – |
| S-17 | Exports | Vendor | – | "Generating export…" | "Export failed. Nothing was downloaded." | – | – |
| S-B0 | Activity-sharing first-run choice | First customer admin | – | – | "Not saved. Your activity is still shown as organisation only." | – | – |
| S-B1–B4 | Customer views | Customer | Zero-incident wording; "no version recorded" | Skeleton | Generic, non-revealing | Not shown (no clocks) | ◈ chips, as vendor |
| S-B5 | About this information | Customer | – | – | – | – | – |
| S-B6 | Customer export and own export history | Customer | "No exports yet." | "Generating…" | "Export failed. Nothing was downloaded." | – | Items stale at export time shown as stale |
| S-B7 | Activity sharing | Customer | – | – | "Not saved. Setting unchanged." | – | – |

Every screen and export carries the NFR-8 notice.

---

## 15. Content and copy rules

### 15.1 Disclaimer (NFR-8)

- **Footer and export notice, exact text:** "Status reflects information entered by **{vendor legal name}**. It is not a determination of compliance."
- Shown in full on every screen, every export page and every CSV. Not shortened, not hidden behind a tooltip, and at least body-text size on export cover pages.
- Final wording subject to legal review (D-4). Must be one configurable string so legal changes don't need a release.

### 15.2 Banned and required wording

| Never use | Use instead |
|---|---|
| compliant, non-compliant, compliance status, compliance score | "evidence attached for 9 of 35 requirements", "status entered by vendor" |
| certified, attested, verified (about the vendor's data), approved | "entered by", "recorded" |
| ensures, guarantees | supports |
| passed, failed, pass/fail, healthy, secure, safe, ready, CRA-ready | the specific status word |
| risk score, severity rating, robustness rating | handling stage |
| No incidents / No vulnerabilities / All clear | "No events recorded here", "No incidents have been shared with you…" |
| submit, file, report (as our action) | "Record filing time"; "File with the single reporting platform yourself" |
| notify, alert (about our product's behaviour) | "The dashboard does not notify them" (8.3a) |
| anonymous (about customer activity) | "organisation only" (9.6.6) |
| CRM | CRA |
| Art. 51 | Recital 51, always with "(context, not binding)" |
| bank (in UI chrome) | customer, or the customer's name |

"Compliance" appears only inside the NFR-8 notice and the "What this is not" text.

### 15.3 Citations

Exact format, always shown next to the thing it governs:
- `CRA Art. 12`, `CRA Art. 13`, `CRA Art. 14(1)`, `CRA Art. 14(2)(c)`, `CRA Art. 14(3)`, `CRA Art. 14(8)`;
- `CRA Annex I, Part I(2)(f)`, `CRA Annex I, Part II(3)`;
- `AI Act Art. 15`, `AI Act Art. 15(5)`, `AI Act Annex III 5(b)`;
- `CRA Recital 51 (context, not binding)`.

Citations come from the requirement-set data, not from UI strings. Art. 14(8) and Art. 14(2)(c) carry a "pending Official Journal check" marker until D-5 closes; the marker is a data flag, removable without a release.

### 15.4 Tone

Plain, factual, short. Errors say what didn't happen and what to do ("Not saved. Your change was not recorded. Retry."). No exclamation marks, no reassurance ("You're all set!").

---

## 16. Accessibility (WCAG 2.2 AA) and security-visible UI

- Status never by colour alone (1.4.1); 4.5:1 text contrast, 3:1 for icons and focus rings (1.4.3, 1.4.11).
- Sticky clock strip reserves layout space and never obscures focus (2.4.11).
- Targets at least 24×24 px (2.5.8). No drag-only interactions (2.5.7).
- Date and time are typed fields with optional pickers, never picker-only. Time-zone select is searchable.
- Authentication: no cognitive tests in our UI (3.3.8). Customer MFA setup (5.1) must offer passkeys and authenticator apps, with copy-paste allowed for codes.
- Help link in the same place on every screen (3.2.6). No repeated data entry (3.3.7): CSV preview and dialogs keep what the user typed after an error.
- Tables use proper headers; countdowns have full accessible names; live region announces tier changes only.
- Reflow at 320 px (1.4.10): the clock strip stacks; tables become cards. S-7, S-8, S-8a and S-9 must be fully usable on mobile, since the person who learns of an incident may be on a phone at night.
- Tagged PDF exports.
- Security-visible UI: "Last sign-in" shown in the user menu; sensitive actions (awareness edit, mark informed, withdraw release, reclassify, close, role changes) use the confirm-with-reason dialogs above. Step-up re-authentication for "Mark informed" (decided, OQ-D6).

---

## 17. UX tradeoffs and simplifications

| Decision | Why | What it costs |
|---|---|---|
| Neutral palette for all requirement and risk statuses | Avoids the green-means-compliant reading (CEO caveat 4, PRD risk table). | Scanning is slower. Mitigated by text-first chips, filters and the stale panel. |
| Text summaries, no progress bars | A bar is a score. | Less visual "motivation" for the vendor. |
| Clock strip on every page, non-dismissible | Only mitigation for no alerts. | Uses vertical space on every screen. |
| Customer never sees Art. 14 deadline states (decided, OQ-D1) | Protects the paying vendor; OQ1 only promised released incidents. | The bank's legal team sees less about the vendor's reporting discipline. Worth asking in the P6 conversation whether that matters. |
| Evidence files not shared with customers (decided, OQ-D2) | Confidentiality; simpler access model. | Legal review sees titles, not documents. |
| Start-a-clock form with no free text (OQ-D4) | Guarantees a non-responder starter never enters or later sees details. | The starter must hand over context by phone or chat. |
| Organisation-wide activity setting, no pseudonyms (OQ-D9) | Simple, and harder to re-identify. | The vendor can't count distinct customer users under setting B. |
| Events not in CSV import (pending engineering review) | Clock-starting data should go through the validated form. | Slower back-filling of historical events. |
| All-or-nothing CSV import | No half-imported states to explain. | One bad row blocks the file. |
| Status per product version (decided, OQ-D3) | Required for "the version I run". | More records; carry-forward needed. |
| One informed time per deployment | R-4 can't work otherwise. | Slightly more complex than R-3's single field. |
| No tenant switcher, one tenant per user | Simplest isolation story for the pentest. | A person working for two customers needs two accounts. |

**Cut or not designed:** alerts of any kind; report drafting and filing; public disclosure; integrations; scores; customer-side editing or comments; a customer audit trail beyond own exports and setting history; analytics dashboards (the audit trail is the source for P5); customer self-invites.

---

## 18. Deviations from, and clarifications of, the PRD

None of these change a PRD goal.

| # | Deviation | Status |
|---|---|---|
| 1 | "Users informed" recorded per deployment, not one field per event (R-3 vs R-4 conflict). | Pending CPO confirmation |
| 2 | Drill events (8.8), to make P4 safe. | **Pending engineering review at `/plan` (OQ-D8)** |
| 3 | Event close states, including "determined not reportable" (8.7), and linked events (8.6). | **Pending engineering review at `/plan` (OQ-D7)** |
| 4 | Both "last tested" and "last reviewed" on AI risks (OQ3 names one, R-2 the other). | Pending CPO confirmation (OQ-D14) |
| 5 | `evidence stale` is system-set only, for requirements and risks. | Pending CPO confirmation |
| 6 | Status recorded per product version, with carry-forward. | **Settled by OQ-D3** |
| 7 | "Fix or mitigation available" label instead of "fix available", pending D-5. | Pending CPO confirmation |
| 8 | Art. 14 events excluded from CSV import. | **Pending engineering review at `/plan` (OQ-D8)** |
| 9 | Export ID and content hash on exports. | Pending CPO confirmation |
| 10 | Delivery-model field in product setup. | Pending CPO confirmation (OQ-D13) |
| 11 | Customer-facing UI says "customer", not "bank" (R-X1). | Pending CPO confirmation |
| 12 | Browser tab-title countdown. | Pending CPO confirmation (OQ-D11) |
| 13 | **New in draft 2:** any vendor admin can start a clock (widens R-3's "as a vendor incident responder" story). | **Settled by OQ-D4** |
| 14 | **New in draft 2:** vendor sees customer views and exports, with customer anonymization (PRD silent). | **Settled by OQ-D9**; the detailed rules in 9.6 are pending CPO confirmation |
| 15 | **New in draft 2:** at least one incident responder required before setup completes. | Pending CPO confirmation (follows from OQ-D4) |

---

## 19. Traceability

| PRD item or decision | Screens | Flows | Notes |
|---|---|---|---|
| Goal 1 / R-1 statuses and citations | S-3, S-4, S-B2 | F-2 | 6.1 vocabulary; citations from data |
| R-1 count summary, not a score | S-3, S-2, S-B1 | F-2 | 10.2 |
| R-1 N/A needs rationale, audited | S-4, S-16 | F-2, F-8 | Customer-visible (OQ-D2) |
| Goal 2 / R-2 register seeded from taxonomy (D-1) | S-14, S-5 | F-1 step 5, F-3 | Taxonomy is data with source and licence |
| R-2 / OQ3 handling stages, last tested | S-5, S-6, S-B3 | F-3 | 7.1 |
| R-2 links to requirements, owner, last reviewed, evidence | S-6, S-4 | F-3 | Links don't roll up; owner hidden from customer |
| Goal 3 / R-3 event type required | S-8, S-8a, S-12 | F-4a, F-4e, F-4c | |
| R-3 awareness time with zone, stored UTC | S-8, S-8a, S-11 | F-4a, F-4e, F-4b | 11.1 |
| R-3 deadline computation, both final-report rules | S-8, S-9, S-1 | F-4 | 8.1; calendar month per OQ-D10 |
| R-3 UTC + local, countdown, five states | S-1, S-7, S-9 | F-4 | 10.4 |
| R-3 record ENISA filing times, tool doesn't file | S-9 | F-4 | Copy 15.2 |
| R-3 "users informed" (Art. 14(8)) | S-9, S-10 | F-5 | Per deployment (deviation 1); step-up (OQ-D6) |
| R-3 awareness edit: reason, previous value, visible recompute | S-11, S-16 | F-4b | |
| R-3 link to version and deployments | S-8, S-9 | F-4a | Added by responder for admin-started events |
| R-4 / OQ1 customer read-only, own deployment | S-B1–B6 | F-6 | 9.2, 9.3 |
| R-4 release only after users informed | S-10, S-B4 | F-5 | |
| OQ2 admins: states and counts; responders: details | S-1, S-7, S-8a, S-16 masking | F-4, F-4e | 2.3; role checked per request |
| OQ-D1 customer never sees clocks | S-B1–B6 | F-6 | 9.2 |
| OQ-D2 customer-visible content | S-4, S-6, S-B2, S-B3, S-B6 | F-6 | 9.2 |
| OQ-D3 status per version | S-3, S-5, S-14 | F-1, F-2, F-3 | 11.5 |
| OQ-D4 any admin starts a clock | S-8a, S-1, S-7 | F-4e | 8.3a |
| OQ-D5 vendor grants roles, invites customers | S-14 | F-1 steps 6, 8 | 5.1; customer IdP open |
| OQ-D6 timeouts, step-up | S-0, S-10 | F-5 | 11.6 |
| OQ-D7 close states, linked events | S-12, S-13 | F-4c | Pending engineering review |
| OQ-D8 drills, events not in CSV | S-7, S-8, S-8a, S-15 | F-4d, F-7 | Pending engineering review |
| OQ-D9 vendor sees customer activity, anonymization | S-B0, S-B7, S-16, S-B6 | F-9 | 9.6 |
| OQ-D10 calendar month | S-9 | F-4 | 11.1 |
| R-X1 data-driven sets, categories, taxonomies | S-14, S-3, S-5 | F-1 | Disabled unsupported categories; "customer" wording |
| Scope: manual entry and CSV | S-4, S-6, S-8, S-8a, S-15 | F-7 | |
| NFR-1 SSO + MFA, RBAC | S-0, 2.3, 5.1 | F-1 | Customer sign-in method open (OQ-D5) |
| NFR-2 tenant isolation | S-B*, 11.3 | F-6 | Non-revealing not-found and empty states |
| NFR-3 audit trail, incl. views, exportable | S-16, S-17 | F-8 | Real actor always stored (9.6.5) |
| NFR-4 time handling, DST, calendar month | S-8, S-8a, S-9, S-11 | F-4 | 11.1 |
| NFR-5 minimal personal data | 9.2, 9.6 | F-9 | Owner names hidden; customer activity minimised |
| NFR-6 availability | S-1 error and sync states | – | UI shows sync status |
| NFR-7 our own posture | – | – | Not a UI item; OQ-D12 relevant |
| NFR-8 notice on every screen and export | S-1 footer, S-B*, S-B6, S-17 | All | 15.1 |
| Non-goal: alerts | – | – | Strip, tab title and "does not notify" copy are in-app only |
| Non-goal: drafting and filing | S-9 copy | – | |
| P1 activation | S-3 summary | F-2 | |
| P2 AI-risk coverage | S-5 summary | F-3 | |
| P3 clock correctness | S-8 preview, 11.1 test dates | F-4 | |
| P4 drills | 8.8 | F-4d | Pending engineering review |
| P5 weekly active admins | S-16 | F-8 | |
| P6 bank written view | S-B5, S-B6, S-B7 | F-6, F-9 | Export designed for legal review |
| P7, P8 | – | – | No UI |

---

## 20. Risks the design does not remove

- **Nobody opens the dashboard.** The clock strip and tab title only work when someone looks. OQ-D4 helps (whoever hears first can start the clock), but the assigned responder still isn't notified. A 24h deadline can pass at a weekend with every tab closed. **Recommendation:** the pilot agreement names an on-call owner and a check cadence, and the P4 drill includes one out-of-hours run and one admin-started clock. This is a pilot-operations measure, not a UI feature.
- **A neutral palette still invites a verdict reading.** A legal reader may treat "evidence attached for 35 of 35" as a claim. The "About this information" page and NFR-8 notice are the mitigation; their wording is the legal team's call (D-4).
- **Awareness time is self-declared.** Every deadline is only as good as that one field.
- **Organisation-only activity is not anonymous to the vendor in a two-person team.** The copy avoids "anonymous" for this reason (9.6.6).

---

## 21. Open questions

### 21.1 Still needing a CPO decision before `/plan`

- **OQ-D5 (remaining part). How do customer admins sign in?** My reading: for the pilot, vendor-managed invitations, with sign-in through our hosted identity service and enforced MFA (passkey or authenticator app). Federation with the customer's own IdP is a later option. Please confirm or correct. Related: should only designated vendor **access managers** (not every vendor admin) grant the responder role and invite customers? *Proposed: access managers only.*
- **OQ-D9 (details).** Confirm the rules in 9.6:
  - organisation-wide setting, changeable by any customer admin;
  - a first-run choice, with "organisation only" applying until someone chooses;
  - no stable pseudonyms;
  - anonymizing applies retroactively in the vendor's view, de-anonymizing applies forward only;
  - the export cover follows the setting;
  - the vendor sees first daily sign-in, incident views and exports, but not page-by-page browsing.
- **Deviations 1, 4, 5, 7, 9–12 and 15 (section 18).** Confirm as a batch or name any to drop.

### 21.2 For engineering review at `/plan` (CPO asked to check with the engineer)

- **OQ-D7.** Event close states ("reporting complete", "determined not reportable with rationale") and linked events (8.6, 8.7).
- **OQ-D8.** Drill mode (8.8) and excluding Art. 14 events from CSV import (12.1).

### 21.3 For legal (D-4), before the bank sees any export

- The NFR-8 notice, the "What this is not" text, and "About this information" sections 1, 4 and 6.
- The calendar-month interim rule (OQ-D10).
- Lawful basis and retention period for customer activity records, and whether "organisation only" is presented accurately (9.6.6).
- A documented process for investigating misuse of a customer account under "organisation only".

### 21.4 Can wait until after `/plan`

- **OQ-D11.** Tab-title countdown acceptable as in-app display under "no alerts"?
- **OQ-D12.** Our own support staff's access to tenant data. *Proposed: none; screen-share support only.* Will matter to the bank's supplier review (NFR-7).
- **OQ-D13.** Delivery-model field in product setup.
- **OQ-D14.** Review-by dates (no default proposed) and keeping "last reviewed" alongside "last tested".
- **Reassign responder** by any vendor admin (8.3a). *Proposed: yes.*

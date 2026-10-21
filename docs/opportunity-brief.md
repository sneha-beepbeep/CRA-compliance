# Opportunity Brief: CRA and AI Act security tracking for credit-scoring software manufacturers

**Stage:** `/kickoff` (stage 2), revision 3, 2026-10-21.
**Source:** the fresh `/ceo-review` (2026-10-21), verdict **Pursue with caveats**. The earlier "Do not pursue" section is context only.
**Status:** revised after two rounds of CPO gate feedback. Not yet approved.
**Hard gate:** still open. Vendor validation (section 7) must be done before `/prd`.

## 1. The idea and the MVP

The product is a tool that **supports** CRA compliance. It never ensures or certifies it. The user is a software manufacturer building high-risk AI systems for creditworthiness assessment (AI Act Annex III 5(b)), for example Taktile or Scienaptic.

**The MVP is a dashboard showing compliance status and relevant deadlines** (CPO decision). It has three areas:

1. **Requirements status.** Progress against the CRA essential requirements (Art. 13 with Annex I) and AI Act Art. 15. CRA Art. 12 links the two. Recital 51 is context only.
2. **AI-specific risk status.** An internal register, with explanations, of risks such as data poisoning, adversarial or evasion attacks and model manipulation. These are the attack classes named in AI Act Art. 15(5).
3. **Art. 14 deadlines.** For each actively exploited vulnerability or severe incident, the dashboard shows three deadlines:
   - the **24h early warning**;
   - the 72h notification;
   - the final report: 14 days after a fix for a vulnerability, or one month after the notification for a severe incident.

**Out of MVP scope:**
- submitting to ENISA's Single Reporting Platform;
- drafting notifications;
- alerts (candidate for v2);
- any "compliant" verdict.

**Who can see it:** every user with admin access to the vendor's AI credit-scoring product (CPO decision). The open questions below cover what "admin" means here.

**Liability and inputs:**
- The dashboard reflects only data the manufacturer enters or connects.
- Statuses describe that data, for example "evidence attached for 9 of 13 requirements" or "early warning overdue". They are never legal conclusions. The words "compliant" and "non-compliant" are never used.
- Deadlines are calculated from the awareness time the manufacturer enters. If that time is wrong, every deadline is wrong.
- The manufacturer decides, files and signs.
- Inputs are not yet decided and will be set at `/prd`. Candidates: SBOM, vulnerability feeds, model and pipeline telemetry, risk documentation.

## 2. Problem and who has it

**User:** security, compliance or product leads at credit-scoring and decisioning vendors selling into the EU. **None has been interviewed yet.**

**Hypothesis:**
- Since 11 Sep 2026, these vendors must meet the Art. 14 reporting clock.
- From 11 Dec 2027, all CRA essential requirements apply.
- AI-specific attack classes don't fit their existing vulnerability tooling.

**Evidence so far, and its limits:**
- The IT and Product departments of mBank, DKB and Sächsische Aufbaubank (no titles given) report two failures: an in-house build, and a white-label tool that has not been named.
- The banks are the vendors' **customers, not the user**.
- The banks' 72h duty is most likely DORA or GDPR, not the CRA. This is not confirmed.
- The thesis "banks demand it in procurement" is untested.
- **Nobody has given a price or budget signal.**

## 3. Why now

- CRA Art. 14 has applied since **11 Sep 2026**, and the Single Reporting Platform went live that day ([Crowell](https://www.crowell.com/en/insights/client-alerts/its-live-the-cyber-resilience-act-reporting-is-mandatory-as-of-today-11-september-2026)).
- The full CRA requirements apply from **11 Dec 2027**.
- The Digital Omnibus deal (7 May 2026) moves stand-alone Annex III obligations to **2 Dec 2027** ([Gibson Dunn](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/)). I could not confirm publication in the Official Journal, so urgency should rest on the CRA.

## 4. Risks

### 4a. Does the CRA reach cloud-delivered decisioning?

Whether remote processing is essential to the service is not the CRA test. The CRA covers remote processing only as part of a *product with digital elements* that has been placed on the market:

- **Art. 3(1):** a product with digital elements is "a software or hardware product **and its** remote data processing solutions".
- **Art. 3(2):** remote processing counts only if two things hold. It is designed and developed by or under the manufacturer's responsibility. And without it, *the product with digital elements* could not perform one of its functions.
- **Recital 11:** it is covered only "in so far as it is necessary for a product with digital elements to perform its functions". The recital's example is a mobile app calling the manufacturer's API.
- **Recital 12:** cloud services that support no product fall under NIS2 instead.
- **Commission guidance (27 Jul 2026):**
  - It sets a three-part test: processing at a distance, functional dependency, and manufacturer responsibility.
  - Software the user merely accesses through a browser is not, on that basis, a product with digital elements.
  - The guidance is non-binding, and formal adoption is pending ([summary](https://www.cyberresilienceact.eu/commission-guidance.html), [HLC](https://www.hlc.com/en/publications/eu-cyber-resilience-act-european-commission-publishes-final-cra-guidance), [Commission](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-new-guidance-support-timely-cyber-resilience-act-implementation)).
- **External legal advice (CPO's lawyer, oral and unpublished, 2026-10-21):** hosted APIs are in scope where the vendor provides a bank-side software product and the API is functionally necessary for it. This fits Art. 3(2) and Recital 11.

| Vendor delivery model | CRA position |
|---|---|
| Installed software, on-premise engine, SDK, library, plugin or app shipped to the bank | **In scope** as a product with digital elements. The vendor's cloud behind it is remote data processing. |
| Hosted API **plus** bank-side software from the same vendor, where the API is functionally necessary to that software | **In scope** (CPO's legal advice; consistent with Art. 3(2) and Recital 11). |
| Browser-only platform, or hosted API with **no** vendor software on the bank side | **Probably out of scope** (NIS2 territory). It stays relevant only as the check on the "all vendors ship software" assumption below. |

**Decision (CPO, 2026-10-21): no fallback for cloud-only vendors is needed.** The CPO states that all target vendors ship software.

This is the **CPO's assertion. It has not been verified.** My earlier research suggested Taktile runs only in its own AWS cloud ([rfp.wiki](https://www.rfp.wiki/vendors/taktile)). That came from a third-party listing and was never confirmed. It is now to be checked against the CPO's position in the vendor conversations (step 2). The "ships no software" kill signal stays as the test of this assumption.

### 4b. Other risks

| Risk | Status |
|---|---|
| **Annex III 5(b) is narrow.** It covers natural persons only, excludes fraud detection, and does not cover SME or B2B lending. | The niche shrinks. |
| **Competitors.** Modulos ships a CRA framework for AI-enabled products that includes Art. 14 readiness ([docs](https://docs.modulos.ai/frameworks/cra/operationalizing-in-modulos)). It shows no per-incident clocks and no coverage of poisoning or adversarial attacks. Finite State, FOSSA and ArmorCode cover Art. 14 but not AI-specific risks. I found no CRA content from Saidot, trail, Credo AI or Holistic AI. | The gap has not been verified by demos. The failed white-label tool is still **unnamed**. |
| **A 24h deadline can pass unnoticed** on a dashboard nobody is watching. | **Accepted for the MVP** (no alerts). Step 2 tests it: ask each vendor who would watch the dashboard out of hours, and whether they would pay for alerts. |
| **A status display implies more than a draft.** A green tile can be read as "compliant". | Covered by the status-wording rules in section 1. |
| **A wider audience exposes unreported vulnerabilities.** Admin-wide visibility shows actively exploited, still-unreported issues to more people. | See open questions 1 and 2. |
| **IP.** The AI-risk taxonomy is extracted from a third-party book. | Rights are not confirmed. It will not ship until they are. |
| **Pre-built schema.** `cra_deadline_check` fits MVP area 3 but lacks the one-month final report for severe incidents. `security_changelog` has **no role**. | Both remain **unapproved scope**, to be confirmed or revised at `/prd`. |

## 5. Rough size of prize (my estimate, unverified)

- I assume about 50 to 150 credit-scoring vendors sell into the EU.
- Assume 20 to 40% are in scope and serve natural-person credit: **about 10 to 60 vendors**. If the CPO's "all ship software" holds, the upper end is more likely.
- At an assumed €15k to €40k annual contract value, that is **€0.2m to €2.4m ARR at full penetration**. It is only viable as a wedge.

**Decision (CPO):** credit scoring stays the beachhead. Build so the product can extend to other Annex III manufacturers if scale demands: employment (4), insurance pricing (5(c)), education (3). Regulation mappings and risk lists must not be hard-coded to 5(b).

## 6. Kill signals (90 days, to 2027-01-19)

Any one of these triggers `/checkpoint`:

- Fewer than 3 vendors will pilot or discuss price.
- Most target vendors ship no software to banks, which would contradict the CPO's assertion.
- An existing tool already combines AI-specific risk tracking with CRA Art. 14 tracking for this segment.
- Vendors say banks don't require this in procurement.

## 7. Validation steps the CPO must complete before `/prd` (hard gate)

1. Hold **3 to 5 vendor conversations**, at least one with a **real pilot candidate with a price or budget signal**. If this fails, run `/checkpoint`.
2. For each vendor, record:
   - **what software they ship to banks, and whether their hosted API is functionally necessary to it.** This confirms the CPO's assertion, and Taktile is the case to check first.
   - whether they serve natural-person credit;
   - their current Art. 14 process;
   - **who would watch the dashboard out of hours, and whether they'd pay for alerts** (the v2 signal);
   - **who counts as an "admin" of their product, and whether that includes bank-side admins;**
   - whether banks require this in procurement;
   - willingness to pay.
3. Ask one bank for the name of the failed white-label tool, why it failed, and which regulation sets its 72h deadline.
4. Get a Modulos demo, or a written answer, on per-incident clocks and AI-risk tracking.
5. Get IP clearance for the book-derived content. If possible, get the lawyer's hosted-API advice in writing so the PRD can cite it.

## Decisions recorded at this gate (CPO, 2026-10-21)

- **Scope:** credit scoring is the beachhead, with an architecture that can extend across Annex III.
- **MVP:** a status and deadline dashboard. Submission to ENISA and notification drafting are out of scope.
- **Alerts:** out of MVP scope. A v2 candidate, depending on vendor demand. The 24h risk is accepted for the MVP.
- **Audience:** every user with admin access to the vendor's AI credit-scoring product.
- **Cloud-only fallback:** not needed, because the CPO states all target vendors ship software. To be confirmed in step 2.
- **Hosted APIs:** in scope when paired with bank-side software, per the CPO's external legal advice.

## Open questions for the CPO

1. **Does "admin access" include bank-side admins of the deployed product?** If it does, a bank could see actively exploited vulnerabilities before the vendor has reported them or has a fix. In a shared deployment, it could also see other banks' incidents. Should a bank admin see only incidents affecting its own deployment, and only after the early warning has been filed?
2. **Confidentiality inside the vendor.** Unreported exploited vulnerabilities are highly sensitive. Should the deadline area (MVP area 3) have narrower visibility than requirements status? Or should every admin see everything, with that recorded as an accepted risk?
3. **What counts as "status" for AI-specific risks?** Requirements status can be shown as evidence attached against Annex I. AI risks such as poisoning have no equivalent checklist. The PRD needs a definition that doesn't imply a compliance verdict.

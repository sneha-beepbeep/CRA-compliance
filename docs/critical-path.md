# Critical path to the pilot

**Status:** the CPO's checklist, 2026-10-21. The plan (`docs/technical-plan.md`) was approved with C4 (2 engineers) and C6 (no real incident data until the pentest passes) confirmed. The pilot starts on **2026-11-15** with drills only. Real incident data follows the pentest (around 2026-12-07). Bank access follows the pentest and legal sign-off (around 2026-12-11).

| # | Item | Owner | Due | Blocks |
|---|---|---|---|---|
| 1 | Requirement content (~35 rows) | PM drafts, legal reviews | **2026-10-30** | The build (catalog loader, phase 0) |
| 2 | Each vendor's delivery model | CPO | ~2026-11-25 | Pentest scope; tests the "all vendors ship software" assumption |
| 3 | Licence checks on the taxonomy seeds | CPO | 2026-11-13 | AI-risk seeding on day 1 |
| 4 | Legal sign-off | CPO and lawyer | ~2026-12-04 | Bank access, exports, and the bank's €15k |
| 5 | IP clearance on the book content | CPO | Not blocking | Only needed to reuse `regtech_cyber.db` |
| 6 | Pilot-agreement clauses (C6 and on-call) | CPO and lawyer | 2026-11-15 | Pilot start |

---

## 1. Requirement content: about 35 rows, due 2026-10-30

Each row needs:
- a stable ID;
- the set it belongs to;
- the exact citation;
- a short title (under about 10 words, neutral, never "compliant");
- a link to the official text;
- a `pending_oj_check` flag.

1. Download the Official Journal texts from EUR-Lex. Use these, not consolidated summaries.
   - CRA: **Regulation (EU) 2024/2847**.
   - AI Act: **Regulation (EU) 2024/1689**.
2. **CRA Annex I, Part I** (product properties): one row for point (1), plus one row per lettered item in point (2).
3. **CRA Annex I, Part II** (vulnerability handling): one row per numbered point.
4. **AI Act Art. 15:** one row per paragraph. Paragraph 5 may be split by threat: data poisoning, model poisoning, adversarial examples, confidentiality attacks, model flaws.
5. **Context-only rows, with no status:**
   - CRA Art. 12, which presumes conformity for high-risk AI;
   - Recital 51.
6. Check each citation against the OJ text, and flag any row you're unsure of.
7. Lawyer spot-check of the titles, about 1 hour. These titles appear in front of the bank.

## 2. Each vendor's delivery model

1. Email your contact at each of the 3 vendors with these questions:
   - What software do you install or ship to clients: an SDK, connector, plugin, on-premise engine or app?
   - Does that software stop working without your hosted service or API?
   - Which clients use your system to score **individuals'** creditworthiness, as opposed to businesses, fraud or AML?
   - Who would be the incident responder for the pilot, and is there out-of-hours cover?
   - Who should be dashboard admins, on your side and on the bank's?
2. Record the answers in a table, one row per vendor.
3. If a vendor answers "nothing, it's browser-only", flag it. That vendor may be outside the CRA, which is the brief's kill signal.

## 3. Licence checks on the taxonomy seeds

1. **MITRE ATLAS:**
   - read the LICENSE file in its GitHub repository (`mitre-atlas`);
   - confirm commercial use and redistribution are allowed;
   - note the attribution wording.
2. **NIST AI 100-2** (Adversarial Machine Learning taxonomy):
   - US government works are generally not copyrighted in the US, but check the publication's front matter for any notice;
   - note the attribution wording.
3. Keep a short note per taxonomy, with links and the attribution text. Engineering marks each one `cleared` in the data.
4. **OWASP** is on hold (CC BY-SA) until counsel advises.

## 4. Legal sign-off

1. Book the lawyer for a review in early December. Send them a single pack:
   - the disclaimer, the "About this information" text and the "What this is not" wording from `docs/design-spec.md`;
   - a sample customer export, once engineering can produce one.
2. Ask for yes/no answers to these questions:
   1. Is the disclaimer wording adequate? Does any copy imply a determination of compliance?
   2. **Month rule:** does "one month" mean the same calendar day next month, clamped to month end, in UTC?
   3. **C7:** when a fix exists before the vendor became aware of exploitation, how is the 14-day final report counted?
   4. Are the Art. 14 deadlines and the Art. 14(8) duty to inform users correct as stated in the PRD, when checked against the OJ text?
   5. Will you confirm in writing your advice that a hosted API is in scope when paired with software the vendor ships to the bank?
   6. Is the PRD right that credit scoring cannot rely on the Art. 6(3) exemption from high-risk status?
3. Get the sign-off in writing. Wording changes are configuration, so no release is needed.
4. Share the signed-off export with the bank's legal team early. The bank's €15k depends on its legal review.

## 5. IP clearance on the book content

This doesn't block the pilot, because the product does not load `regtech_cyber.db`.

1. Identify the publisher and its permissions or rights contact.
2. Ask for a licence for commercial use of a structured summary of Chapters 1, 2 and 11 (risks, mitigations and barriers) in a paid SaaS product, with attribution.
3. If they decline, the public taxonomies replace it. No product change is needed.

## 6. Pilot-agreement clauses

**C6 clause.** Draft wording for the lawyer to adapt:

> "During the period from the Pilot Start Date until [Provider] confirms in writing that the independent penetration test has been completed and all critical and high findings remediated (expected on or around 7 December 2026), the Customer shall use the Service for simulated ('drill') events only and shall not enter information concerning actual vulnerabilities or incidents. The Customer shall continue to operate its existing processes for meeting its obligations under Article 14 of Regulation (EU) 2024/2847 throughout the Pilot. The Service supports the Customer's own compliance activities and does not determine compliance."

**On-call clause.** Name the vendor's out-of-hours on-call owner. The MVP has no alerts.

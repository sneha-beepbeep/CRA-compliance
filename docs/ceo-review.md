# CEO Review

Running log. The original `/ceo-review` verdict is below. Any later `/checkpoint`
entries are appended underneath, dated and tagged by stage, and never replace
earlier entries.

---

## /ceo-review: stage 1 (2026-10-20 to 2026-10-21)

### Raw idea as given

The CPO first ran `/ceo-review` with no arguments. The idea then went through
four framings during the session. The final restatement, which the CPO
described as replacing the earlier blended ideas, is the one reviewed:

> "A database security indicator indicating compliance with the CRA for
> European B2B software companies handling sensitive data. An example domain
> would be healthcare. Pilot customer could be a healthcare startup booking lab
> tests for patients. Customer service and other actors would access the
> database frequently. Therefore there needs to be an easy indicator to
> indicate security of database and show potential CRA breaches to all who
> access it."

How the framing developed, for the record:

| Round | Framing | What happened |
|---|---|---|
| 0 | Draft PRD one-liner: "Continuous Hardening as a Service for mid-market EU companies newly in scope for CRA/NIS2/DORA reporting within the context of publicly provable data-infrastructure security" | Sent back. It named three regulatory populations, no buyer title, and gave a value proposition where the domain should be. |
| 1 | "A managed, staged and vulnerability-disclosure service and reference guide for CISOs at mid-market EU software companies newly subject to CRA Article 14 reporting and implementing AI systems" | Sent back. It had no domain clause, "bug bounty" was missing, and "service + guide" described two products. |
| 2 | Answers only: `regtech_cyber.db` is the guide and will not be hardened; the AI Act widens the problem; the commercial pains are (a) meeting Art. 14 deadlines and (b) finding AI-specific flaws | Dropped the "hardened DB as proof" and "public changelog = CRA compliance" premises. Still no restated sentence. |
| 3 | "A database security indicator which uses existing change logs to indicate security vulnerabilities and compliance with CRA for government/regulated actors handling sensitive personal information who have had data leaks recently" | A different product and a different user. The CRA largely does not apply to that user. |
| 4 | Final restatement (quoted above) | Reviewed. |

The final restatement still has no explicit "within the context of
<domain>" clause. Healthcare is offered only as an example. I reviewed it
anyway, and treated "B2B health-software, EU product-cybersecurity compliance"
as the domain, because the session had run four rounds and the CPO was told
this one would go to a verdict.

### Key questions asked

1. What does the flagship case study prove? Why would hardening a
   book-derived, public-reference SQLite file convince a buyer about their own
   production systems?
2. Is a public security changelog really the same thing as CRA Art. 14
   reporting? Art. 14 covers actively exploited vulnerabilities, reported
   confidentially to the CSIRT/ENISA single reporting platform within 24h
   and 72h of awareness. Which pain does the customer pay for?
3. Why would a buyer use us instead of going direct to Intigriti or YesWeHack
   (managed VDP and bug bounty), DAM/SIEM tools, security-rating services, or
   free AI-risk frameworks (OWASP Top 10 for LLM Applications, MITRE ATLAS,
   NIST AI RMF)?
4. What evidence of demand is there: named prospects, willingness to pay? Who
   delivers around the clock against a 24h clock, and who carries the
   liability if something leaks?
5. Does the CRA actually apply to the stated user? Covered in rounds 3 and 4:
   the CRA binds manufacturers of products with digital elements. Data
   controllers answer to GDPR and, often, NIS2.
6. For the indicator: what does it read, what does it output, who looks at
   it, and what do they do as a result?

### CPO's answers (summarised)

- **Q1:** `regtech_cyber.db` is now the reference guide (book-derived AI-risk
  content), not a case study, and will not be hardened. This drops the
  "Provably Secure" premise.
- **Q2:** The AI angle makes the regulatory problem bigger, not smaller. The
  pains named were Art. 14 deadline compliance and AI-specific flaw-finding.
  The public trust signal was dropped. In the final framing the AI angle,
  the guide and the bug bounty are no longer mentioned.
- **Q3 (differentiation):** Not answered in any round.
- **Q4 (demand, delivery, liability):** Not answered. The final framing
  offers a hypothetical pilot ("could be a healthcare startup booking lab
  tests"), not a named prospect or a statement of willingness to pay.
- **Q5 (regulatory fit):** The final framing moves the user back to B2B
  software companies, which are CRA manufacturers. That partly addresses the
  concern.
- **Q6 (the indicator):** The audience is customer service and other internal
  staff who access the database. The indicator should show database security
  and "potential CRA breaches". The inputs, the scoring logic and the action
  a viewer takes were not defined.

### Verdict: **Do not pursue (as currently framed)**

### Reasoning

1. **The idea has not stabilised.** There were four materially different
   products in four rounds: hardening service, managed VDP plus guide, breach
   indicator for regulated bodies, and internal CRA database indicator. The
   CPO candidly said they were blending ideas. A PM handed `/kickoff` now
   would be choosing the product, which is not the PM's job, and the
   downstream work would rest on whichever framing happened to be last.

2. **The final framing is built on a category error about the CRA.**
   - The CRA regulates *products with digital elements* and their
     manufacturers' vulnerability-handling and reporting duties. It does not
     regulate databases. "CRA breaches" is not a CRA concept. Personal-data
     breaches fall under GDPR (Art. 33/34), and incident reporting for
     in-scope entities falls under NIS2.
   - The CPO's own example pilot, a hosted lab-test booking service, is
     likely SaaS. Under the CRA, pure SaaS is largely out of scope, except
     for remote data processing that is integral to a product, and is covered
     instead by NIS2. Health-sector software may also fall under the MDR
     instead.
   - So the indicator could show "CRA compliant" or "CRA breach" for a system
     the CRA doesn't govern. That is worse than useless in a regulated
     setting.

3. **The indicator has no clear user decision behind it.** Customer-service
   staff can't fix a vulnerability, and they shouldn't decide on regulatory
   reporting.
   - Showing live vulnerability and compliance state to everyone with
     database access widens exposure of exactly the information an attacker
     wants.
   - The people who *can* act (engineering, security, the DPO) already get
     this from vulnerability-management, DAM, SIEM and compliance-automation
     tools, several of which are adding CRA mappings.

4. **No differentiation and no demand evidence, across all four framings.**
   - Q3 and Q4 went unanswered every round.
   - There is no named prospect, no buyer conversation and no
     willingness-to-pay signal.
   - There is no size-of-prize estimate, which the draft PRD also left TBD
     and `/kickoff` requires.

5. **What is genuinely strong, stated plainly.**
   - The CRA reporting obligations that apply from 11 September 2026 are real
     and new for EU software manufacturers. Mid-market makers without
     security headcount plausibly feel this.
   - The CPO has relevant domain material: the AI-risk knowledge base, and a
     `finding` / `cra_deadline_check` model that already encodes the
     Art. 14 clocks correctly.
   - The opportunity space is not the problem. The problem is that no single,
     regulation-correct, buyer-validated bet has been put forward yet.

### What would have to become true to revisit

A fresh `/ceo-review` would be worth running when all of the following hold:

1. **One idea in the required form:** "<idea> for <user> within the context
   of <domain>", with an explicit domain clause. The CPO writes it, and it
   says what has been dropped from earlier framings.
2. **A regulation-correct obligation.** The target user is confirmed to be in
   scope of the regulation the product claims to address. For example: a
   manufacturer of an on-premise or embedded product with digital elements
   for the CRA, or a hosted service handling health data for GDPR/NIS2. The
   product's language matches that regulation.
3. **A defined indicator, or other core output.** Specify:
   - what it reads;
   - what it outputs;
   - who looks at it;
   - what decision they make because of it.
4. **Evidence of demand.** At least 3 to 5 conversations with the named buyer
   title in the target segment. At least one should be a real (not
   hypothetical) pilot candidate, with some signal of willingness to pay.
5. **A differentiation answer.** Explain specifically why this beats
   compliance-automation tools, DAM/SIEM and managed VDP platforms for that
   buyer.

The cheapest coherent candidate visible from this session is an internal
CRA Art. 14 vulnerability-handling and deadline tracker for EU software
manufacturers. It reuses the existing `finding` and `cra_deadline_check`
model. It would still need items 2 to 5 before it is worth a stage-1
approval. This is noted as a lead, not a recommendation.

---

## /ceo-review (fresh review): stage 1 (2026-10-21)

The CPO came back on the revisit route set out above. This is a new review
of a new idea, judged on its own merits and against the five revisit
conditions. The earlier verdict stands as the record of the framings it
covered.

### Raw idea as given

Final one-liner, verbatim:

> "A CRM compliance tool for sofware manfucaturers building high-risk AI
> systems as per Art 51 of the CRA in the domain of creditworthiness checks
> (e.g. Taktile, Scienaptic)."

The CPO has confirmed two corrections:
- "CRM" means **CRA**.
- "Art 51" means **Recital 51** of the CRA preamble, which deals with how the
  CRA applies to high-risk AI systems. Recitals aren't binding. The operative
  provision is CRA Art. 12.

As corrected, the idea reads: *a CRA compliance tool for software
manufacturers building high-risk AI systems, in the domain of
creditworthiness assessment.*

Stated functions:
1. Ensure the product meets the CRA essential cybersecurity requirements and
   AI Act Art. 15.
2. Internal tracking and explainability for AI-specific risks, such as data
   poisoning and adversarial attacks.
3. A reporting function that enables vulnerability and incident notification
   within 72h under CRA Art. 14.

An earlier round of this review used "CRM compliance checker" and named the
banks mBank, DKB and Sächsische Aufbaubank as demand evidence.

### Key questions asked

1. Is it "CRM" or "CRA", and is the citation correct? Creditworthiness is
   high-risk under AI Act Annex III 5(b). The CRA's link to high-risk AI is
   Art. 12.
2. Are the banks the user, or the user's customers? Banks deploy credit
   scoring, or build it in-house. They are not CRA manufacturers.
3. What exactly did the banks say: titles, problem, budget, pilot?
4. What does the tool read and output, who acts on it, and who carries the
   liability for a wrong "compliant"?
5. Why this rather than Europe-based AI-governance tools (Modulos, Saidot,
   trail), US players (Credo AI, Holistic AI), or the Big Four?
6. Which 72h deadline and which authority did the banks name: DORA, GDPR or
   CRA? Their own 72h duty is most likely DORA or GDPR, not CRA Art. 14.
7. Is the bet (A) banks as the user, under DORA and AI Act deployer duties, or
   (B) credit-scoring vendors as the user, under the CRA?
8. Is there a payment signal? Which white-label product failed, and why?
9. What result in 90 days would show this was a mistake?

### CPO's answers (summarised)

- **Q1:** CRA, and Recital 51.
- **Q2 / Q3:** The CPO spoke to the IT and Product departments at mBank, DKB
  and Sächsische Aufbaubank. No titles were given. The banks had tried to
  build their own tools and had tried a white-label product, and both
  failed. The pain they described: no capacity to track vulnerabilities after
  implementation and to report within 72h, and they said competitor products
  lack this feature.
- **Q7:** The CPO implicitly chose **(B)**: the user is credit-scoring
  software vendors, with Taktile and Scienaptic as examples. These are
  examples, not conversations. No vendor has been spoken to.
- **Q4:** Partly answered through the three stated functions. Inputs and
  liability were not addressed.
- **Q5, Q6, Q8, Q9:** Not answered. There is no payment signal, the
  white-label product isn't named, and the authority behind the banks' 72h
  isn't confirmed.

### Verdict: **Pursue with caveats**

### Reasoning

**Against the revisit conditions:**

| Condition | Status |
|---|---|
| 1. One idea in the required form | **Met, with corrections.** There is a single idea, user and domain. The wording errors ("CRM", "Art 51") are typos the CPO has corrected, not changes of direction. |
| 2. Regulation-correct obligation | **Met in principle.** Credit-scoring vendors are AI Act providers of an Annex III 5(b) high-risk system. Where they place a product with digital elements on the EU market, they are CRA manufacturers, and CRA Art. 12 links the two regimes. Open risk: SaaS delivery (caveat 2). |
| 3. Defined core output | **Partly met.** Three functions are named. Inputs, outputs and the liability boundary are not. |
| 4. Evidence of demand | **Partly met, from the wrong side of the market.** Three named banks report a failed build and a failed buy, which is a strong signal of pain. But the banks are the vendors' customers. No vendor, the actual user, has been spoken to, and there is no payment signal. |
| 5. Differentiation | **Asserted, not shown.** "Competitors don't integrate this" is plausible. The intersection of AI-specific risk tracking and CRA vulnerability reporting does look under-served: AI-governance tools focus on AI Act documentation, and CRA tooling isn't AI-specific. It has not been verified. |

**Why "Pursue with caveats" and not "Do not pursue":**

- The idea is now stable, specific and coherent with the regulations.
- The regulatory intersection it targets is real and new:
  - the CRA Art. 12 and AI Act Art. 15 overlap;
  - Art. 14 reporting, in force since 11 September 2026;
  - the essential requirements, due 11 December 2027.
- The banks' failed build and failed buy is credible pain sitting downstream
  of the target user. That makes a "vendors will pay because their bank
  customers demand it" thesis worth testing.
- The CPO already holds reusable assets:
  - the `finding` / `cra_deadline_check` model, for function 3;
  - the AI-risk taxonomy, for function 2.

**Why not plain "Pursue":** the user hasn't been validated at all. The one
piece of real evidence comes from a different party, and condition 4 is not
met for the stated user. Without the caveats below, the case would not
clear stage 1.

### Caveats (binding on later stages)

1. **Vendor validation gate before `/prd`.**
   - `/kickoff` must include 3 to 5 conversations with security, compliance
     or product leads at credit-scoring and decisioning vendors selling into
     the EU.
   - At least one must be a real pilot candidate with a price or budget
     signal.
   - If this gate fails, run `/checkpoint` before `/prd`.
2. **CRA scope for SaaS.**
   - Many decisioning vendors deliver as cloud platforms. Pure SaaS is
     largely outside the CRA (NIS2 territory), except for remote data
     processing that is integral to a product with digital elements.
   - The opportunity brief must establish what share of target vendors ship
     in-scope products: on-premise, SDK, embedded, or integral remote
     processing.
   - If most are out of scope, the CRA hook fails for them.
3. **Exact regulatory basis in every artifact.**
   - **CRA:** Art. 12 (high-risk AI), Art. 13 with Annex I (essential
     requirements), Art. 14 (reporting).
   - **AI Act:** Art. 15 and Annex III 5(b).
   - Art. 14 has a **24h early warning** before the 72h notification, plus a
     final report (14 days after a fix for exploited vulnerabilities, one
     month for severe incidents). Function 3 must meet the 24h clock, not
     just the 72h one.
   - Use "CRA", never "CRM". Cite Recital 51 as context only.
   - The application dates for the AI Act's high-risk obligations have been
     in flux (Digital Omnibus). Anchor urgency on CRA Art. 14, which is
     already in force.
4. **"Ensures" becomes "supports".**
   - The tool supports conformity assessment and reporting. It does not
     certify compliance.
   - The PRD must define the liability boundary and what the tool reads.
     Inputs could include SBOM, vulnerability feeds, model and data-pipeline
     telemetry, and risk-management documentation. This is not yet decided.
5. **Differentiation must be verified.**
   - Name the white-label product the banks tried and why it failed.
   - Check the "no competitor integrates this" claim against AI-governance
     tools (Modulos, Saidot, trail, Credo AI, Holistic AI) and CRA
     vulnerability-handling tools.
6. **Size of prize.** The number of credit-scoring vendors selling into the
   EU is a narrow niche. `/kickoff` must size it and name the expansion path,
   for example other Annex III categories.
7. **IP check before reuse.** The AI-risk knowledge base is extracted from a
   third-party book. Confirm rights before its content ships in a commercial
   product.
8. **Pre-built schema.** The `finding` table and the `security_changelog` /
   `cra_deadline_check` views remain unapproved scope.
   - `cra_deadline_check` fits function 3 and should be confirmed or revised
     at `/prd`.
   - `security_changelog` (public disclosure) has no role in this framing.

### What would tell us in 90 days that this was a mistake

Any one of the following should trigger a `/checkpoint`, with Reshape or
Abandon on the table:

- Fewer than 3 vendors will take a pilot or discuss price.
- Most target vendors turn out to be pure SaaS outside CRA scope.
- An existing tool already combines AI-specific risk tracking with CRA
  Art. 14 reporting for this segment.
- Vendors say their bank customers don't actually require this in
  procurement.

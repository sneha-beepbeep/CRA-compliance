<!-- product-dev-pipeline:product-readme
     Instantiated by the Product Manager at /kickoff, rewritten by the Launch
     Coordinator at /ship. Replace every <angle-bracketed> placeholder.
     If placeholders are still here at /ship, that is a bug, not a style choice. -->

# CRA and AI Act Security Tracker (working title)

A planned dashboard for companies whose AI systems score people's creditworthiness. It will show their progress on the security requirements of the EU Cyber Resilience Act (CRA) and the AI Act, track how they handle AI-specific risks, and count down the CRA's reporting deadlines for exploited vulnerabilities and severe incidents.

**Status: in development, specification stage.** Requirements are drafted, but nothing has been built and nothing can be installed or run. A paid pilot with one software vendor and one of its banking clients is being planned.

## Who it's for

Security, compliance and product leads at software vendors whose AI system assesses the creditworthiness of individuals and is sold into the EU. Their customers can be banks, consumer lenders or other firms that credit-score individuals. Everyone with admin access to the vendor's credit-scoring product will be able to see the dashboard. Who sees which incident details is still being decided. A read-only view for the vendor's bank customers, limited to their own deployment, is proposed but not confirmed.

## What it does

Nothing yet. Everything below is **planned**, not built, and may change:

- **Planned:** show each CRA essential requirement (Annex I) and AI Act cybersecurity requirement (Art. 15) with the evidence you have attached, as a count of evidence attached rather than a compliance score.
- **Planned:** keep a register of AI-specific risks, such as data poisoning and adversarial attacks, showing how you have treated each one and when you last tested it.
- **Planned:** for each actively exploited vulnerability or severe incident, show the CRA Art. 14 deadlines: the 24h early warning, the 72h notification and the final report. Each deadline shows its exact time and a countdown.
- **Planned:** a full audit trail of who changed or viewed what.

The dashboard will **support** your compliance work and will only reflect the information you give it. It will not certify that your product is compliant, it will not draft or file reports for you, and it does not replace your own legal judgement.

## Getting started

Not yet runnable. There is nothing to install or try at this stage.

## Limitations

- Nothing is built yet.
- It will not certify compliance. You remain responsible for your own conformity assessment and for submitting reports to the authorities.
- The first version is planned without alerts, so you will need to check the dashboard yourself, including outside office hours, so that you don't miss a 24h deadline.
- Deadlines are calculated from the time you enter for when you became aware of the issue. If that time is wrong, the deadlines will be wrong.
- The first version covers only credit scoring of individuals. It does not cover credit scoring of businesses, fraud detection, or insurance pricing.
- The CRA applies to you if you ship software to your customers, together with any hosted service that software depends on. A purely hosted service with no software on the customer's side may fall outside it. Check your own scope with legal counsel.
- AI Act dates for high-risk systems have recently changed and may still shift.

---

Planning and specification documents live in [`docs/`](docs/). They are written
for the team building this product, not for people using it, and they are not a
substitute for the sections above.

<!-- At /ship, delete the docs/ pointer above: the shipped README is written for
     the end user, and internal artifacts are not part of their path. -->

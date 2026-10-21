<!-- product-dev-pipeline:product-readme
     Instantiated by the Product Manager at /kickoff, rewritten by the Launch
     Coordinator at /ship. Replace every <angle-bracketed> placeholder.
     If placeholders are still here at /ship, that is a bug, not a style choice. -->

# CRA and AI Act Security Tracker (working title)

A planned dashboard for software makers whose AI systems assess people's creditworthiness. It will show where they stand on the security requirements of the EU Cyber Resilience Act (CRA) and the AI Act, list the AI-specific attacks they are tracking, and show which CRA reporting deadlines are open, due or overdue.

**Status: in development, early concept.** Nothing user-facing exists yet, and nothing can be installed or run. The product is still being validated with prospective users and has not been specified. This repository holds only a reference database of AI risks and an unapproved draft data model.

## Who it's for

Security, compliance and product leads at companies that build credit-scoring or credit-decisioning software and sell it into the EU. Their products count as high-risk AI under the EU AI Act and fall under the CRA. The plan is that anyone with admin access to the credit-scoring product can view the dashboard.

## What it does

Nothing yet. Everything below is **planned**, not built, and may change after validation:

- **Planned:** show your progress against the CRA essential cybersecurity requirements and the AI Act's cybersecurity article (Art. 15).
- **Planned:** show the status of the AI-specific risks you track, such as data poisoning and adversarial attacks, with plain explanations.
- **Planned:** for each actively exploited vulnerability or severe incident, show the CRA Art. 14 deadlines: the 24h early warning, the 72h notification and the final report.

The dashboard will **support** your compliance work. It will only reflect the information you give it. It will not certify that your product is compliant, it will not file reports for you, and it does not replace your own legal judgement.

## Getting started

Not yet runnable. There is nothing to install or try at this stage.

## Limitations

- Nothing is built yet.
- It will not certify compliance. You remain responsible for your own conformity assessment and for submitting reports to the authorities.
- The first version is planned without alerts. You will need to check the dashboard yourself, including outside office hours, so a 24h deadline is not missed.
- Deadlines will be calculated from the time you enter for when you became aware of the issue. If that time is wrong, the deadlines will be wrong.
- The CRA applies to you if you ship software to your customers, together with any hosted service that software depends on. A purely hosted service with no software on the customer's side may fall outside it. Check your own scope with legal counsel.
- AI Act dates for high-risk systems have recently changed and may still shift.

---

Planning and specification documents live in [`docs/`](docs/). They are written
for the team building this product, not for people using it, and they are not a
substitute for the sections above.

<!-- At /ship, delete the docs/ pointer above: the shipped README is written for
     the end user, and internal artifacts are not part of their path. -->

# PRD (CPO draft): Provably Secure — Continuous Hardening as a Service

**Status:** CPO-authored draft, reformatted from an earlier chat (written
c. 2026-09-15, "four days" after the CRA reporting clock started). Not yet
through `/ceo-review`, `/kickoff` or `/prd`. Gaps are marked **TBD (CPO)**
rather than filled in. Market claims are as the CPO stated them and have not
been verified.

**`/ceo-review` one-liner:**
> Continuous Hardening as a Service for mid-market EU companies newly in scope
> for CRA/NIS2/DORA reporting within the context of publicly provable
> data-infrastructure security

**Tagline:** "Provably Secure": the database that has to keep proving it's
secure, not just claim it.

## Problem

EU companies handling sensitive data are under growing pressure to
*demonstrate* security, not just assert it:

- **Regulation:** CRA vulnerability-reporting duties started on
  11 September 2026, and NIS2 and DORA add further obligations.
- **Breaches:** high-profile incidents, such as Ceva rippling into ING, Bol,
  Ajax and Steam, keep showing that "we take security seriously" means
  nothing until something tests it.
- **Current alternatives fall short:** static audits and self-reported
  compliance are expensive, go stale fast, and produce no evidence that anyone
  outside the company trusts.

## Proposed solution

A security claim that is **continuously proven, not asserted**, built from:

1. **A staged, legally scoped bug bounty programme:** private pentest, then
   invite-only, then public.
2. **EU-native platforms:** run through Intigriti or YesWeHack. We integrate
   these platforms and don't build our own.
3. **Safe targets:** testing always runs against synthetic-data sandboxes,
   never production data.
4. **CVSS-tiered payouts.**
5. **A live public security changelog:** every finding and every fix is
   published.

**The key insight:** the changelog serves as the marketing asset, and it also
covers most of what the CRA's 24-hour / 72-hour / 14-day disclosure regime
requires a company to be capable of. The marketing asset and the compliance
obligation are the same muscle.

## Business model: who builds and sells it

| Option | Description | Assessment |
|---|---|---|
| A. Security-native DBaaS startup | Build a database-as-a-service with this as its core differentiator | Needs heavy capital and a multi-year infrastructure build |
| **B. Consultancy productized service (preferred, first bet)** | The consultancy sells "Continuous Hardening as a Service" to companies that already have data infrastructure | Faster and cheaper; reuses existing bounty platforms |

Under option B, **our own hardened database is the flagship case study.** It
proves the method on ourselves before we sell it to anyone. This feeds the
**rating-tool pitch**: "we do this to ourselves first" is the credibility
story that pitch needs.

## Goals

1. Give customers a credible, continuously updated, publicly checkable signal
   that their security works.
2. Give customers the vulnerability-disclosure process the CRA (and
   NIS2/DORA) requires, without them having to hire for it.
3. Run bounty programmes safely and within legal scope for customers who lack
   the expertise (or nerve) to run one themselves.
4. Prove the method on our own database first and use it as the flagship case
   study.

## Non-goals

- Building our own bug bounty platform. We integrate Intigriti or YesWeHack.
- Building a security-native DBaaS (option A), at least for now.
- Testing against production or real customer data. Sandboxes use synthetic
  data only.
- Serving large incumbents (Ticketmaster scale) that already run this in-house.
- Serving companies too small to have budget or real stakes.
- **TBD (CPO):** whether we file CRA reports on customers' behalf or only
  build their capability to file them.

## Target users

**Buyer:** mid-market, EU-headquartered companies past MVP stage that are both:

1. newly in scope for CRA, NIS2 or DORA reporting obligations, needing the
   process but not the headcount; and
2. handling data sensitive enough that a public trust signal matters
   commercially.

**Target verticals:**
- Fintech and insurtech
- Healthtech
- Ticketing platforms *(already scoped)*
- HR-tech and recruitment-AI *(already scoped)*

**Sweet spot:** companies that have just become "a real target now".

**TBD (CPO):** the buyer persona and title (CISO, CTO, Head of Compliance?)
and the size band in employees or revenue.

## Core user stories

*Drafted from the pitch. The CPO should confirm or cut each one.*

- As a **compliance lead at a newly in-scope company**, I want a working
  vulnerability-intake and disclosure process, so that I can meet the CRA's
  24h/72h/14d deadlines without hiring a security team.
- As a **CTO**, I want our systems tested in stages against synthetic-data
  sandboxes, so that outside researchers find real flaws without putting
  production data at risk.
- As a **commercial lead**, I want a public, live security changelog, so that
  prospects and partners can check our security posture instead of taking our
  word for it.
- As a **customer**, I want findings triaged and paid by CVSS tier, so that
  the bounty budget is predictable and fair.
- As **the consultancy**, we want to run the full method on our own database
  first, so that we have a flagship case study before the first sale.

## Success metrics

**TBD (CPO).** The pitch defines none. Candidates to decide on:

- The flagship case study is live with a public changelog by <date>.
- <N> paying customers within <period>.
- Each customer's time from finding to fix to published changelog entry,
  compared with the CRA deadlines.
- How far customers have moved from private, through invite-only, to public.

## Scope boundaries

**In scope (first version):**
- The staged bounty programme on existing EU platforms
- Synthetic-data sandbox setup
- The public security changelog
- The flagship case study on our own database

**Out of scope:**
- Our own bounty platform
- A DBaaS product
- Large incumbents
- Pre-MVP companies
- Testing on production data

**TBD (CPO):** whether non-EU-headquartered companies are in scope, and how
far legal support goes (safe-harbour terms, contracts with researchers).

## Why now

- The CRA reporting clock started on 11 September 2026.
- EU-native bounty infrastructure already exists and is vetted by the
  Commission.
- Nobody has yet positioned "continuous, publicly provable security" as the
  product.

## Size of prize

**TBD (CPO).** Not covered in the pitch, and `/kickoff` requires it.

## Open questions

1. **How does this relate to the decision-matrix repo?** Is
   `regtech_cyber.db` the "own hardened database" that becomes the flagship
   case study, or is it the "rating tool"?
2. **Liability:** who carries legal risk if a public bounty finding leaks or
   is exploited before the fix? What do we need from the platforms' safe
   harbour?
3. **Disclosure tension:** publishing every finding helps marketing, but
   customers may resist full public disclosure. What is the minimum disclosure
   a customer has to accept to join?

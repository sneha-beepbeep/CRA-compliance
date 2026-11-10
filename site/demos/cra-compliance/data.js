// Synthetic sample data for the CRA tracker demo. The vendor, product, people
// and dates are invented. Requirement citations are real references; their
// short titles in the product are still pending legal review, so the demo
// shows the citation only, plus a neutral description written for this demo.
window.DEMO_DATA = {
  vendor: 'Northwind Scoring (fictional)',
  product: 'ScoreKit',
  version: '3.2',
  requirements: [
    { citation: 'CRA Annex I, Part I(2)(b)', note: 'Secure-by-default configuration', status: 'evidence_attached', review_by: '2027-03-31', evidence: 2 },
    { citation: 'CRA Annex I, Part I(2)(c)', note: 'Security updates', status: 'evidence_attached', review_by: '2026-10-01', evidence: 1 },
    { citation: 'CRA Annex I, Part I(2)(d)', note: 'Protection from unauthorised access', status: 'in_progress', evidence: 0 },
    { citation: 'CRA Annex I, Part I(2)(f)', note: 'Integrity of data and programs', status: 'not_started', evidence: 0 },
    { citation: 'CRA Annex I, Part II(1)', note: 'Identify and document components (SBOM)', status: 'in_progress', evidence: 1 },
    { citation: 'AI Act Art. 15(5)', note: 'Resilience against AI-specific attacks', status: 'not_applicable', rationale: 'Sample rationale: covered under the vendor’s separate model-security programme.', evidence: 0 },
  ],
  risks: [
    { name: 'Training-data poisoning', owner: 'ML lead', stage: 'treatment_in_place', last_tested: '2026-09-14', review_by: '2027-03-14', links: ['AI Act Art. 15(5)'] },
    { name: 'Adversarial examples at scoring time', owner: 'Security lead', stage: 'assessed_planned', planned: 'Add input-range checks and a red-team exercise in Q1.', last_tested: null, links: ['AI Act Art. 15(5)', 'CRA Annex I, Part I(2)(f)'] },
    { name: 'Model inversion revealing applicant data', owner: 'Privacy lead', stage: 'not_assessed', last_tested: null, links: ['CRA Annex I, Part I(2)(d)'] },
    { name: 'Model drift lowering accuracy', owner: 'ML lead', stage: 'treatment_in_place', last_tested: '2026-03-02', review_by: '2026-09-02', links: ['AI Act Art. 15(1)'] },
  ],
  // The demo pretends "today" is this date when deciding whether evidence is stale,
  // so the walkthrough looks the same whenever it is opened.
  today: '2026-11-10',
};

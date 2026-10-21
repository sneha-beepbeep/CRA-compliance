-- Column-limited views for customer sessions (D1, D2, OQ1).
-- app_customer has no rights on any base table. These views run with the
-- owner's rights, so each one filters on the customer tenant explicitly; with
-- no context, app_current_tenant() is NULL and every view returns 0 rows.
-- Never exposed: awareness time, deadline states, filing times, drills,
-- evidence URLs, AI-risk owner names, unreleased incidents.

CREATE OR REPLACE VIEW cust_deployment WITH (security_barrier) AS
SELECT d.id AS deployment_id, d.label, d.version_changed_at,
       p.name AS product_name, v.id AS version_id, v.label AS version_label,
       p.category_id AS annex_iii_category, vt.legal_name AS vendor_legal_name
FROM deployment d
JOIN product p ON p.id = d.product_id
JOIN tenant vt ON vt.id = d.vendor_tenant_id
LEFT JOIN product_version v ON v.id = d.version_id
WHERE d.customer_tenant_id = app_current_tenant();

CREATE OR REPLACE VIEW cust_requirement_status WITH (security_barrier) AS
SELECT d.id AS deployment_id, r.id AS requirement_id, rs.title AS requirement_set, r.citation,
       r.short_title, r.official_url,
       CASE WHEN s.status = 'evidence_attached' AND s.review_by < (now() AT TIME ZONE 'UTC')::date
            THEN 'evidence_stale' ELSE s.status END AS status,
       s.review_by, s.rationale, s.updated_at AS last_changed_at, s.id AS status_id
FROM deployment d
JOIN requirement_status s ON s.version_id = d.version_id
JOIN requirement r ON r.id = s.requirement_id
JOIN requirement_set rs ON rs.code = r.requirement_set_id
WHERE d.customer_tenant_id = app_current_tenant();

CREATE OR REPLACE VIEW cust_evidence WITH (security_barrier) AS
SELECT d.id AS deployment_id, e.requirement_status_id, e.ai_risk_id, e.title, e.type, e.evidence_date
FROM deployment d
JOIN evidence_item e ON e.vendor_tenant_id = d.vendor_tenant_id
LEFT JOIN requirement_status s ON s.id = e.requirement_status_id
LEFT JOIN ai_risk a ON a.id = e.ai_risk_id
WHERE d.customer_tenant_id = app_current_tenant()
  AND (s.version_id = d.version_id OR a.version_id = d.version_id);

CREATE OR REPLACE VIEW cust_ai_risk WITH (security_barrier) AS
SELECT d.id AS deployment_id, a.id AS ai_risk_id, a.name, a.attack_class,
       CASE WHEN a.stage = 'treatment_in_place' AND a.review_by < (now() AT TIME ZONE 'UTC')::date
            THEN 'evidence_stale' ELSE a.stage END AS stage,
       (SELECT max(e.evidence_date) FROM evidence_item e
         WHERE e.ai_risk_id = a.id AND e.type = 'test_report') AS last_tested,
       a.last_reviewed_on, (a.owner_id IS NOT NULL) AS owner_assigned, a.rationale
FROM deployment d
JOIN ai_risk a ON a.version_id = d.version_id
WHERE d.customer_tenant_id = app_current_tenant();

CREATE OR REPLACE VIEW cust_incident WITH (security_barrier) AS
SELECT ui.deployment_id, 'INC-' || cr.number AS reference, e.event_type, p.name AS product_name,
       v.label AS version_label, ui.informed_at, e.fix_available_at
FROM art14_users_informed ui
JOIN art14_event e ON e.id = ui.event_id
JOIN art14_customer_reference cr ON cr.event_id = e.id AND cr.customer_tenant_id = ui.customer_tenant_id
JOIN deployment d ON d.id = ui.deployment_id AND d.customer_tenant_id = ui.customer_tenant_id
JOIN product p ON p.id = e.product_id
LEFT JOIN product_version v ON v.id = e.product_version_id
WHERE ui.customer_tenant_id = app_current_tenant()
  AND ui.released AND ui.withdrawn_at IS NULL AND NOT e.is_drill;

-- Only the disclaimer template; nothing else from system_setting.
CREATE OR REPLACE VIEW cust_system_setting WITH (security_barrier) AS
SELECT key, value FROM system_setting WHERE key = 'disclaimer_template' AND app_current_tenant() IS NOT NULL;

REVOKE ALL ON cust_system_setting, cust_deployment, cust_requirement_status, cust_evidence, cust_ai_risk, cust_incident
    FROM PUBLIC, app_vendor, app_auth;
GRANT SELECT ON cust_system_setting, cust_deployment, cust_requirement_status, cust_evidence, cust_ai_risk, cust_incident
    TO app_customer;

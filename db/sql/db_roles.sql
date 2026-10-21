-- Database roles (technical plan, "Authorization and isolation").
--
--   app_vendor    vendor sessions; row-level security on vendor_tenant_id;
--                 incident-detail tables additionally require app.is_responder.
--   app_customer  customer sessions; may read ONLY the column-limited cust_* views.
--   app_auth      the login role's own rights, used before the request context is
--                 set: resolve the session, the user, the tenant and the responder flag.
--
-- The deployment's login user is granted app_auth (INHERIT TRUE) and app_vendor /
-- app_customer WITH INHERIT FALSE, SET TRUE (PostgreSQL 16), so it can only use
-- tenant data after `SET LOCAL ROLE`. Roles are cluster-wide; this is idempotent.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_vendor') THEN
        CREATE ROLE app_vendor NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_customer') THEN
        CREATE ROLE app_customer NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_auth') THEN
        CREATE ROLE app_auth NOLOGIN NOINHERIT;
    END IF;
END $$;

-- Request-context helpers. A missing context yields NULL, so policies match 0 rows.
CREATE OR REPLACE FUNCTION app_current_tenant() RETURNS uuid
    LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('app.tenant_id', true), '')::uuid $$;
CREATE OR REPLACE FUNCTION app_is_responder() RETURNS boolean
    LANGUAGE sql STABLE AS $$ SELECT coalesce(current_setting('app.is_responder', true), '') = 'on' $$;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM app_vendor, app_customer, app_auth;
GRANT USAGE ON SCHEMA public TO app_vendor, app_customer, app_auth;
GRANT EXECUTE ON FUNCTION app_current_tenant(), app_is_responder() TO app_vendor, app_customer, app_auth;

-- Reference data: read-only for vendor sessions.
GRANT SELECT ON annex_iii_category, requirement_set, requirement, category_requirement_set,
                taxonomy, taxonomy_item, system_setting TO app_vendor;

-- Tenant data for vendor sessions. No DELETE except on pure link/evidence rows;
-- events, statuses and grants are never deleted.
GRANT SELECT, INSERT, UPDATE ON tenant, user_account, role_grant, customer_invitation,
      activity_sharing_setting, product, product_version, deployment, requirement_status,
      evidence_item, ai_risk, ai_risk_requirement_link, art14_event, art14_event_detail,
      art14_event_deployment, art14_users_informed, art14_customer_reference, art14_event_link,
      drill_outcome, import_batch, export_record TO app_vendor;
GRANT DELETE ON ai_risk_requirement_link, evidence_item, art14_event_deployment TO app_vendor;

-- Audit: insert and read only (no UPDATE, DELETE or TRUNCATE for anyone but the owner,
-- and the owner is blocked by triggers in audit_append_only.sql).
GRANT SELECT, INSERT ON audit_event TO app_vendor;
GRANT INSERT ON audit_event TO app_customer;

-- The auth role: identity tables only.
GRANT SELECT ON tenant, user_account, role_grant TO app_auth;
GRANT UPDATE (last_login) ON user_account TO app_auth;
GRANT SELECT, INSERT, UPDATE, DELETE ON django_session TO app_auth;

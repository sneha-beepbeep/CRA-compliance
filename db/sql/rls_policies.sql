-- Row-level security on every table that carries vendor_tenant_id.
-- Applied dynamically so a new tenant table cannot be forgotten; the isolation
-- test suite also fails if any such table lacks RLS or a policy.

DO $$
DECLARE
    t text;
    responder_only text[] := ARRAY['art14_event_detail', 'art14_event_deployment'];
    auth_readable text[] := ARRAY['tenant', 'user_account', 'role_grant'];
BEGIN
    FOR t IN
        SELECT c.table_name FROM information_schema.columns c
        JOIN information_schema.tables tb ON tb.table_name = c.table_name AND tb.table_schema = c.table_schema
        WHERE c.table_schema = 'public' AND c.column_name = 'vendor_tenant_id' AND tb.table_type = 'BASE TABLE'
    LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('DROP POLICY IF EXISTS vendor_isolation ON %I', t);
        IF t = ANY (responder_only) THEN
            EXECUTE format($p$CREATE POLICY vendor_isolation ON %I TO app_vendor
                USING (vendor_tenant_id = app_current_tenant() AND app_is_responder())
                WITH CHECK (vendor_tenant_id = app_current_tenant() AND app_is_responder())$p$, t);
        ELSE
            EXECUTE format($p$CREATE POLICY vendor_isolation ON %I TO app_vendor
                USING (vendor_tenant_id = app_current_tenant())
                WITH CHECK (vendor_tenant_id = app_current_tenant())$p$, t);
        END IF;
        EXECUTE format('DROP POLICY IF EXISTS auth_lookup ON %I', t);
        IF t = ANY (auth_readable) THEN
            EXECUTE format('CREATE POLICY auth_lookup ON %I FOR SELECT TO app_auth USING (true)', t);
        END IF;
    END LOOP;
END $$;

-- Customer sessions may insert their own activity entries into the vendor's audit
-- trail (D9: views and exports), and nothing else.
DROP POLICY IF EXISTS customer_activity_insert ON audit_event;
CREATE POLICY customer_activity_insert ON audit_event FOR INSERT TO app_customer
    WITH CHECK (actor_tenant_id = app_current_tenant()
                AND vendor_tenant_id = nullif(current_setting('app.vendor_tenant_id', true), '')::uuid);

-- QA-01: Django's auth.login() updates user_account.last_login with the login
-- role's own rights (before any tenant context). The column grant in
-- db_roles.sql limits app_auth to that one column; this policy lets the UPDATE
-- reach active accounts' rows. No INSERT or DELETE for app_auth anywhere.
DROP POLICY IF EXISTS auth_last_login ON user_account;
CREATE POLICY auth_last_login ON user_account FOR UPDATE TO app_auth
    USING (is_active) WITH CHECK (is_active);

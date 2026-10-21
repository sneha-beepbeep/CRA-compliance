-- Independent check of the Python deadline engine (apps/art14/deadlines.py).
-- Moved from the SQLite knowledge base, revised per PRD section 6:
--   * includes severe incidents;
--   * vulnerability final report = fix or mitigation available + 14 days;
--   * severe-incident final report = notification filing + 1 month under the
--     configured month rule (system_setting 'month_rule'):
--       calendar_clamp_utc: same day next month in UTC, clamped to month end
--         (PostgreSQL's timestamp + interval '1 month' clamps: 2027-01-31 -> 2027-02-28;
--          SQLite's date('2027-01-31','+1 month') gave 2027-03-03);
--       days_30: + 30 days;
--   * adds the 'stopped' state for events closed as not reportable.
-- All arithmetic is done on UTC wall time so the session TimeZone can't shift days.
-- The differential test compares this with the Python engine.

CREATE OR REPLACE FUNCTION cra_clock_state(start_at timestamptz, due_at timestamptz,
                                           filed_at timestamptz, now_at timestamptz,
                                           stopped boolean) RETURNS text
LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE
        WHEN filed_at IS NOT NULL AND due_at IS NOT NULL THEN
            CASE WHEN filed_at <= due_at THEN 'met' ELSE 'late' END
        WHEN stopped THEN 'stopped'
        WHEN start_at IS NULL OR due_at IS NULL THEN 'not started'
        WHEN now_at > due_at THEN 'overdue'
        ELSE 'open'
    END
$$;

CREATE OR REPLACE FUNCTION cra_utc_add(ts timestamptz, iv interval) RETURNS timestamptz
LANGUAGE sql IMMUTABLE AS $$ SELECT ((ts AT TIME ZONE 'UTC') + iv) AT TIME ZONE 'UTC' $$;

CREATE OR REPLACE FUNCTION cra_deadline_check_at(as_of timestamptz)
RETURNS TABLE (
    event_id uuid, vendor_tenant_id uuid, ref_number integer, event_type text, is_drill boolean,
    status text, awareness_at timestamptz,
    early_warning_due timestamptz, early_warning_filed_at timestamptz, early_warning_state text,
    notification_due timestamptz, notification_filed_at timestamptz, notification_state text,
    final_report_start timestamptz, final_report_due timestamptz, final_report_filed_at timestamptz,
    final_report_state text, month_rule text
)
LANGUAGE sql STABLE SECURITY INVOKER AS $$
    WITH rule AS (
        SELECT coalesce((SELECT value #>> '{}' FROM system_setting WHERE key = 'month_rule'),
                        'calendar_clamp_utc') AS r
    ), d AS (
        SELECT e.*,
               (date_trunc('minute', as_of AT TIME ZONE 'UTC') AT TIME ZONE 'UTC') AS now_m,
               cra_utc_add(e.awareness_at, interval '24 hours') AS ew_due,
               cra_utc_add(e.awareness_at, interval '72 hours') AS nt_due,
               CASE WHEN e.event_type = 'vulnerability' THEN e.fix_available_at
                    ELSE e.notification_filed_at END AS fr_start,
               (SELECT r FROM rule) AS rule_used
        FROM art14_event e
    )
    SELECT d.id, d.vendor_tenant_id, d.ref_number::integer, d.event_type::text, d.is_drill, d.status::text,
           d.awareness_at,
           d.ew_due, d.early_warning_filed_at,
           cra_clock_state(d.awareness_at, d.ew_due, d.early_warning_filed_at, d.now_m,
                           d.status = 'closed_not_reportable'),
           d.nt_due, d.notification_filed_at,
           cra_clock_state(d.awareness_at, d.nt_due, d.notification_filed_at, d.now_m,
                           d.status = 'closed_not_reportable'),
           d.fr_start, fr.due, d.final_report_filed_at,
           cra_clock_state(d.fr_start, fr.due, d.final_report_filed_at, d.now_m,
                           d.status = 'closed_not_reportable'),
           d.rule_used
    FROM d
    CROSS JOIN LATERAL (
        SELECT CASE
            WHEN d.fr_start IS NULL THEN NULL
            WHEN d.event_type = 'vulnerability' THEN cra_utc_add(d.fr_start, interval '14 days')
            WHEN d.rule_used = 'days_30' THEN cra_utc_add(d.fr_start, interval '30 days')
            ELSE cra_utc_add(d.fr_start, interval '1 month')
        END AS due
    ) fr
$$;

-- security_invoker: row-level security on art14_event applies to the caller.
CREATE OR REPLACE VIEW cra_deadline_check WITH (security_invoker = true) AS
    SELECT * FROM cra_deadline_check_at(now());

GRANT EXECUTE ON FUNCTION cra_clock_state(timestamptz, timestamptz, timestamptz, timestamptz, boolean),
                          cra_utc_add(timestamptz, interval), cra_deadline_check_at(timestamptz) TO app_vendor;
GRANT SELECT ON cra_deadline_check TO app_vendor;

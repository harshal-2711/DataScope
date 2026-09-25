-- DataScope Security & RLS Hardening Migration
-- Migration: 20260925000000_security_hardening.sql
-- Description: Enforce least-privilege RLS policies, user-isolation on users table, and owner delete protections.

-- 1. Ensure RLS is active on all tables
ALTER TABLE IF EXISTS public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.company_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.dataset_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.data_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.data_sync_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.audit_logs ENABLE ROW LEVEL SECURITY;

-- 2. Data sync jobs source column alignment
ALTER TABLE IF EXISTS public.data_sync_jobs ALTER COLUMN source_id DROP NOT NULL;

-- 3. Owner-only delete protection for companies
DROP POLICY IF EXISTS "Owners can delete company" ON public.companies;
CREATE POLICY "Owners can delete company" ON public.companies FOR DELETE
    USING (public.user_has_company_role(id, ARRAY['owner']));

-- 4. Admin and Owner delete protection for dataset versions
DROP POLICY IF EXISTS "Admins and Owners can delete dataset versions" ON public.dataset_versions;
CREATE POLICY "Admins and Owners can delete dataset versions" ON public.dataset_versions FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM public.datasets d
        WHERE d.id = dataset_versions.dataset_id
          AND public.user_has_company_role(d.company_id, ARRAY['owner', 'admin'])
    ));

-- 5. Sync jobs management policy for analysts and admins
DROP POLICY IF EXISTS "Analysts can manage sync jobs" ON public.data_sync_jobs;
CREATE POLICY "Analysts can manage sync jobs" ON public.data_sync_jobs FOR ALL
    USING (EXISTS (
        SELECT 1 FROM public.data_sources s
        WHERE s.id = COALESCE(data_sync_jobs.data_source_id, data_sync_jobs.source_id)
          AND public.user_has_company_role(s.company_id, ARRAY['owner', 'admin', 'analyst'])
    ));

-- 6. User record self-isolation
DROP POLICY IF EXISTS "Users can only read own user record" ON public.users;
CREATE POLICY "Users can only read own user record" ON public.users FOR SELECT
    USING (auth.uid()::text = id::text);

DROP POLICY IF EXISTS "Users can only update own user record" ON public.users;
CREATE POLICY "Users can only update own user record" ON public.users FOR UPDATE
    USING (auth.uid()::text = id::text);

-- DataScope Supabase Row-Level Security (RLS) & Storage Migration
-- Migration: 20260923000001_rls_policies.sql
-- Description: Enforce workspace tenant isolation across all public tables and storage buckets

-- 1. Enable RLS on all public tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.company_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dataset_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_sync_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- 2. Helper Functions for Workspace Membership & Role Checking
CREATE OR REPLACE FUNCTION public.user_has_company_access(target_company_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.company_memberships
        WHERE company_id = target_company_id
          AND user_id = auth.uid()
          AND status = 'active'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.user_has_company_role(target_company_id UUID, required_roles TEXT[])
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM public.company_memberships
        WHERE company_id = target_company_id
          AND user_id = auth.uid()
          AND role = ANY(required_roles)
          AND status = 'active'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. Profiles Policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- 4. Companies Policies
DROP POLICY IF EXISTS "Users can view companies they belong to" ON public.companies;
CREATE POLICY "Users can view companies they belong to"
    ON public.companies FOR SELECT
    USING (public.user_has_company_access(id));

DROP POLICY IF EXISTS "Authenticated users can create companies" ON public.companies;
CREATE POLICY "Authenticated users can create companies"
    ON public.companies FOR INSERT
    WITH CHECK (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "Admins and Owners can update company" ON public.companies;
CREATE POLICY "Admins and Owners can update company"
    ON public.companies FOR UPDATE
    USING (public.user_has_company_role(id, ARRAY['owner', 'admin']));

-- 5. Company Memberships Policies
DROP POLICY IF EXISTS "Members can view workspace team" ON public.company_memberships;
CREATE POLICY "Members can view workspace team"
    ON public.company_memberships FOR SELECT
    USING (public.user_has_company_access(company_id));

DROP POLICY IF EXISTS "Admins and Owners can invite/add members" ON public.company_memberships;
CREATE POLICY "Admins and Owners can invite/add members"
    ON public.company_memberships FOR INSERT
    WITH CHECK (
        public.user_has_company_role(company_id, ARRAY['owner', 'admin'])
        OR auth.uid() = user_id -- Allow creator initial self-membership
    );

DROP POLICY IF EXISTS "Admins and Owners can update member roles" ON public.company_memberships;
CREATE POLICY "Admins and Owners can update member roles"
    ON public.company_memberships FOR UPDATE
    USING (public.user_has_company_role(company_id, ARRAY['owner', 'admin']));

DROP POLICY IF EXISTS "Admins and Owners can remove members" ON public.company_memberships;
CREATE POLICY "Admins and Owners can remove members"
    ON public.company_memberships FOR DELETE
    USING (public.user_has_company_role(company_id, ARRAY['owner', 'admin']));

-- 6. Datasets Policies
DROP POLICY IF EXISTS "Members can view company datasets" ON public.datasets;
CREATE POLICY "Members can view company datasets"
    ON public.datasets FOR SELECT
    USING (public.user_has_company_access(company_id));

DROP POLICY IF EXISTS "Analysts, Admins, and Owners can upload datasets" ON public.datasets;
CREATE POLICY "Analysts, Admins, and Owners can upload datasets"
    ON public.datasets FOR INSERT
    WITH CHECK (public.user_has_company_role(company_id, ARRAY['owner', 'admin', 'analyst']));

DROP POLICY IF EXISTS "Analysts, Admins, and Owners can update datasets" ON public.datasets;
CREATE POLICY "Analysts, Admins, and Owners can update datasets"
    ON public.datasets FOR UPDATE
    USING (public.user_has_company_role(company_id, ARRAY['owner', 'admin', 'analyst']));

DROP POLICY IF EXISTS "Admins and Owners can delete datasets" ON public.datasets;
CREATE POLICY "Admins and Owners can delete datasets"
    ON public.datasets FOR DELETE
    USING (public.user_has_company_role(company_id, ARRAY['owner', 'admin']));

-- 7. Dataset Versions Policies
DROP POLICY IF EXISTS "Members can view dataset versions" ON public.dataset_versions;
CREATE POLICY "Members can view dataset versions"
    ON public.dataset_versions FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.datasets d
        WHERE d.id = dataset_id AND public.user_has_company_access(d.company_id)
    ));

DROP POLICY IF EXISTS "Analysts can insert dataset versions" ON public.dataset_versions;
CREATE POLICY "Analysts can insert dataset versions"
    ON public.dataset_versions FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM public.datasets d
        WHERE d.id = dataset_id AND public.user_has_company_role(d.company_id, ARRAY['owner', 'admin', 'analyst'])
    ));

-- 8. Data Sources Policies
DROP POLICY IF EXISTS "Members can view data sources" ON public.data_sources;
CREATE POLICY "Members can view data sources"
    ON public.data_sources FOR SELECT
    USING (public.user_has_company_access(company_id));

DROP POLICY IF EXISTS "Analysts can manage data sources" ON public.data_sources;
CREATE POLICY "Analysts can manage data sources"
    ON public.data_sources FOR ALL
    USING (public.user_has_company_role(company_id, ARRAY['owner', 'admin', 'analyst']));

-- 9. Data Sync Jobs Policies
DROP POLICY IF EXISTS "Members can view sync jobs" ON public.data_sync_jobs;
CREATE POLICY "Members can view sync jobs"
    ON public.data_sync_jobs FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.data_sources s
        WHERE s.id = source_id AND public.user_has_company_access(s.company_id)
    ));

-- 10. Reports Policies
DROP POLICY IF EXISTS "Members can view company reports" ON public.reports;
CREATE POLICY "Members can view company reports"
    ON public.reports FOR SELECT
    USING (public.user_has_company_access(company_id));

DROP POLICY IF EXISTS "Analysts can create reports" ON public.reports;
CREATE POLICY "Analysts can create reports"
    ON public.reports FOR INSERT
    WITH CHECK (public.user_has_company_role(company_id, ARRAY['owner', 'admin', 'analyst']));

-- 11. Audit Logs Policies
DROP POLICY IF EXISTS "Members can view audit logs" ON public.audit_logs;
CREATE POLICY "Members can view audit logs"
    ON public.audit_logs FOR SELECT
    USING (public.user_has_company_access(company_id));

-- 12. Storage Buckets Creation & Storage RLS
INSERT INTO storage.buckets (id, name, public)
VALUES 
    ('datasets', 'datasets', false),
    ('reports', 'reports', false)
ON CONFLICT (id) DO NOTHING;

-- Storage RLS Policies
DROP POLICY IF EXISTS "Authenticated users can upload datasets" ON storage.objects;
CREATE POLICY "Authenticated users can upload datasets"
    ON storage.objects FOR INSERT
    WITH CHECK (bucket_id IN ('datasets', 'reports') AND auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "Authenticated users can read dataset files" ON storage.objects;
CREATE POLICY "Authenticated users can read dataset files"
    ON storage.objects FOR SELECT
    USING (bucket_id IN ('datasets', 'reports') AND auth.uid() IS NOT NULL);

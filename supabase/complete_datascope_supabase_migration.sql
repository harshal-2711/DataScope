-- ==============================================================================
-- DATASCOPE COMPLETE SUPABASE DATABASE & STORAGE SETUP
-- Run this entire script in Supabase Dashboard -> SQL Editor -> Run
-- ==============================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Profiles Table (1-to-1 with auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Automatic Profile Creation Trigger on Auth Signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url, created_at, updated_at)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
        NEW.raw_user_meta_data->>'avatar_url',
        now(),
        now()
    )
    ON CONFLICT (id) DO UPDATE
    SET email = EXCLUDED.email,
        full_name = COALESCE(EXCLUDED.full_name, public.profiles.full_name),
        updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT OR UPDATE ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 4. Companies / Workspaces Table
CREATE TABLE IF NOT EXISTS public.companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    industry TEXT NOT NULL DEFAULT 'SaaS / Technology',
    company_size TEXT NOT NULL DEFAULT '11-50 Employees',
    country TEXT NOT NULL DEFAULT 'United States',
    primary_objective TEXT NOT NULL DEFAULT 'Revenue Growth & Margin Protection',
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. Company Memberships & RBAC
CREATE TABLE IF NOT EXISTS public.company_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'analyst' CHECK (role IN ('owner', 'admin', 'analyst', 'viewer')),
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(company_id, user_id)
);

-- 6. Datasets Metadata Table
CREATE TABLE IF NOT EXISTS public.datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    filename TEXT NOT NULL,
    storage_path TEXT,
    file_format TEXT NOT NULL DEFAULT 'csv',
    file_size_bytes BIGINT DEFAULT 0,
    row_count INT NOT NULL DEFAULT 0,
    column_count INT NOT NULL DEFAULT 0,
    column_schema JSONB NOT NULL DEFAULT '[]'::jsonb,
    detected_domain JSONB NOT NULL DEFAULT '{}'::jsonb,
    summary_stats JSONB NOT NULL DEFAULT '{}'::jsonb,
    quality_score NUMERIC NOT NULL DEFAULT 100.0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 7. Dataset Versions for Rollback & Audit
CREATE TABLE IF NOT EXISTS public.dataset_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
    version_number INT NOT NULL DEFAULT 1,
    storage_path TEXT NOT NULL,
    row_count INT NOT NULL DEFAULT 0,
    change_summary TEXT,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(dataset_id, version_number)
);

-- 8. Data Sources (Live Connectors)
CREATE TABLE IF NOT EXISTS public.data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('rest_api', 'postgres', 'mysql', 'google_sheets', 'file_upload', 'manual_entry')),
    sync_frequency TEXT NOT NULL DEFAULT 'hourly',
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'error', 'syncing')),
    last_sync_at TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 9. Data Sync Jobs
CREATE TABLE IF NOT EXISTS public.data_sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES public.data_sources(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'success', 'failed')),
    rows_synced INT NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- 10. Reports Table (Executive Dossiers)
CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES public.companies(id) ON DELETE CASCADE,
    dataset_id UUID REFERENCES public.datasets(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    report_type TEXT NOT NULL DEFAULT 'executive_decision_dossier',
    report_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    storage_path_pdf TEXT,
    storage_path_docx TEXT,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 11. Audit Logs Table
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES public.companies(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_memberships_user_id ON public.company_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_company_id ON public.company_memberships(company_id);
CREATE INDEX IF NOT EXISTS idx_datasets_company_id ON public.datasets(company_id);
CREATE INDEX IF NOT EXISTS idx_data_sources_company_id ON public.data_sources(company_id);
CREATE INDEX IF NOT EXISTS idx_reports_company_id ON public.reports(company_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_company_id ON public.audit_logs(company_id);

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.company_memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dataset_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_sync_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Helper Functions
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

-- Profiles Policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Companies Policies
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

-- Memberships Policies
DROP POLICY IF EXISTS "Members can view workspace team" ON public.company_memberships;
CREATE POLICY "Members can view workspace team"
    ON public.company_memberships FOR SELECT
    USING (public.user_has_company_access(company_id));

DROP POLICY IF EXISTS "Admins and Owners can invite/add members" ON public.company_memberships;
CREATE POLICY "Admins and Owners can invite/add members"
    ON public.company_memberships FOR INSERT
    WITH CHECK (
        public.user_has_company_role(company_id, ARRAY['owner', 'admin'])
        OR auth.uid() = user_id
    );

DROP POLICY IF EXISTS "Admins and Owners can update member roles" ON public.company_memberships;
CREATE POLICY "Admins and Owners can update member roles"
    ON public.company_memberships FOR UPDATE
    USING (public.user_has_company_role(company_id, ARRAY['owner', 'admin']));

DROP POLICY IF EXISTS "Admins and Owners can remove members" ON public.company_memberships;
CREATE POLICY "Admins and Owners can remove members"
    ON public.company_memberships FOR DELETE
    USING (public.user_has_company_role(company_id, ARRAY['owner', 'admin']));

-- Datasets Policies
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

-- Dataset Versions Policies
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

-- Data Sources Policies
DROP POLICY IF EXISTS "Members can view data sources" ON public.data_sources;
CREATE POLICY "Members can view data sources"
    ON public.data_sources FOR SELECT
    USING (public.user_has_company_access(company_id));

DROP POLICY IF EXISTS "Analysts can manage data sources" ON public.data_sources;
CREATE POLICY "Analysts can manage data sources"
    ON public.data_sources FOR ALL
    USING (public.user_has_company_role(company_id, ARRAY['owner', 'admin', 'analyst']));

-- Data Sync Jobs Policies
DROP POLICY IF EXISTS "Members can view sync jobs" ON public.data_sync_jobs;
CREATE POLICY "Members can view sync jobs"
    ON public.data_sync_jobs FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.data_sources s
        WHERE s.id = source_id AND public.user_has_company_access(s.company_id)
    ));

-- Reports Policies
DROP POLICY IF EXISTS "Members can view company reports" ON public.reports;
CREATE POLICY "Members can view company reports"
    ON public.reports FOR SELECT
    USING (public.user_has_company_access(company_id));

DROP POLICY IF EXISTS "Analysts can create reports" ON public.reports;
CREATE POLICY "Analysts can create reports"
    ON public.reports FOR INSERT
    WITH CHECK (public.user_has_company_role(company_id, ARRAY['owner', 'admin', 'analyst']));

-- Audit Logs Policies
DROP POLICY IF EXISTS "Members can view audit logs" ON public.audit_logs;
CREATE POLICY "Members can view audit logs"
    ON public.audit_logs FOR SELECT
    USING (public.user_has_company_access(company_id));

-- ==============================================================================
-- STORAGE BUCKETS & STORAGE SECURITY
-- ==============================================================================

INSERT INTO storage.buckets (id, name, public)
VALUES 
    ('datasets', 'datasets', false),
    ('reports', 'reports', false)
ON CONFLICT (id) DO NOTHING;

DROP POLICY IF EXISTS "Authenticated users can upload datasets" ON storage.objects;
CREATE POLICY "Authenticated users can upload datasets"
    ON storage.objects FOR INSERT
    WITH CHECK (bucket_id IN ('datasets', 'reports') AND auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "Authenticated users can read dataset files" ON storage.objects;
CREATE POLICY "Authenticated users can read dataset files"
    ON storage.objects FOR SELECT
    USING (bucket_id IN ('datasets', 'reports') AND auth.uid() IS NOT NULL);

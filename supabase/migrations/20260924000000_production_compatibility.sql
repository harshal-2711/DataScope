-- DataScope Production Schema Compatibility & DataRecords Migration
-- Migration: 20260924000000_production_compatibility.sql
-- Description: Additive migration to align Supabase PostgreSQL schema with DataScope SQLAlchemy models and add persistent DataRecords table.

-- 1. Ensure extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. Enhance Profiles Table
ALTER TABLE IF EXISTS public.profiles
    ADD COLUMN IF NOT EXISTS hashed_password TEXT,
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS is_verified BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS auth_provider TEXT NOT NULL DEFAULT 'local',
    ADD COLUMN IF NOT EXISTS google_id TEXT,
    ADD COLUMN IF NOT EXISTS reset_password_token TEXT,
    ADD COLUMN IF NOT EXISTS reset_password_expires_at TIMESTAMPTZ;

-- 3. Enhance Companies Table
ALTER TABLE IF EXISTS public.companies
    ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS domain_type TEXT NOT NULL DEFAULT 'General Business',
    ADD COLUMN IF NOT EXISTS logo_url TEXT;

-- Sync owner_id with created_by if created_by exists
UPDATE public.companies SET owner_id = created_by WHERE owner_id IS NULL AND created_by IS NOT NULL;

-- 4. Enhance Company Memberships Table
ALTER TABLE IF EXISTS public.company_memberships
    ADD COLUMN IF NOT EXISTS invited_email TEXT,
    ADD COLUMN IF NOT EXISTS invitation_token TEXT,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- 5. Enhance Datasets Table
ALTER TABLE IF EXISTS public.datasets
    ADD COLUMN IF NOT EXISTS name TEXT,
    ADD COLUMN IF NOT EXISTS file_type TEXT NOT NULL DEFAULT 'csv',
    ADD COLUMN IF NOT EXISTS active_version_number INT NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS current_row_count INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS current_col_count INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS currency_symbol TEXT NOT NULL DEFAULT 'Rs. ',
    ADD COLUMN IF NOT EXISTS domain_id TEXT NOT NULL DEFAULT 'general_business',
    ADD COLUMN IF NOT EXISTS domain_name TEXT NOT NULL DEFAULT 'General Business',
    ADD COLUMN IF NOT EXISTS created_by_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

-- Populate default name from filename if NULL
UPDATE public.datasets SET name = filename WHERE name IS NULL AND filename IS NOT NULL;
UPDATE public.datasets SET created_by_id = user_id WHERE created_by_id IS NULL AND user_id IS NOT NULL;

-- 6. Enhance Dataset Versions Table
ALTER TABLE IF EXISTS public.dataset_versions
    ADD COLUMN IF NOT EXISTS col_count INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS column_schema TEXT,
    ADD COLUMN IF NOT EXISTS created_by_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

ALTER TABLE IF EXISTS public.dataset_versions
    ALTER COLUMN storage_path DROP NOT NULL;

UPDATE public.dataset_versions SET created_by_id = created_by WHERE created_by_id IS NULL AND created_by IS NOT NULL;

-- 7. Enhance Data Sources Table
ALTER TABLE IF EXISTS public.data_sources
    ADD COLUMN IF NOT EXISTS dataset_id UUID REFERENCES public.datasets(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS config_json TEXT NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS is_paused BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS next_sync_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS last_error_message TEXT,
    ADD COLUMN IF NOT EXISTS total_records_synced INT NOT NULL DEFAULT 0;

-- 8. Create Data Records Table (Row-Level Multi-Tenant Storage)
CREATE TABLE IF NOT EXISTS public.data_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
    version_id UUID REFERENCES public.dataset_versions(id) ON DELETE CASCADE,
    row_index INT NOT NULL,
    record_json TEXT NOT NULL DEFAULT '{}',
    is_deleted INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_data_records_dataset_id ON public.data_records(dataset_id);
CREATE INDEX IF NOT EXISTS idx_data_records_version_id ON public.data_records(version_id);
CREATE INDEX IF NOT EXISTS idx_data_records_dataset_row ON public.data_records(dataset_id, row_index);
CREATE INDEX IF NOT EXISTS idx_data_records_active ON public.data_records(dataset_id, is_deleted);

-- Enable RLS on data_records
ALTER TABLE public.data_records ENABLE ROW LEVEL SECURITY;

-- RLS Policies for data_records
DROP POLICY IF EXISTS "Members can view company dataset records" ON public.data_records;
CREATE POLICY "Members can view company dataset records"
    ON public.data_records FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM public.datasets d
        WHERE d.id = dataset_id AND public.user_has_company_access(d.company_id)
    ));

DROP POLICY IF EXISTS "Analysts can manage dataset records" ON public.data_records;
CREATE POLICY "Analysts can manage dataset records"
    ON public.data_records FOR ALL
    USING (EXISTS (
        SELECT 1 FROM public.datasets d
        WHERE d.id = dataset_id AND public.user_has_company_role(d.company_id, ARRAY['owner', 'admin', 'analyst'])
    ));

-- 9. Enhance Data Sync Jobs Table
ALTER TABLE IF EXISTS public.data_sync_jobs
    ADD COLUMN IF NOT EXISTS data_source_id UUID REFERENCES public.data_sources(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS company_id UUID REFERENCES public.companies(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS sync_type TEXT NOT NULL DEFAULT 'manual',
    ADD COLUMN IF NOT EXISTS records_added INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS records_updated INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS records_rejected INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS log_output TEXT;

-- 10. Enhance Audit Logs Table
ALTER TABLE IF EXISTS public.audit_logs
    ADD COLUMN IF NOT EXISTS user_email TEXT,
    ADD COLUMN IF NOT EXISTS target_type TEXT NOT NULL DEFAULT 'dataset',
    ADD COLUMN IF NOT EXISTS target_id TEXT,
    ADD COLUMN IF NOT EXISTS details_json TEXT;

-- 11. Create Performance Indexes
CREATE INDEX IF NOT EXISTS idx_data_sources_dataset_id ON public.data_sources(dataset_id);
CREATE INDEX IF NOT EXISTS idx_data_sources_company_status ON public.data_sources(company_id, status);
CREATE INDEX IF NOT EXISTS idx_dataset_versions_dataset_num ON public.dataset_versions(dataset_id, version_number);
CREATE INDEX IF NOT EXISTS idx_audit_logs_company_target ON public.audit_logs(company_id, target_type);

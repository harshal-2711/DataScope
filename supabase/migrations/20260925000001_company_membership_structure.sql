-- DataScope Company Membership Structure & Visibility Migration
-- Migration: 20260925000001_company_membership_structure.sql
-- Description: Clarify Company -> Owner -> Workers -> Role database relationships and provide clear overview view.

-- 1. Ensure composite index for fast company membership lookups
CREATE INDEX IF NOT EXISTS idx_company_memberships_company_role 
ON public.company_memberships (company_id, role, status);

-- 2. Ensure each company has an active owner membership for its designated owner_id
INSERT INTO public.company_memberships (id, company_id, user_id, role, status, created_at, updated_at)
SELECT 
    gen_random_uuid(),
    c.id,
    c.owner_id,
    'owner',
    'active',
    COALESCE(c.created_at, now()),
    COALESCE(c.updated_at, now())
FROM public.companies c
WHERE c.owner_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM public.company_memberships cm
      WHERE cm.company_id = c.id
        AND cm.user_id = c.owner_id
  );

-- 3. Create canonical view for Company -> User -> Email -> Role -> Status visibility
CREATE OR REPLACE VIEW public.company_members_overview AS
SELECT 
    c.name AS "Company",
    COALESCE(p.full_name, u.full_name, 'Invited Member') AS "User",
    COALESCE(p.email, u.email, cm.invited_email) AS "Email",
    UPPER(cm.role) AS "Role",
    INITCAP(cm.status) AS "Status",
    c.id AS company_id,
    cm.user_id,
    cm.id AS membership_id,
    (c.owner_id = cm.user_id) AS is_owner,
    cm.created_at,
    cm.updated_at
FROM public.company_memberships cm
JOIN public.companies c ON c.id = cm.company_id
LEFT JOIN public.profiles p ON p.id = cm.user_id
LEFT JOIN public.users u ON u.id = cm.user_id::text;

-- 4. Grant access to authenticated and service_role
GRANT SELECT ON public.company_members_overview TO authenticated;
GRANT SELECT ON public.company_members_overview TO service_role;

COMMENT ON VIEW public.company_members_overview IS 'Canonical DataScope visibility view: Company -> Owner -> Workers -> Role';

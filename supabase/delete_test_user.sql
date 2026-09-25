-- ==============================================================================
-- DATASCOPE: STRICT ZERO-RISK TEST USER AUDIT & RESET SCRIPT
-- Target Email: test-user@example.com
-- Mode: Production-Safe Dev Reset with Strict Workspace Ownership Guards
-- ==============================================================================

-- ==============================================================================
-- STRICT WORKSPACE DELETION CRITERIA:
-- A workspace/company will be DELETED IF AND ONLY IF ALL 4 CONDITIONS ARE MET:
-- 1. Target user is the verified creator (companies.created_by = target_user_id)
-- 2. Target user is the verified owner (company_memberships.role = 'owner')
-- 3. Zero other members exist in public.company_memberships
-- 4. Zero datasets or reports from any other user exist in the workspace
--
-- IF ANY of these conditions fail (e.g. user is only an analyst/admin, or someone
-- else created the workspace, or other members/data exist):
-- -> The workspace is 100% PRESERVED.
-- -> All datasets, data sources, reports, and sync jobs are PRESERVED.
-- -> Only the target user's individual membership record is removed.
-- ==============================================================================


-- ==============================================================================
-- PART 1: 100% READ-ONLY DIAGNOSTIC & DRY-RUN QUERY
-- (Run this FIRST in Supabase SQL Editor. It performs NO writes/deletes.)
-- ==============================================================================
WITH target AS (
    SELECT id, email, created_at, last_sign_in_at
    FROM auth.users
    WHERE email = 'test-user@example.com'
)
SELECT 
    t.id AS target_auth_user_id,
    t.email AS target_email,
    t.created_at AS auth_user_created_at,
    t.last_sign_in_at,
    p.full_name AS profile_name,
    p.created_at AS profile_created_at,
    
    -- Strict Ownership & Shared Data Breakdown for Each Workspace
    COALESCE((
        SELECT jsonb_agg(jsonb_build_object(
            'company_id', c.id,
            'company_name', c.name,
            'user_role_in_workspace', cm.role,
            'is_workspace_creator', (c.created_by = t.id),
            'is_workspace_owner_role', (cm.role = 'owner'),
            'other_members_count', (
                SELECT count(*) 
                FROM public.company_memberships cm2 
                WHERE cm2.company_id = c.id AND cm2.user_id != t.id
            ),
            'other_users_datasets_count', (
                SELECT count(*) 
                FROM public.datasets d 
                WHERE d.company_id = c.id AND d.user_id IS NOT NULL AND d.user_id != t.id
            ),
            'other_users_reports_count', (
                SELECT count(*) 
                FROM public.reports r 
                WHERE r.company_id = c.id AND r.created_by IS NOT NULL AND r.created_by != t.id
            ),
            'dry_run_action', CASE 
                WHEN (c.created_by = t.id) 
                     AND (cm.role = 'owner') 
                     AND ((SELECT count(*) FROM public.company_memberships cm2 WHERE cm2.company_id = c.id AND cm2.user_id != t.id) = 0)
                     AND ((SELECT count(*) FROM public.datasets d WHERE d.company_id = c.id AND d.user_id IS NOT NULL AND d.user_id != t.id) = 0)
                     AND ((SELECT count(*) FROM public.reports r WHERE r.company_id = c.id AND r.created_by IS NOT NULL AND r.created_by != t.id) = 0)
                THEN 'DELETE WORKSPACE (Confirmed sole-creator, sole-owner, 0 other members, 0 other data)'
                ELSE 'PRESERVE WORKSPACE 100% (Non-owned, shared, or contains other users data. Only unlink membership)'
            END
        ))
        FROM public.company_memberships cm
        JOIN public.companies c ON c.id = cm.company_id
        WHERE cm.user_id = t.id
    ), '[]'::jsonb) AS workspace_ownership_audit,
    
    -- Personal Artifact Counts
    (SELECT count(*) FROM public.datasets WHERE user_id = t.id) AS personal_datasets_count,
    (SELECT count(*) FROM public.reports WHERE created_by = t.id) AS personal_reports_count,
    (SELECT count(*) FROM public.audit_logs WHERE user_id = t.id) AS personal_audit_logs_count,
    (SELECT count(*) FROM storage.objects WHERE owner = t.id) AS owned_storage_files_count
FROM target t
LEFT JOIN public.profiles p ON p.id = t.id;


-- ==============================================================================
-- PART 2: STRICT SAFE RESET (DO BLOCK)
-- (Execute ONLY after inspecting Part 1 output in SQL Editor)
-- ==============================================================================
DO $$
DECLARE
    v_target_email TEXT := 'test-user@example.com';
    v_target_user_id UUID;
    v_company RECORD;
    v_is_creator BOOLEAN;
    v_is_owner_role BOOLEAN;
    v_other_members_count INT;
    v_other_datasets_count INT;
    v_other_reports_count INT;
BEGIN
    -- 1. Find user in auth.users
    SELECT id INTO v_target_user_id 
    FROM auth.users 
    WHERE email = lower(trim(v_target_email));

    IF v_target_user_id IS NULL THEN
        RAISE NOTICE '[DATASCOPE-RESET] Target email "%" not found in auth.users. Nothing to clean.', v_target_email;
        RETURN;
    END IF;

    RAISE NOTICE '[DATASCOPE-RESET] Found User ID: % for "%". Starting verified reset...', v_target_user_id, v_target_email;

    -- 2. Clean private storage objects owned directly by this user
    DELETE FROM storage.objects 
    WHERE owner = v_target_user_id;
    RAISE NOTICE '[DATASCOPE-RESET] [1/7] Cleaned personal storage objects.';

    -- 3. Clean personal audit logs of this user
    DELETE FROM public.audit_logs 
    WHERE user_id = v_target_user_id;
    RAISE NOTICE '[DATASCOPE-RESET] [2/7] Cleaned personal audit logs.';

    -- 4. Process all workspaces associated with this user
    FOR v_company IN 
        SELECT c.id, c.name, c.created_by, cm.role AS user_role
        FROM public.companies c
        JOIN public.company_memberships cm ON cm.company_id = c.id AND cm.user_id = v_target_user_id
    LOOP
        -- Check creator status
        v_is_creator := (v_company.created_by = v_target_user_id);
        v_is_owner_role := (v_company.user_role = 'owner');

        -- Count other members
        SELECT COUNT(*) INTO v_other_members_count
        FROM public.company_memberships
        WHERE company_id = v_company.id AND user_id != v_target_user_id;

        -- Count datasets created by OTHER users in this workspace
        SELECT COUNT(*) INTO v_other_datasets_count
        FROM public.datasets
        WHERE company_id = v_company.id AND user_id IS NOT NULL AND user_id != v_target_user_id;

        -- Count reports created by OTHER users in this workspace
        SELECT COUNT(*) INTO v_other_reports_count
        FROM public.reports
        WHERE company_id = v_company.id AND created_by IS NOT NULL AND created_by != v_target_user_id;

        -- Strict Deletion Condition: MUST be creator + owner + 0 other members + 0 other user data
        IF v_is_creator = TRUE 
           AND v_is_owner_role = TRUE 
           AND v_other_members_count = 0 
           AND v_other_datasets_count = 0 
           AND v_other_reports_count = 0 THEN
           
            -- Sole-owner workspace: Safe to cascade delete company resources
            DELETE FROM public.data_sync_jobs WHERE source_id IN (SELECT id FROM public.data_sources WHERE company_id = v_company.id);
            DELETE FROM public.data_sources WHERE company_id = v_company.id;
            DELETE FROM public.dataset_versions WHERE dataset_id IN (SELECT id FROM public.datasets WHERE company_id = v_company.id);
            DELETE FROM public.datasets WHERE company_id = v_company.id;
            DELETE FROM public.reports WHERE company_id = v_company.id;
            DELETE FROM public.audit_logs WHERE company_id = v_company.id;
            DELETE FROM public.company_memberships WHERE company_id = v_company.id;
            DELETE FROM public.companies WHERE id = v_company.id;
            RAISE NOTICE '[DATASCOPE-RESET] [3/7] DELETED sole-owned workspace "%" (ID: %)', v_company.name, v_company.id;
        ELSE
            -- NON-OWNED OR SHARED WORKSPACE: PRESERVE EVERYTHING.
            -- Only remove target user's membership.
            DELETE FROM public.company_memberships 
            WHERE company_id = v_company.id AND user_id = v_target_user_id;

            RAISE NOTICE '[DATASCOPE-RESET] [3/7] PRESERVED workspace "%" (Creator: %, Role: %, Other members: %, Other data: %). Removed only user membership.', 
                v_company.name, v_is_creator, v_company.user_role, v_other_members_count, (v_other_datasets_count + v_other_reports_count);
        END IF;
    END LOOP;

    -- 5. Remove any orphan company memberships if remaining
    DELETE FROM public.company_memberships 
    WHERE user_id = v_target_user_id;
    RAISE NOTICE '[DATASCOPE-RESET] [4/7] Removed user company memberships.';

    -- 6. Remove user profile
    DELETE FROM public.profiles 
    WHERE id = v_target_user_id;
    RAISE NOTICE '[DATASCOPE-RESET] [5/7] Removed user profile in public.profiles.';

    -- 7. Delete user from Supabase Authentication
    DELETE FROM auth.users 
    WHERE id = v_target_user_id;
    RAISE NOTICE '[DATASCOPE-RESET] [6/7] Removed user from auth.users.';

    RAISE NOTICE '[DATASCOPE-RESET] [7/7] SUCCESS: User % reset complete. Ready for fresh registration!', v_target_email;
END $$;

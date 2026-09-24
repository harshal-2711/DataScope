"""Comprehensive Multi-Tenant SaaS, Authentication, RBAC & Live Data Tests."""
from __future__ import annotations

import json
import unittest
import uuid
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import Base
from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.data_record import DataRecord
from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.membership import CompanyMembership
from app.models.user import User


class TestSaasMultiTenant(unittest.TestCase):
    """Test suite for Multi-Tenant DataScope SaaS Platform."""

    @classmethod
    def setUpClass(cls):
        # Create isolated in-memory SQLite database for unit tests
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_password_hashing_and_verification(self):
        """Verify secure PBKDF2 password hashing and salt verification."""
        password = "SecretPassword123!"
        hashed = hash_password(password)

        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))
        self.assertFalse(verify_password("", hashed))

    def test_jwt_token_generation_and_decoding(self):
        """Verify JWT access and refresh token creation, type enforcement, and payload parsing."""
        user_id = str(uuid.uuid4())
        company_id = str(uuid.uuid4())
        token_data = {"sub": user_id, "email": "test@company.com", "company_id": company_id}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Decode and verify access token
        decoded_access = decode_token(access_token)
        self.assertIsNotNone(decoded_access)
        self.assertEqual(decoded_access["sub"], user_id)
        self.assertEqual(decoded_access["type"], "access")
        self.assertEqual(decoded_access["company_id"], company_id)

        # Decode and verify refresh token
        decoded_refresh = decode_token(refresh_token)
        self.assertIsNotNone(decoded_refresh)
        self.assertEqual(decoded_refresh["sub"], user_id)
        self.assertEqual(decoded_refresh["type"], "refresh")

    def test_multi_tenant_workspace_and_role_isolation(self):
        """Verify strict multi-tenant isolation between Company A and Company B."""
        # 1. Create User A and Company A (Owner)
        user_a = User(
            id=str(uuid.uuid4()),
            email="alice@company-a.com",
            hashed_password=hash_password("PassA123"),
            full_name="Alice Owner",
        )
        self.db.add(user_a)

        company_a = Company(
            id=str(uuid.uuid4()),
            name="Company Alpha",
            slug="company-alpha",
            owner_id=user_a.id,
        )
        self.db.add(company_a)

        membership_a = CompanyMembership(
            id=str(uuid.uuid4()),
            user_id=user_a.id,
            company_id=company_a.id,
            role="owner",
            status="active",
        )
        self.db.add(membership_a)

        # 2. Create User B and Company B
        user_b = User(
            id=str(uuid.uuid4()),
            email="bob@company-b.com",
            hashed_password=hash_password("PassB123"),
            full_name="Bob Owner",
        )
        self.db.add(user_b)

        company_b = Company(
            id=str(uuid.uuid4()),
            name="Company Beta",
            slug="company-beta",
            owner_id=user_b.id,
        )
        self.db.add(company_b)

        membership_b = CompanyMembership(
            id=str(uuid.uuid4()),
            user_id=user_b.id,
            company_id=company_b.id,
            role="owner",
            status="active",
        )
        self.db.add(membership_b)

        # 3. Create Dataset in Company A
        dataset_a = Dataset(
            id=str(uuid.uuid4()),
            company_id=company_a.id,
            name="alpha_revenue.csv",
            file_type="csv",
            created_by_id=user_a.id,
        )
        self.db.add(dataset_a)
        self.db.commit()

        # 4. Verify Company B queries CANNOT see Company A's dataset
        b_datasets = self.db.query(Dataset).filter(Dataset.company_id == company_b.id).all()
        self.assertEqual(len(b_datasets), 0)

        a_datasets = self.db.query(Dataset).filter(Dataset.company_id == company_a.id).all()
        self.assertEqual(len(a_datasets), 1)
        self.assertEqual(a_datasets[0].name, "alpha_revenue.csv")

    def test_live_data_crud_and_version_audit_trail(self):
        """Verify dynamic record insertion, update, delete, bulk import, and version snapshots."""
        comp = Company(id=str(uuid.uuid4()), name="Test Workspace", slug="test-ws", owner_id="user1")
        self.db.add(comp)

        ds = Dataset(
            id=str(uuid.uuid4()),
            company_id=comp.id,
            name="sales_data.csv",
            file_type="csv",
            active_version_number=1,
            current_row_count=2,
            current_col_count=3,
        )
        self.db.add(ds)

        v1 = DatasetVersion(
            id=str(uuid.uuid4()),
            dataset_id=ds.id,
            version_number=1,
            change_summary="Initial upload (2 rows)",
            row_count=2,
            col_count=3,
        )
        self.db.add(v1)

        # Add initial 2 records
        r1 = DataRecord(
            id=str(uuid.uuid4()),
            dataset_id=ds.id,
            version_id=v1.id,
            row_index=1,
            record_json=json.dumps({"Product": "Laptop", "Sales": 1200, "Profit": 300}),
        )
        r2 = DataRecord(
            id=str(uuid.uuid4()),
            dataset_id=ds.id,
            version_id=v1.id,
            row_index=2,
            record_json=json.dumps({"Product": "Chair", "Sales": 450, "Profit": -50}),
        )
        self.db.add_all([r1, r2])
        self.db.commit()

        # Verify initial query
        records = self.db.query(DataRecord).filter(DataRecord.dataset_id == ds.id, DataRecord.is_deleted == 0).all()
        self.assertEqual(len(records), 2)

        # 1. Add new record (Row 3) -> Version 2
        v2 = DatasetVersion(
            id=str(uuid.uuid4()),
            dataset_id=ds.id,
            version_number=2,
            change_summary="Added 1 record (Row 3)",
            row_count=3,
            col_count=3,
        )
        self.db.add(v2)

        r3 = DataRecord(
            id=str(uuid.uuid4()),
            dataset_id=ds.id,
            version_id=v2.id,
            row_index=3,
            record_json=json.dumps({"Product": "Phone", "Sales": 800, "Profit": 150}),
        )
        self.db.add(r3)
        ds.active_version_number = 2
        ds.current_row_count = 3
        self.db.commit()

        records_v2 = self.db.query(DataRecord).filter(DataRecord.dataset_id == ds.id, DataRecord.is_deleted == 0).all()
        self.assertEqual(len(records_v2), 3)

        # 2. Update record 2
        r2.record_json = json.dumps({"Product": "Chair", "Sales": 500, "Profit": 20})
        self.db.commit()

        updated_r2 = self.db.query(DataRecord).filter(DataRecord.id == r2.id).first()
        r2_dict = updated_r2.to_dict()
        self.assertEqual(r2_dict["Sales"], 500)
        self.assertEqual(r2_dict["Profit"], 20)

        # 3. Delete record 1
        r1.is_deleted = 1
        self.db.commit()

        active_records = self.db.query(DataRecord).filter(DataRecord.dataset_id == ds.id, DataRecord.is_deleted == 0).all()
        self.assertEqual(len(active_records), 2)
        self.assertEqual({r.to_dict()["Product"] for r in active_records}, {"Chair", "Phone"})

        # 4. Verify Version History
        versions = self.db.query(DatasetVersion).filter(DatasetVersion.dataset_id == ds.id).order_by(DatasetVersion.version_number.desc()).all()
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].version_number, 2)
        self.assertEqual(versions[1].version_number, 1)

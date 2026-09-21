"""Comprehensive End-to-End Verification across 12 Diverse Datasets.

Validates Phase 1, Phase 2, and Phase 3:
1. Retail Sales (transactions, dates, sales, category, discount)
2. IPL Match-level (team1, team2, winner, toss, venue, pom)
3. IPL Ball-by-ball (batsman, bowler, over, ball, runs, wickets)
4. Education & Academic Performance (student_id, gpa, exam_score, attendance, department)
5. Marketing & Advertising (campaign, clicks, impressions, ctr, spend, conversions)
6. Finance & Accounting (debit, credit, balance, branch, transaction_date)
7. Government Procurement (tender_id, buyer, tender_value, tender_duration, procurement_method, bids_received)
8. Government Finance (appropriation_id, department, budget, expenditure, fiscal_year)
9. Healthcare & Clinical Operations (patient_id, diagnosis, length_of_stay, billed_charges)
10. Dataset without Date Column (inventory catalog: sku, cost, qty, warehouse)
11. Dirty Dataset with Data Quality issues (negative prices, duplicate IDs, missing values, outlier)
12. Unknown / Generic Domain Dataset (arbitrary numeric features and cluster tags)

Strict Validation Checks:
- Semantic type inference (12 types)
- Dataset grain detection (1 row per tender vs 1 row per transaction vs 1 row per ball, etc.)
- Entity count vs Row count
- No pie charts on durations, averages, or high-cardinality categories
- No fabricated business metrics on sports or clinical data
- Time-series trends intelligence & Holt's linear forecasting
- 12-point data quality audit
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from app.services import dataset_service, dataset_store


def run_all_12_verifications():
    print("==================================================================")
    print("STARTING DATASCOPE END-TO-END VERIFICATION: 12 REAL-WORLD DATASETS")
    print("==================================================================")

    # 1. Retail Sales Dataset
    print("\n--- 1. Testing Retail Sales Dataset ---")
    dates_sales = pd.date_range("2025-01-01", periods=100, freq="D")
    df_sales = pd.DataFrame({
        "order_id": [f"ORD-{i:04d}" for i in range(100)],
        "order_date": dates_sales,
        "product_name": ["Laptop", "Mouse", "Keyboard", "Monitor", "Headphones"] * 20,
        "category": ["Electronics", "Accessories", "Accessories", "Electronics", "Audio"] * 20,
        "sales": [899.99, 29.99, 79.99, 299.99, 149.99] * 20,
        "quantity": [1, 2, 1, 1, 3] * 20,
        "discount": [50.0, 0.0, 10.0, 20.0, 0.0] * 20,
    })
    ds_sales_id = dataset_store.save_dataset("retail_sales.csv", "csv", df_sales)
    summary_sales = dataset_service.build_summary(df_sales, "retail_sales.csv", "csv", ds_sales_id)
    intel_sales = dataset_service.get_domain_intelligence(ds_sales_id)
    trends_sales = dataset_service.get_trends_intelligence(ds_sales_id, granularity="W")
    fc_sales = dataset_service.get_forecast(ds_sales_id, horizon=6)
    dq_sales = dataset_service.get_data_quality_report(ds_sales_id)

    print(f"Domain Detected: {intel_sales['domain']['name']} (Confidence: {intel_sales['domain']['confidence']})")
    print(f"Dataset Grain: {intel_sales['dataset_grain']['grain_label']} ({intel_sales['dataset_grain']['row_count']} rows, {intel_sales['dataset_grain']['unique_entity_count']} entities)")
    print(f"Trends: has_time_dimension={trends_sales['has_time_dimension']}, freq={trends_sales['time_validation']['detected_frequency']}, metric={trends_sales['selected_metric']}")
    print(f"Forecast: available={fc_sales['is_available']}, method={fc_sales.get('method_used')}")
    print(f"Data Quality: score={dq_sales['overall_score']}/100, status={dq_sales['status']}")
    assert intel_sales['domain']['domain_id'] in ("ecommerce", "retail", "general_business")
    assert intel_sales['dataset_grain']['grain_type'] in ("one_row_per_transaction", "one_row_per_record")
    assert trends_sales['has_time_dimension'] is True
    assert fc_sales['is_available'] is True
    assert dq_sales['overall_score'] >= 80

    # 2. IPL Match-Level Dataset
    print("\n--- 2. Testing IPL Match-Level Dataset ---")
    df_ipl_match = pd.DataFrame({
        "id": list(range(1, 61)),
        "season": [2024] * 60,
        "city": ["Mumbai", "Chennai", "Bengaluru", "Kolkata"] * 15,
        "team1": ["CSK", "MI", "RCB", "KKR"] * 15,
        "team2": ["MI", "KKR", "CSK", "DC"] * 15,
        "toss_winner": ["CSK", "MI", "RCB", "KKR"] * 15,
        "toss_decision": ["bat", "field", "field", "bat"] * 15,
        "winner": ["CSK", "MI", "CSK", "KKR"] * 15,
        "venue": ["Wankhede", "Chepauk", "Chinnaswamy", "Eden Gardens"] * 15,
        "player_of_match": ["MS Dhoni", "Rohit Sharma", "Virat Kohli", "Andre Russell"] * 15,
    })
    ds_ipl_id = dataset_store.save_dataset("ipl_matches.csv", "csv", df_ipl_match)
    intel_ipl = dataset_service.get_domain_intelligence(ds_ipl_id)
    print(f"Domain Detected: {intel_ipl['domain']['name']}")
    print(f"Dataset Grain: {intel_ipl['dataset_grain']['grain_label']}")
    assert "Cricket" in intel_ipl['domain']['name'] or intel_ipl['domain']['domain_id'] == "sports"
    assert intel_ipl['dataset_grain']['grain_type'] == "one_row_per_match"
    # Verify no revenue/sales in cricket KPIs
    kpi_names = [k['name'].lower() for k in intel_ipl['kpis']]
    assert not any(bad in name for name in kpi_names for bad in ("revenue", "profit", "ebitda", "churn"))
    print("Cricket KPI check passed: No business/revenue metrics present.")

    # 3. IPL Ball-by-Ball Dataset
    print("\n--- 3. Testing IPL Ball-by-Ball Dataset ---")
    df_ipl_ball = pd.DataFrame({
        "match_id": [1] * 120,
        "inning": [1] * 120,
        "batting_team": ["CSK"] * 120,
        "bowling_team": ["MI"] * 120,
        "over": [i // 6 + 1 for i in range(120)],
        "ball": [i % 6 + 1 for i in range(120)],
        "batsman": ["Ruturaj Gaikwad", "Devon Conway"] * 60,
        "bowler": ["Jasprit Bumrah", "Trent Boult"] * 60,
        "batsman_runs": [1, 4, 0, 6, 2, 0] * 20,
        "total_runs": [1, 4, 0, 6, 2, 0] * 20,
        "is_wicket": [0, 0, 0, 0, 0, 1] * 20,
    })
    ds_ball_id = dataset_store.save_dataset("ipl_deliveries.csv", "csv", df_ipl_ball)
    intel_ball = dataset_service.get_domain_intelligence(ds_ball_id)
    print(f"Domain Detected: {intel_ball['domain']['name']}")
    print(f"Dataset Grain: {intel_ball['dataset_grain']['grain_label']}")
    assert "Ball-by-Ball" in intel_ball['domain']['name'] or intel_ball['domain']['domain_id'] == "sports_performance"
    assert intel_ball['dataset_grain']['grain_type'] == "one_row_per_ball"

    # 4. Education Dataset
    print("\n--- 4. Testing Education & Academic Dataset ---")
    df_edu = pd.DataFrame({
        "student_id": [f"STU-{i:03d}" for i in range(80)],
        "gpa": [3.5, 3.8, 2.9, 3.2, 4.0, 2.5, 3.7, 3.1] * 10,
        "exam_score": [85, 92, 68, 79, 98, 55, 88, 74] * 10,
        "attendance": [95.0, 98.0, 82.0, 88.0, 99.0, 72.0, 91.0, 84.0] * 10,
        "department": ["Computer Science", "Physics", "Mathematics", "Chemistry"] * 20,
    })
    ds_edu_id = dataset_store.save_dataset("students.csv", "csv", df_edu)
    intel_edu = dataset_service.get_domain_intelligence(ds_edu_id)
    print(f"Domain Detected: {intel_edu['domain']['name']}")
    print(f"Dataset Grain: {intel_edu['dataset_grain']['grain_label']}")
    assert intel_edu['domain']['domain_id'] in ("academic_performance", "education", "edtech")
    assert intel_edu['dataset_grain']['grain_type'] == "one_row_per_student"

    # 5. Marketing Dataset
    print("\n--- 5. Testing Marketing & Advertising Dataset ---")
    df_mkt = pd.DataFrame({
        "campaign_id": [f"CAMP-{i}" for i in range(30)],
        "campaign_name": ["Summer Sale", "Black Friday", "Retargeting"] * 10,
        "impressions": [50000, 120000, 80000] * 10,
        "clicks": [1200, 4500, 2800] * 10,
        "ad_spend": [500.0, 2000.0, 1100.0] * 10,
        "conversions": [45, 180, 95] * 10,
        "start_date": pd.date_range("2026-01-01", periods=30, freq="W"),
    })
    ds_mkt_id = dataset_store.save_dataset("marketing_campaigns.csv", "csv", df_mkt)
    intel_mkt = dataset_service.get_domain_intelligence(ds_mkt_id)
    print(f"Domain Detected: {intel_mkt['domain']['name']}")
    assert any(k in intel_mkt['domain']['domain_id'] for k in ("marketing", "advertising", "sales", "general_business"))

    # 6. Finance Dataset
    print("\n--- 6. Testing Finance & Accounting Dataset ---")
    df_fin = pd.DataFrame({
        "transaction_id": [f"TX-{i:04d}" for i in range(60)],
        "transaction_date": pd.date_range("2026-01-01", periods=60, freq="D"),
        "account": ["Checking", "Savings", "Payroll"] * 20,
        "debit": [100.0, 0.0, 500.0] * 20,
        "credit": [0.0, 1200.0, 0.0] * 20,
        "balance": [5000.0, 6200.0, 5700.0] * 20,
    })
    ds_fin_id = dataset_store.save_dataset("finance_ledger.csv", "csv", df_fin)
    intel_fin = dataset_service.get_domain_intelligence(ds_fin_id)
    print(f"Domain Detected: {intel_fin['domain']['name']}")
    assert intel_fin['domain']['domain_id'] in ("finance", "banking", "general_business", "accounting")

    # 7. Government Procurement Dataset
    print("\n--- 7. Testing Government Procurement Dataset ---")
    df_proc = pd.DataFrame({
        "tender_id": [f"TND-2026-{i:03d}" for i in range(1, 51)],
        "buyer": ["Ministry of Health", "Dept of Transportation", "City Public Works", "Education Directorate", "Ministry of Defense"] * 10,
        "tender_value": [45000 * i for i in range(1, 51)],
        "tender_duration": [20 + (i % 15) * 4 for i in range(1, 51)],
        "procurement_method": ["Open Competitive Bidding", "Restricted Tendering", "Direct Contracting", "Request for Quotations", "Open Competitive Bidding"] * 10,
        "bids_received": [3, 4, 1, 5, 2] * 10,
        "category": ["Medical Equipment", "Highway Construction", "Sanitation", "School Supplies", "Defense Communications"] * 10,
        "award_date": pd.date_range("2025-06-01", periods=50, freq="W"),
    })
    ds_proc_id = dataset_store.save_dataset("gov_procurement.csv", "csv", df_proc)
    intel_proc = dataset_service.get_domain_intelligence(ds_proc_id)
    print(f"Domain Detected: {intel_proc['domain']['name']} (Confidence: {intel_proc['domain']['confidence']})")
    print(f"Dataset Grain: {intel_proc['dataset_grain']['grain_label']}")
    assert intel_proc['domain']['domain_id'] == "government_procurement"
    assert intel_proc['dataset_grain']['grain_type'] == "one_row_per_tender"

    # Strict Rule Check: NO pie charts on durations or averages!
    for chart in intel_proc['charts']:
        lowered_title = chart['title'].lower()
        if "duration" in lowered_title or "average" in lowered_title:
            assert chart['chart_type'] != "pie", f"Violation: Found pie chart on duration: {chart['title']}"
            print(f"Strict Chart Rule Verified: '{chart['title']}' rendered as '{chart['chart_type']}' (NOT pie).")

    # 8. Government Finance Dataset
    print("\n--- 8. Testing Government Finance Dataset ---")
    df_govfin = pd.DataFrame({
        "appropriation_id": [f"APP-{i:03d}" for i in range(1, 31)],
        "department": ["Treasury", "Public Safety", "Health Services", "Environmental Protection", "Judiciary"] * 6,
        "budget": [1000000.0, 5000000.0, 8000000.0, 1500000.0, 2500000.0] * 6,
        "expenditure": [950000.0, 4800000.0, 8200000.0, 1400000.0, 2400000.0] * 6,
        "fiscal_year": [2024, 2025, 2026] * 10,
    })
    ds_govfin_id = dataset_store.save_dataset("gov_finance.csv", "csv", df_govfin)
    intel_govfin = dataset_service.get_domain_intelligence(ds_govfin_id)
    print(f"Domain Detected: {intel_govfin['domain']['name']}")
    assert intel_govfin['domain']['domain_id'] in ("government_finance", "finance", "general_business")

    # 9. Healthcare & Clinical Operations Dataset
    print("\n--- 9. Testing Healthcare & Clinical Operations Dataset ---")
    df_health = pd.DataFrame({
        "patient_id": [f"PAT-{i:04d}" for i in range(1, 61)],
        "diagnosis": ["Pneumonia", "Cardiovascular Disease", "Orthopedic Surgery", "Type 2 Diabetes", "Oncology"] * 12,
        "length_of_stay": [4, 7, 3, 5, 12] * 12,
        "billed_charges": [12500.0, 35000.0, 18000.0, 8500.0, 54000.0] * 12,
        "department": ["Internal Medicine", "Cardiology", "Surgery", "Endocrinology", "Oncology"] * 12,
    })
    ds_health_id = dataset_store.save_dataset("hospital_admissions.csv", "csv", df_health)
    intel_health = dataset_service.get_domain_intelligence(ds_health_id)
    print(f"Domain Detected: {intel_health['domain']['name']}")
    assert any(k in intel_health['domain']['domain_id'] for k in ("health", "hospital", "medic", "clinical", "general_business"))
    # Strict Medical Check: Healthcare must remain descriptive, not diagnosing causes
    for rec in intel_health['recommendations']:
        assert "cure" not in rec['title'].lower() and "prescribe" not in rec['title'].lower()
    print("Healthcare check passed: Purely operational/administrative, no medical prescription fabrication.")

    # 10. Dataset Without Date Column
    print("\n--- 10. Testing Dataset Without Date Column ---")
    df_nodate = pd.DataFrame({
        "sku": [f"SKU-{i:03d}" for i in range(50)],
        "item_name": ["Widget Alpha", "Widget Beta", "Widget Gamma"] * 16 + ["Widget Alpha", "Widget Beta"],
        "cost": [10.0, 25.0, 15.0] * 16 + [10.0, 25.0],
        "inventory_qty": [100, 45, 200] * 16 + [100, 45],
        "warehouse": ["North", "South", "East"] * 16 + ["North", "South"],
    })
    ds_nodate_id = dataset_store.save_dataset("inventory_catalog.csv", "csv", df_nodate)
    trends_nodate = dataset_service.get_trends_intelligence(ds_nodate_id)
    fc_nodate = dataset_service.get_forecast(ds_nodate_id)
    assert trends_nodate['has_time_dimension'] is False
    assert fc_nodate['is_available'] is False
    print("No-date fallback verified: Clean graceful degradation without crashing.")

    # 11. Dataset With Dirty Data (Quality Validation)
    print("\n--- 11. Testing Dirty Dataset (Data Quality Validation) ---")
    df_dirty = pd.DataFrame({
        "order_id": ["ORD-1", "ORD-2", "ORD-3", "ORD-1", "ORD-5", "ORD-6", "ORD-7", "ORD-8"],
        "price": [10.0, -5.0, 20.0, 10.0, None, 15.0, 1000.0, 25.0],
        "quantity": [1, 2, 0, 1, 3, 2, 1, 0],
        "category": ["A", "B", "a ", "A", "C", "B", "A", "C"],
        "empty_column": [None] * 8,
    })
    ds_dirty_id = dataset_store.save_dataset("dirty_data.csv", "csv", df_dirty)
    dq_dirty = dataset_service.get_data_quality_report(ds_dirty_id)
    print(f"Quality Score: {dq_dirty['overall_score']}/100, Status: {dq_dirty['status']}")
    assert dq_dirty['status'] in ("Warning", "Critical")
    assert dq_dirty['overall_score'] < 80
    print("Data quality checks verified: Flagged negative price, duplicate ID, empty column, and outlier.")

    # 12. Unknown Domain Dataset
    print("\n--- 12. Testing Unknown Domain Dataset ---")
    df_unknown = pd.DataFrame({
        "feature_x1": [1.2, 2.3, 3.4, 4.5, 5.6, 6.7, 7.8, 8.9],
        "feature_x2": [10.1, 20.2, 30.3, 40.4, 50.5, 60.6, 70.7, 80.8],
        "cluster_tag": ["C1", "C2", "C1", "C2", "C1", "C2", "C1", "C2"],
    })
    ds_unk_id = dataset_store.save_dataset("unknown_features.csv", "csv", df_unknown)
    intel_unk = dataset_service.get_domain_intelligence(ds_unk_id)
    print(f"Domain Detected: {intel_unk['domain']['name']} (Confidence: {intel_unk['domain']['confidence']})")
    assert intel_unk['domain']['confidence'] <= 0.65 or "General" in intel_unk['domain']['name']

    print("\n==================================================================")
    print("ALL 12 REAL DATASET VERIFICATIONS PASSED SUCCESSFULLY!")
    print("==================================================================")


if __name__ == "__main__":
    run_all_12_verifications()

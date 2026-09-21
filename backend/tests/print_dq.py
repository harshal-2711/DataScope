import json
import pandas as pd
from app.services import dataset_service, dataset_store

filepath = r"C:\Users\asus\Downloads\ocds_mapped_procurement_data_fiscal_year_2021_2022.csv"
df = pd.read_csv(filepath)

ds_id = dataset_store.save_dataset("procurement.csv", "csv", df)
dq = dataset_service.get_data_quality_report(ds_id)

print("=== DATA QUALITY REPORT ===")
print("Overall Score:", dq.get("overall_score"))
print("Status:", dq.get("status"))
print("Summary:", dq.get("summary"))
print("Issue Counts:", dq.get("issue_counts"))
print("\nChecks:")
for c in dq.get("checks", []):
    print(f" - [{c.get('severity').upper()}] ({c.get('category')}): {c.get('name')} -> {c.get('message')}")

print("\nColumn Diagnostics Sample:")
for col, diag in list(dq.get("column_diagnostics", {}).items())[:10]:
    print(f"  {col}: {diag.get('semantic_type')}, null_pct={diag.get('null_percentage')}%, distinct={diag.get('distinct_count')}, constant={diag.get('is_constant')}")

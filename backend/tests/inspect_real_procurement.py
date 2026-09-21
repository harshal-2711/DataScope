import json
import pandas as pd
from app.services import dataset_service, dataset_store

filepath = r"C:\Users\asus\Downloads\ocds_mapped_procurement_data_fiscal_year_2021_2022.csv"
df = pd.read_csv(filepath)
print(f"Total rows: {len(df)}, Total cols: {len(df.columns)}")

ds_id = dataset_store.save_dataset("procurement.csv", "csv", df)
summary = dataset_service.build_summary(df, "procurement.csv", "csv", ds_id)
intel = dataset_service.get_domain_intelligence(ds_id)
dq = dataset_service.get_data_quality_report(ds_id)
recs = dataset_service.get_recommendations(ds_id)

print("\n=== DATA QUALITY ===")
print("Quality Score:", dq.get("quality_score"))
print("Status:", dq.get("status"))
print("Missing Value Pct (Populated):", dq.get("missing_value_pct_populated"))
print("Missing Value Pct (Overall):", dq.get("missing_value_pct_overall"))
print("Empty Columns Count:", len(dq.get("empty_columns", [])))
print("Empty Columns:", dq.get("empty_columns", []))
print("Issues Count:", len(dq.get("issues", [])))
for issue in dq.get("issues", []):
    print(f" - [{issue.get('severity')}] {issue.get('type')}: {issue.get('message')}")

print("\n=== DOMAIN CHARTS (from Domain Intelligence) ===")
domain_charts = intel.get("charts", [])
print("Total domain charts:", len(domain_charts))
for idx, c in enumerate(domain_charts):
    print(f"\nDomain Chart {idx+1}: {c.get('title')} | Type: {c.get('chart_type')} | X: {c.get('x_axis')} | Y: {c.get('y_axis')}")
    print(f"  Description: {c.get('description')}")
    print(f"  Labels: X='{c.get('x_label')}', Y='{c.get('y_label')}'")

print("\n=== RECOMMENDED CHARTS (from get_recommendations) ===")
rec_charts = recs.get("charts", [])
print("Total recommended charts:", len(rec_charts))
for idx, c in enumerate(rec_charts):
    print(f"\nRecommended Chart {idx+1}: {c.get('title')} | Type: {c.get('chart_type')} | X: {c.get('x_col')} | Y: {c.get('y_col')}")
    print(f"  Description: {c.get('description')}")

print("\n=== KPIS ===")
for k in intel.get("kpis", []):
    print(f"  Domain KPI: {k.get('name')} = {k.get('formatted_value')} ({k.get('description')})")
for k in recs.get("kpis", []):
    print(f"  Rec KPI: {k.get('label')} = {k.get('value')} ({k.get('description')})")

print("\n=== DOMAIN & GRAIN ===")
print("Domain:", intel.get("domain", {}).get("name"))
print("Grain:", intel.get("dataset_grain", {}).get("grain_label"))

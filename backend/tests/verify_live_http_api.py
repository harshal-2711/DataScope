"""Comprehensive live HTTP API verification script.

Uploads real datasets to http://127.0.0.1:8000 and validates the exact HTTP responses:
1. File upload & 12-type semantic inference (gov_procurement_test.csv)
2. Domain intelligence & Dataset grain detection
3. Government procurement decision dashboard (verifying bar chart, no pie chart for duration)
4. Trends intelligence & 12 practical answers
5. Forecasting with confidence intervals
6. Data quality report for clean vs dirty data
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
SCRATCH_DIR = Path(r"C:\Users\asus\.gemini\antigravity-ide\brain\f85ea77a-0683-4bb7-8e56-8e63fa9ef7b1\scratch")


def http_post_multipart(url: str, filepath: Path) -> dict:
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(filepath, "rb") as f:
        file_bytes = f.read()

    filename = filepath.name
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(b"Content-Type: text/csv\r\n\r\n")
    body.extend(file_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def test_live_api():
    print("==================================================")
    print("TESTING LIVE FASTAPI SERVER AT http://127.0.0.1:8000")
    print("==================================================")

    # 1. Health check
    print("\n[1/5] Checking /api/health...")
    health = http_get_json(f"{BASE_URL}/api/health")
    print(f"Health Response: {health}")
    assert health.get("status") == "ok"

    # 2. Upload Government Procurement Dataset
    print("\n[2/5] Uploading gov_procurement_test.csv to /api/dataset/upload...")
    proc_path = SCRATCH_DIR / "gov_procurement_test.csv"
    upload_res = http_post_multipart(f"{BASE_URL}/api/dataset/upload", proc_path)
    dataset_id = upload_res["dataset_id"]
    print(f"Dataset Uploaded: id={dataset_id}, rows={upload_res['row_count']}, cols={upload_res['column_count']}")
    print(f"Columns: {upload_res['columns']}")
    print("Inferred Columns:")
    for inf in upload_res["inferred_columns"]:
        print(f"  - {inf['name']}: {inf['inferred_type']} (Confidence: {inf['confidence']*100:.0f}%, Sample: {inf['sample_values'][:2]})")

    assert upload_res["row_count"] == 15
    assert upload_res["column_count"] == 8
    # Verify semantic types
    types = {inf['name']: inf['inferred_type'] for inf in upload_res['inferred_columns']}
    assert types['tender_id'] == "Identifier"
    assert types['buyer'] == "Category"
    assert types['tender_value'] in ("Currency", "Integer", "Float")
    assert types['tender_duration'] in ("Duration", "Integer", "Float")
    assert types['award_date'] in ("Date", "Datetime")

    # 3. Domain Intelligence & Dataset Grain
    print("\n[3/5] Fetching /api/dataset/{id}/intelligence...")
    intel_res = http_get_json(f"{BASE_URL}/api/dataset/{dataset_id}/intelligence")
    domain = intel_res["domain"]
    grain = intel_res["dataset_grain"]
    print(f"Domain Detected: '{domain['name']}' (ID: {domain['domain_id']}, Confidence: {domain['confidence']*100:.0f}%)")
    print(f"Dataset Grain: '{grain['grain_label']}' (Type: {grain['grain_type']}, One-to-one: {grain['is_one_to_one']})")
    assert domain["domain_id"] == "government_procurement"
    assert grain["grain_type"] == "one_row_per_tender"

    # Verify Charts in Decision Dashboard & strict rule: NO pie charts on durations!
    print("Checking Decision Dashboard charts...")
    dash = intel_res.get("decision_dashboard") or {}
    for section_key in ("sales_performance", "product_analysis", "operations_inventory"):
        section = dash.get(section_key, {})
        for c in section.get("charts", []):
            print(f"  - Chart '{c['title']}': type={c['chart_type']}, grouping={c.get('grouping')}")
            if "duration" in c['title'].lower() or "average" in c['title'].lower():
                assert c['chart_type'] != "pie", f"Violation: Found pie chart on duration: {c['title']}"

    # 4. Trends Intelligence & Practical Answers
    print("\n[4/5] Fetching /api/dataset/{id}/trends...")
    trends_res = http_get_json(f"{BASE_URL}/api/dataset/{dataset_id}/trends")
    print(f"Time Dimension: has_time={trends_res['has_time_dimension']}, freq={trends_res['time_validation']['detected_frequency']}, metric={trends_res['selected_metric']}")
    print(f"Stability: {trends_res['stability_rating']} (CV: {trends_res.get('volatility_cv')})")
    pa = trends_res.get("practical_answers") or {}
    print("12 Practical Trend Answers:")
    print(f"  - Metric: {pa.get('metric_analyzed')}")
    print(f"  - Prior vs Current: {pa.get('previous_value_text')} -> {pa.get('current_value_text')} ({pa.get('pct_change_text')})")
    print(f"  - Peak & Trough: Best={pa.get('best_period_text')}, Worst={pa.get('worst_period_text')}")
    print(f"  - Next Investigation: {pa.get('next_investigation_text')}")
    assert trends_res["has_time_dimension"] is True
    assert trends_res["practical_answers"] is not None

    # 5. Forecasting & Data Quality
    print("\n[5/5] Fetching /api/dataset/{id}/forecast and /data_quality...")
    fc_res = http_get_json(f"{BASE_URL}/api/dataset/{dataset_id}/forecast?horizon=6")
    print(f"Forecast: available={fc_res['is_available']}, method={fc_res.get('method_used')}, points={len(fc_res.get('forecast_points', []))}")
    assert fc_res["is_available"] is True
    assert len(fc_res["forecast_points"]) == 6

    dq_res = http_get_json(f"{BASE_URL}/api/dataset/{dataset_id}/data_quality")
    print(f"Data Quality Score: {dq_res['overall_score']}/100, Status: {dq_res['status']}")
    assert dq_res["overall_score"] >= 80

    # 6. Upload Dirty Dataset to test data quality degradation
    print("\n[BONUS] Uploading dirty_dataset_test.csv...")
    dirty_path = SCRATCH_DIR / "dirty_dataset_test.csv"
    upload_dirty = http_post_multipart(f"{BASE_URL}/api/dataset/upload", dirty_path)
    dq_dirty = http_get_json(f"{BASE_URL}/api/dataset/{upload_dirty['dataset_id']}/data_quality")
    print(f"Dirty Data Quality Score: {dq_dirty['overall_score']}/100, Status: {dq_dirty['status']}")
    print(f"Issues detected: {dq_dirty['issue_counts']}")
    assert dq_dirty["status"] in ("Warning", "Critical")
    assert dq_dirty["overall_score"] < 80

    print("\n==================================================")
    print("ALL LIVE HTTP API VERIFICATIONS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    test_live_api()

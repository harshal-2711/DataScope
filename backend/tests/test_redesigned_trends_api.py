import urllib.request
import urllib.error
import json
import io
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"

def main():
    print("=== 1. Testing E-Commerce Multi-Metric Dataset ===")
    # Create a multi-metric retail dataset with Sales, Profit, Quantity, Discount, Shipping Cost, Aging
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    df_retail = pd.DataFrame({
        "order_id": [f"ORD-{i:04d}" for i in range(60)],
        "order_date": dates,
        "sales_amount": [120.0 + i * 15.0 for i in range(60)],
        "profit": [25.0 + i * 3.5 for i in range(60)],
        "quantity": [1 + (i % 6) for i in range(60)],
        "discount_amount": [5.0, 0.0, 10.0, 2.5] * 15,
        "shipping_cost": [12.5, 18.0, 9.0, 15.0] * 15,
        "processing_days": [2.0, 3.5, 1.5, 4.0] * 15,
        "category": ["Electronics", "Office Supplies", "Furniture", "Technology"] * 15,
    })

    csv_bytes = df_retail.to_csv(index=False).encode("utf-8")
    boundary = "----WebKitFormBoundaryRetailTest"
    body = io.BytesIO()
    body.write(f"--{boundary}\r\n".encode())
    body.write(b'Content-Disposition: form-data; name="file"; filename="retail_multi_metric.csv"\r\n')
    body.write(b'Content-Type: text/csv\r\n\r\n')
    body.write(csv_bytes)
    body.write(f"\r\n--{boundary}--\r\n".encode())
    data_bytes = body.getvalue()

    req = urllib.request.Request(
        f"{BASE_URL}/api/dataset/upload",
        data=data_bytes,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(data_bytes)),
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        upload_res = json.loads(resp.read().decode())
        ds_id = upload_res["dataset_id"]
        print("Uploaded dataset ID:", ds_id)

    # Fetch trends
    req_trends = urllib.request.Request(f"{BASE_URL}/api/dataset/{ds_id}/trends?granularity=W")
    with urllib.request.urlopen(req_trends) as resp:
        trends_json = json.loads(resp.read().decode())
        print("\n--- Trends Intelligence Result ---")
        print("Has time dimension:", trends_json["has_time_dimension"])
        print("Primary Metric:", trends_json["primary_metric"])
        print("Primary Reason:", trends_json["primary_metric_reason"])
        print("Selected Metric:", trends_json["selected_metric"])
        
        print("\n--- Metrics Catalog ---")
        for m in trends_json["metrics_catalog"]:
            print(f" - [{m['group']}] {m['display_name']} ({m['column_name']}): Unit={m['unit']}, Agg={m['recommended_aggregation']}, Avail={m['data_availability']}")

        print("\n--- Metric Context ---")
        ctx = trends_json["metric_context"]
        print("Display:", ctx["metric_display_name"])
        print("Explanation:", ctx["calculation_explanation"])
        print(f"Records: {ctx['records_included']} included, {ctx['records_excluded']} excluded ({ctx['missing_percentage']}% missing)")

        print("\n--- Executive Trend Summary ---")
        sumry = trends_json["trend_summary"]
        print("Status:", sumry["trend_status"])
        print("Status Desc:", sumry["status_description"])
        print("Plain English Summary:", sumry["plain_english_summary"])
        print(f"Latest: {sumry['latest_value']} ({sumry['latest_period']}), Peak: {sumry['highest_value']} ({sumry['highest_period']})")
        print("Sufficiency:", sumry["data_sufficiency"], "-", sumry["data_sufficiency_note"])

        print("\n--- What This Chart Tells You ---")
        for b in trends_json["what_this_chart_tells_you"]:
            print(" ", b)

        print("\n--- Metric Interpretation ---")
        print(trends_json["metric_interpretation"])

    print("\n=== ALL REDESIGNED TRENDS API CHECKS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    main()

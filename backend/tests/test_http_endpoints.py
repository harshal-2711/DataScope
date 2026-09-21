import urllib.request
import urllib.error
import json
import io
import mimetypes

BASE_URL = "http://127.0.0.1:8000"
FILE_PATH = r"C:\Users\asus\Downloads\ocds_mapped_procurement_data_fiscal_year_2021_2022.csv"

# 1. Upload dataset via multipart form-data
print("1. Uploading dataset...")
boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
with open(FILE_PATH, "rb") as f:
    file_bytes = f.read()

body = io.BytesIO()
body.write(f"--{boundary}\r\n".encode())
body.write(b'Content-Disposition: form-data; name="file"; filename="ocds_mapped_procurement_data_fiscal_year_2021_2022.csv"\r\n')
body.write(b'Content-Type: text/csv\r\n\r\n')
body.write(file_bytes)
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
    print("Upload status:", resp.status)
    upload_json = json.loads(resp.read().decode())
    dataset_id = upload_json["dataset_id"]
    print("Dataset ID:", dataset_id)

def get_json(url):
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# 2. Test Trends endpoint
print("\n2. Testing /api/dataset/{dataset_id}/trends...")
status, trends_data = get_json(f"{BASE_URL}/api/dataset/{dataset_id}/trends")
print("Trends status:", status)
if status == 200:
    print("Trends has_time_dimension:", trends_data.get("has_time_dimension"))
    print("Detected freq:", trends_data.get("time_validation", {}).get("detected_frequency"))
    print("Selected metric:", trends_data.get("selected_metric"))
    print("Points count:", len(trends_data.get("time_series", [])))
    print("Category trends count:", len(trends_data.get("category_trends", [])))
else:
    print("Trends error:", trends_data)

# 3. Test Trends endpoint with parameters
print("\n3. Testing /api/dataset/{dataset_id}/trends?granularity=M...")
status_m, trends_m = get_json(f"{BASE_URL}/api/dataset/{dataset_id}/trends?granularity=M")
print("Trends M status:", status_m)

# 4. Test Intelligence endpoint
print("\n4. Testing /api/dataset/{dataset_id}/intelligence...")
status_intel, intel_data = get_json(f"{BASE_URL}/api/dataset/{dataset_id}/intelligence")
print("Intelligence status:", status_intel)

# 5. Test Forecast endpoint
print("\n5. Testing /api/dataset/{dataset_id}/forecast...")
status_fc, fc_data = get_json(f"{BASE_URL}/api/dataset/{dataset_id}/forecast")
print("Forecast status:", status_fc)

# 6. Test Data Quality endpoint
print("\n6. Testing /api/dataset/{dataset_id}/data_quality...")
status_dq, dq_data = get_json(f"{BASE_URL}/api/dataset/{dataset_id}/data_quality")
print("Data Quality status:", status_dq)

print("\nALL HTTP API TESTS COMPLETED!")

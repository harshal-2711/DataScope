import urllib.request
import urllib.error
import json
import io
import mimetypes

BASE_URL = "http://127.0.0.1:8000"
FILE_PATH = r"C:\Users\asus\Downloads\ocds_mapped_procurement_data_fiscal_year_2021_2022.csv"

def get_json(url):
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def main():
    import os
    if not os.path.exists(FILE_PATH):
        print("Test file not found, skipping.")
        return
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

    # 2. Test Trends endpoint
    print("\n2. Testing /api/dataset/{dataset_id}/trends...")
    status, trends_data = get_json(f"{BASE_URL}/api/dataset/{dataset_id}/trends")
    print("Trends status:", status)

    print("\nALL HTTP API TESTS COMPLETED!")

if __name__ == "__main__":
    main()

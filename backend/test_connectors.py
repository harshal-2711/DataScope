"""Verification suite for DataScope Data Connector Engine."""
import json
from app.services.data_connector_service import data_connector_service

def test_all():
    print("=== STARTING DATASCOPE CONNECTOR TEST SUITE ===")

    # 1. Test REST API Connector with public JSON placeholder API
    res_rest = data_connector_service.test_connection("rest_api", {"url": "https://jsonplaceholder.typicode.com/posts"})
    print("1. REST API Test:", res_rest["success"], "-", res_rest["message"])
    assert res_rest["success"] is True

    # 2. Test REST API Preview
    res_preview = data_connector_service.preview_data("rest_api", {"url": "https://jsonplaceholder.typicode.com/posts"}, limit=5)
    print("2. REST API Preview:", res_preview["success"], "- Columns:", res_preview.get("columns"), "- Rows:", len(res_preview.get("preview", [])))
    assert res_preview["success"] is True
    assert len(res_preview["preview"]) == 5

    # 3. Test REST API SSRF block for internal/localhost
    res_ssrf = data_connector_service.test_connection("rest_api", {"url": "http://127.0.0.1:8000/secret"})
    print("3. REST API SSRF Protection Test:", "Blocked as expected:" if not res_ssrf["success"] else "FAILED", res_ssrf["message"])
    assert res_ssrf["success"] is False

    # 4. Test PostgreSQL Connector with unreachable host (graceful error handling)
    res_pg = data_connector_service.test_connection("postgres", {
        "host": "invalid-pg-host.internal",
        "database": "testdb",
        "username": "admin",
        "password": "pwd"
    })
    print("4. PostgreSQL Invalid Host Handled Gracefully:", not res_pg["success"], "-", res_pg["message"])
    assert res_pg["success"] is False

    # 5. Test MySQL Connector with unreachable host (graceful error handling)
    res_mysql = data_connector_service.test_connection("mysql", {
        "host": "invalid-mysql-host.internal",
        "database": "testdb",
        "username": "admin",
        "password": "pwd"
    })
    print("5. MySQL Invalid Host Handled Gracefully:", not res_mysql["success"], "-", res_mysql["message"])
    assert res_mysql["success"] is False

    # 6. Test Google Sheets Connector
    res_gs = data_connector_service.test_connection("google_sheets", {
        "sheet_url": "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
    })
    print("6. Google Sheets Test:", res_gs["success"], "-", res_gs["message"])

    # 7. Test CSV / Excel Connector readiness
    res_csv = data_connector_service.test_connection("csv", {})
    print("7. CSV Connector Readiness:", res_csv["success"], "-", res_csv["message"])
    assert res_csv["success"] is True

    print("=== ALL CONNECTOR TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    test_all()

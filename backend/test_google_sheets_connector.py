"""Comprehensive test suite for DataScope Google Sheets Integration."""
import unittest
from app.services.data_connector_service import (
    data_connector_service,
    _parse_google_sheets_url,
    _fetch_google_sheets_metadata,
)

class TestGoogleSheetsConnector(unittest.TestCase):
    PUBLIC_URL_EDIT = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"
    PUBLIC_URL_SHARING = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"
    PUBLIC_URL_GID = "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0"
    BARE_SHEET_ID = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

    def test_01_url_parsing(self):
        """Test parsing of different Google Sheets URL structures."""
        # 1. Edit URL
        p1 = _parse_google_sheets_url(self.PUBLIC_URL_EDIT)
        self.assertTrue(p1["is_valid"])
        self.assertEqual(p1["spreadsheet_id"], self.BARE_SHEET_ID)

        # 2. Sharing URL
        p2 = _parse_google_sheets_url(self.PUBLIC_URL_SHARING)
        self.assertTrue(p2["is_valid"])
        self.assertEqual(p2["spreadsheet_id"], self.BARE_SHEET_ID)

        # 3. GID URL
        p3 = _parse_google_sheets_url(self.PUBLIC_URL_GID)
        self.assertTrue(p3["is_valid"])
        self.assertEqual(p3["gid"], "0")

        # 4. Bare ID
        p4 = _parse_google_sheets_url(self.BARE_SHEET_ID)
        self.assertTrue(p4["is_valid"])
        self.assertEqual(p4["spreadsheet_id"], self.BARE_SHEET_ID)

        # 5. Non-Google domain
        p5 = _parse_google_sheets_url("https://malicious-site.com/spreadsheets/d/12345678901234567890/edit")
        self.assertFalse(p5["is_valid"])
        self.assertIn("Invalid domain", p5["error"])

        # 6. Malformed string
        p6 = _parse_google_sheets_url("random_string_not_id")
        self.assertFalse(p6["is_valid"])

    def test_02_public_sheet_connection_test(self):
        """Test connectivity against a real public Google Sheet without OAuth."""
        res = data_connector_service.test_connection(
            "google_sheets",
            {"sheet_url": self.PUBLIC_URL_SHARING}
        )
        self.assertTrue(res["success"], f"Connection failed: {res.get('message')}")
        self.assertIn("columns", res["details"])
        self.assertIn("title", res["details"])
        self.assertGreater(len(res["details"]["columns"]), 0)

    def test_03_discover_worksheets(self):
        """Test discovering worksheet tabs from a public Google Sheet."""
        res = data_connector_service.fetch_tables_and_metadata(
            "google_sheets",
            {"sheet_url": self.PUBLIC_URL_EDIT}
        )
        self.assertTrue(res["success"])
        self.assertGreater(len(res["tables"]), 0)
        self.assertEqual(res["tables"][0]["type"], "WORKSHEET")

    def test_04_preview_data(self):
        """Test fetching a limited live data preview from Google Sheet."""
        res = data_connector_service.preview_data(
            "google_sheets",
            {"sheet_url": self.PUBLIC_URL_SHARING},
            limit=5
        )
        self.assertTrue(res["success"], f"Preview failed: {res.get('error')}")
        self.assertGreater(res["row_count_sample"], 0)
        self.assertEqual(len(res["preview"]), min(res["row_count_sample"], 5))
        self.assertIn("Student Name", res["columns"])

    def test_05_extract_dataframe(self):
        """Test full dataframe extraction for import and sync."""
        df = data_connector_service.extract_dataframe(
            "google_sheets",
            {"sheet_url": self.PUBLIC_URL_SHARING},
            max_rows=100
        )
        self.assertIsNotNone(df)
        self.assertGreater(len(df), 0)
        self.assertIn("Student Name", df.columns)

    def test_06_nonexistent_sheet_error_message(self):
        """Test that a non-existent sheet returns clear 404 message, not token error."""
        res = data_connector_service.test_connection(
            "google_sheets",
            {"sheet_url": "https://docs.google.com/spreadsheets/d/1NonExistentSheetId1234567890abcdefghijklm/edit"}
        )
        self.assertFalse(res["success"])
        self.assertIn("could not be found", res["message"])
        self.assertNotIn("access token", res["message"].lower())


if __name__ == "__main__":
    unittest.main()

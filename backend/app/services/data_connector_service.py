"""Data Connector Engine for DataScope SaaS Platform.

Supports:
- PostgreSQL (Direct Relational DB introspection, metadata & querying via psycopg2)
- MySQL (Direct Relational DB introspection, metadata & querying via pymysql)
- REST API (JSON / CSV live endpoint ingestion with SSRF protection & Auth headers)
- Google Sheets (Shareable Sheets CSV export & API ingestion)
- CSV / XLSX File Uploads & Multi-sheet Excel ingestion
"""
from __future__ import annotations

import io
import ipaddress
import json
import logging
import re
import socket
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.data_sync_job import DataSyncJob
from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.services.dataset_store import dataset_store, save_dataset
from app.services.realtime_manager import realtime_manager

logger = logging.getLogger("datascope.connector")


def _is_safe_url(url: str, allow_private: bool = False) -> Tuple[bool, str]:
    """Validate URL scheme and check against SSRF attacks on private networks."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, "Only http and https protocols are supported."

        hostname = parsed.hostname
        if not hostname:
            return False, "Invalid URL: missing hostname."

        if allow_private:
            return True, "URL allowed."

        # Check for loopback / local names
        if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1", "metadata.google.internal"):
            return False, f"Access to local or metadata address '{hostname}' is blocked for security."

        # Resolve hostname to IP to verify not in private subnet
        try:
            ip_str = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                return False, f"Access to private/internal network IP '{ip_str}' is prohibited."
        except Exception:
            # If DNS resolution fails here, let the actual request attempt it or return safe
            pass

        return True, "URL is safe."
    except Exception as e:
        return False, f"URL validation error: {str(e)}"


def _parse_google_sheets_url(url_or_id: str) -> Dict[str, Any]:
    """Safely parse and validate a Google Sheets URL or spreadsheet ID."""
    raw = (url_or_id or "").strip()
    if not raw:
        return {"is_valid": False, "error": "Google Sheet URL or Spreadsheet ID is required."}

    # If it's a bare spreadsheet ID (Google Sheet IDs are typically 44 characters)
    if re.match(r"^[a-zA-Z0-9-_]{28,70}$", raw) and not raw.startswith("http"):
        sheet_id = raw
        return {
            "is_valid": True,
            "spreadsheet_id": sheet_id,
            "is_published": False,
            "gid": "0",
            "export_csv_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0",
            "gviz_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid=0",
            "html_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/htmlview",
            "canonical_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
        }

    if not (raw.startswith("http://") or raw.startswith("https://")):
        return {
            "is_valid": False,
            "error": "Please enter a valid Google Sheets URL (e.g. https://docs.google.com/spreadsheets/d/...).",
        }

    try:
        parsed = urllib.parse.urlparse(raw)
    except Exception:
        return {"is_valid": False, "error": "Please enter a valid Google Sheets URL."}

    hostname = (parsed.hostname or "").lower()
    allowed_domains = ("docs.google.com", "drive.google.com", "spreadsheets.google.com")
    if not any(hostname == d or hostname.endswith("." + d) for d in allowed_domains):
        return {
            "is_valid": False,
            "error": "Invalid domain. Only official Google Sheets links (docs.google.com or drive.google.com) are accepted.",
        }

    # Published to web format: /spreadsheets/d/e/2PACX-.../pubhtml or pub?output=csv
    pub_match = re.search(r"/spreadsheets/d/e/([a-zA-Z0-9-_]+)", parsed.path)
    if pub_match:
        pub_id = pub_match.group(1)
        q = urllib.parse.parse_qs(parsed.query)
        gid = q.get("gid", ["0"])[0]
        return {
            "is_valid": True,
            "spreadsheet_id": pub_id,
            "is_published": True,
            "gid": gid,
            "export_csv_url": f"https://docs.google.com/spreadsheets/d/e/{pub_id}/pub?output=csv&gid={gid}",
            "gviz_url": f"https://docs.google.com/spreadsheets/d/e/{pub_id}/pub?output=csv&gid={gid}",
            "html_url": f"https://docs.google.com/spreadsheets/d/e/{pub_id}/pubhtml",
            "canonical_url": f"https://docs.google.com/spreadsheets/d/e/{pub_id}/pubhtml",
        }

    # Standard spreadsheet URL: /spreadsheets/d/{ID} or /file/d/{ID}
    id_match = re.search(r"/(?:spreadsheets(?:/u/\d+)?/d|file/d)/([a-zA-Z0-9-_]+)", parsed.path)
    if not id_match:
        q = urllib.parse.parse_qs(parsed.query)
        if "id" in q and q["id"]:
            sheet_id = q["id"][0]
        else:
            return {
                "is_valid": False,
                "error": "Please enter a valid Google Sheets URL. Could not find spreadsheet ID in URL.",
            }
    else:
        sheet_id = id_match.group(1)

    # Extract gid from query or fragment
    gid = None
    q = urllib.parse.parse_qs(parsed.query)
    if "gid" in q and q["gid"]:
        gid = q["gid"][0]
    elif parsed.fragment:
        frag_q = urllib.parse.parse_qs(parsed.fragment)
        if "gid" in frag_q and frag_q["gid"]:
            gid = frag_q["gid"][0]
        else:
            m_gid = re.search(r"gid=(\d+)", parsed.fragment)
            if m_gid:
                gid = m_gid.group(1)

    gid = gid or "0"

    return {
        "is_valid": True,
        "spreadsheet_id": sheet_id,
        "is_published": False,
        "gid": gid,
        "export_csv_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}",
        "gviz_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}",
        "html_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/htmlview",
        "canonical_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit",
    }


def _fetch_google_sheets_metadata(parsed_info: Dict[str, Any], oauth_token: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve title and available worksheet tabs from a Google Sheet."""
    sheet_id = parsed_info["spreadsheet_id"]

    # 1. OAuth path (for private sheets when user connected Google Account)
    if oauth_token:
        try:
            import httpx
            api_url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
            headers = {"Authorization": f"Bearer {oauth_token}", "User-Agent": "DataScope-Sync/1.0"}
            with httpx.Client(timeout=10.0) as client:
                res = client.get(api_url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    title = data.get("properties", {}).get("title", "Google Sheet")
                    sheets = []
                    for s in data.get("sheets", []):
                        props = s.get("properties", {})
                        sheets.append({
                            "name": props.get("title", "Sheet1"),
                            "gid": str(props.get("sheetId", 0)),
                        })
                    return {
                        "is_accessible": True,
                        "title": title,
                        "tabs": sheets or [{"name": "Sheet1", "gid": "0"}],
                        "auth_mode": "oauth",
                    }
                elif res.status_code in (401, 403):
                    return {
                        "is_accessible": False,
                        "error": "Your Google authentication has expired. Please reconnect your Google account.",
                    }
                elif res.status_code == 404:
                    return {
                        "is_accessible": False,
                        "error": "Google Sheet could not be found. Check the URL.",
                    }
                elif res.status_code == 429:
                    return {
                        "is_accessible": False,
                        "error": "Google Sheets API rate limit reached. Please try again in a few moments.",
                    }
        except httpx.TimeoutException:
            return {"is_accessible": False, "error": "Google Sheets took too long to respond. Please try again."}
        except Exception as e:
            return {"is_accessible": False, "error": f"Google Sheets OAuth inspection error: {str(e)}"}

    # 2. Public URL inspection
    html_url = parsed_info.get("html_url") or f"https://docs.google.com/spreadsheets/d/{sheet_id}/htmlview"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        import httpx
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(html_url, headers=headers)

            # Check if redirected to Google sign-in (Private Sheet)
            if "accounts.google.com" in str(resp.url) or "ServiceLogin" in resp.text or "Sign in - Google Accounts" in resp.text:
                return {
                    "is_accessible": False,
                    "is_private": True,
                    "error": "This Google Sheet is private. Make it accessible (set sharing to 'Anyone with the link can view') or connect your Google account.",
                }

            if resp.status_code == 404:
                return {
                    "is_accessible": False,
                    "error": "Google Sheet could not be found. Check the URL.",
                }

            if resp.status_code in (401, 403):
                return {
                    "is_accessible": False,
                    "error": "You don't have permission to read this Google Sheet. Ensure sharing is set to 'Anyone with the link can view'.",
                }

            if resp.status_code == 429:
                return {
                    "is_accessible": False,
                    "error": "Google Sheets API rate limit reached. Please try again in a few moments.",
                }

            if resp.status_code != 200:
                return {
                    "is_accessible": False,
                    "error": f"Could not retrieve Google Sheet (HTTP {resp.status_code}). Check URL.",
                }

            title = None
            m_title = re.search(r"<title>(.*?)(?: - Google (?:Sheets|Docs|Drive))?</title>", resp.text, re.IGNORECASE)
            if m_title:
                title = m_title.group(1).strip()

            tabs = []
            found_tabs = re.findall(r'<li id=["\']sheet-button-([^"\']+)["\'][^>]*><a[^>]*>(.*?)</a>', resp.text)
            for gid, tab_name in found_tabs:
                clean_name = re.sub(r"<[^>]+>", "", tab_name).strip()
                if clean_name and not any(t["name"] == clean_name for t in tabs):
                    tabs.append({"name": clean_name, "gid": gid})

            if not tabs:
                span_tabs = re.findall(r'class=["\']docs-sheet-tab-name["\'][^>]*>(.*?)</span>', resp.text)
                for idx, tab_name in enumerate(span_tabs):
                    clean_name = re.sub(r"<[^>]+>", "", tab_name).strip()
                    if clean_name and not any(t["name"] == clean_name for t in tabs):
                        tabs.append({"name": clean_name, "gid": str(idx)})

            if not tabs:
                tabs.append({"name": "Sheet1", "gid": parsed_info.get("gid", "0")})

            return {
                "is_accessible": True,
                "title": title or "Google Sheet",
                "tabs": tabs,
                "auth_mode": "public_url",
            }
    except httpx.TimeoutException:
        return {"is_accessible": False, "error": "Google Sheets took too long to respond. Please try again."}
    except Exception as e:
        return {"is_accessible": False, "error": f"Google Sheets connection error: {str(e)}"}


def _fetch_google_sheets_dataframe(
    parsed_info: Dict[str, Any],
    sheet_gid: Optional[str] = None,
    sheet_name: Optional[str] = None,
    limit: Optional[int] = None,
    oauth_token: Optional[str] = None,
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Fetch sample or full DataFrame from public or authorized Google Sheet."""
    sheet_id = parsed_info["spreadsheet_id"]
    gid = sheet_gid or parsed_info.get("gid") or "0"
    is_published = parsed_info.get("is_published", False)

    # 1. OAuth API fetch
    if oauth_token:
        try:
            import httpx
            target_range = urllib.parse.quote(sheet_name or "Sheet1")
            api_url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{target_range}"
            headers = {"Authorization": f"Bearer {oauth_token}", "User-Agent": "DataScope-Sync/1.0"}
            with httpx.Client(timeout=15.0) as client:
                res = client.get(api_url, headers=headers)
                if res.status_code == 200:
                    val_data = res.json().get("values", [])
                    if not val_data or len(val_data) == 0:
                        return None, "The selected worksheet contains no data rows."
                    headers_row = [str(c) if c is not None and str(c).strip() else f"Col_{i+1}" for i, c in enumerate(val_data[0])]
                    rows = val_data[1:limit+1] if limit else val_data[1:]
                    if not rows:
                        df = pd.DataFrame(columns=headers_row)
                    else:
                        df = pd.DataFrame(rows, columns=headers_row)
                    return df, None
                elif res.status_code in (401, 403):
                    return None, "Your Google authentication has expired. Please reconnect your Google account."
                elif res.status_code == 404:
                    return None, "Google Sheet or worksheet could not be found. Check the URL."
                elif res.status_code == 429:
                    return None, "Google Sheets API rate limit reached. Please try again in a few moments."
                else:
                    return None, f"Google Sheets API error (HTTP {res.status_code})"
        except httpx.TimeoutException:
            return None, "Google Sheets took too long to respond. Please try again."
        except Exception as e:
            return None, f"Google Sheets OAuth fetch error: {str(e)}"

    # 2. Public Export CSV fetch
    if is_published:
        fetch_url = f"https://docs.google.com/spreadsheets/d/e/{sheet_id}/pub?output=csv&gid={gid}"
    elif sheet_name and not sheet_gid:
        fetch_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={urllib.parse.quote(sheet_name)}"
    else:
        fetch_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        import httpx
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            resp = client.get(fetch_url, headers=headers)
            if "accounts.google.com" in str(resp.url) or "ServiceLogin" in resp.text or "Sign in - Google Accounts" in resp.text:
                return None, "This Google Sheet is private. Make it accessible (set sharing to 'Anyone with the link can view') or connect your Google account."
            if resp.status_code == 404:
                return None, "Google Sheet could not be found. Check the URL."
            if resp.status_code in (401, 403):
                return None, "You don't have permission to read this Google Sheet. Ensure sharing is set to 'Anyone with the link can view'."
            if resp.status_code == 429:
                return None, "Google Sheets API rate limit reached. Please try again in a few moments."
            if resp.status_code != 200:
                return None, f"Could not retrieve Google Sheet (HTTP {resp.status_code}). Check URL."

            raw_bytes = resp.content
            if not raw_bytes or len(raw_bytes.strip()) == 0:
                return None, "The selected worksheet contains no data rows."

            try:
                df = pd.read_csv(io.BytesIO(raw_bytes), nrows=limit)
            except pd.errors.EmptyDataError:
                return None, "The selected worksheet contains no data rows."
            except Exception as e:
                # Fallback to GViz CSV endpoint if export format had glitch
                if not is_published:
                    try:
                        gviz_fallback_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
                        resp_fallback = client.get(gviz_fallback_url, headers=headers)
                        if resp_fallback.status_code == 200 and "accounts.google.com" not in str(resp_fallback.url):
                            df = pd.read_csv(io.BytesIO(resp_fallback.content), nrows=limit)
                        else:
                            return None, f"Failed to parse Google Sheet data: {str(e)}"
                    except Exception:
                        return None, f"Failed to parse Google Sheet data: {str(e)}"
                else:
                    return None, f"Failed to parse Google Sheet data: {str(e)}"

            if df is None or len(df) == 0:
                return None, "The selected worksheet contains no data rows."

            return df, None
    except httpx.TimeoutException:
        return None, "Google Sheets took too long to respond. Please try again."
    except Exception as e:
        return None, f"Google Sheets connection error: {str(e)}"


class DataConnectorService:
    @staticmethod
    def test_connection(source_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test connectivity and configuration for a data source without persisting data."""
        source_type = source_type.lower().strip()

        # -------------------------------------------------------------
        # 1. PostgreSQL Connector Test
        # -------------------------------------------------------------
        if source_type in ("postgres", "postgresql"):
            host = config.get("host", "").strip()
            port = int(config.get("port") or 5432)
            database = config.get("database", "").strip()
            username = config.get("username", "").strip()
            password = config.get("password", "")
            sslmode = config.get("sslmode", "prefer").strip()

            if not host or not database or not username:
                return {
                    "success": False,
                    "message": "Host, database name, and username are required for PostgreSQL connection.",
                }

            try:
                import psycopg2

                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=database,
                    user=username,
                    password=password,
                    sslmode=sslmode,
                    connect_timeout=5,
                )
                with conn.cursor() as cur:
                    cur.execute("SELECT version();")
                    pg_version = cur.fetchone()[0]

                    # Count user tables
                    cur.execute(
                        """
                        SELECT count(*) 
                        FROM information_schema.tables 
                        WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                          AND table_type = 'BASE TABLE';
                    """
                    )
                    table_count = cur.fetchone()[0]

                conn.close()
                return {
                    "success": True,
                    "message": f"Successfully connected to PostgreSQL database '{database}' at {host}:{port}.",
                    "details": {
                        "server_version": pg_version.split(",")[0] if pg_version else "PostgreSQL",
                        "available_tables": int(table_count),
                        "ssl_active": sslmode,
                    },
                }
            except Exception as e:
                err_msg = str(e).strip()
                if "password authentication failed" in err_msg.lower():
                    return {"success": False, "message": "Authentication failed: Invalid username or password."}
                if "could not connect to server" in err_msg.lower() or "timeout" in err_msg.lower():
                    return {
                        "success": False,
                        "message": f"Could not connect to PostgreSQL server at {host}:{port}. Check host, firewall, or port.",
                    }
                return {"success": False, "message": f"PostgreSQL connection error: {err_msg}"}

        # -------------------------------------------------------------
        # 2. MySQL Connector Test
        # -------------------------------------------------------------
        elif source_type == "mysql":
            host = config.get("host", "").strip()
            port = int(config.get("port") or 3306)
            database = config.get("database", "").strip()
            username = config.get("username", "").strip()
            password = config.get("password", "")

            if not host or not database or not username:
                return {
                    "success": False,
                    "message": "Host, database name, and username are required for MySQL connection.",
                }

            try:
                import pymysql

                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database=database,
                    connect_timeout=5,
                )
                with conn.cursor() as cur:
                    cur.execute("SELECT VERSION();")
                    mysql_ver = cur.fetchone()[0]

                    cur.execute("SHOW TABLES;")
                    tables = cur.fetchall()
                    table_count = len(tables)

                conn.close()
                return {
                    "success": True,
                    "message": f"Successfully connected to MySQL database '{database}' at {host}:{port}.",
                    "details": {
                        "server_version": f"MySQL {mysql_ver}",
                        "available_tables": table_count,
                    },
                }
            except Exception as e:
                err_msg = str(e).strip()
                if "access denied" in err_msg.lower():
                    return {"success": False, "message": "Authentication failed: Invalid username or password."}
                if "can't connect" in err_msg.lower() or "timeout" in err_msg.lower():
                    return {
                        "success": False,
                        "message": f"Could not connect to MySQL server at {host}:{port}. Check host and port.",
                    }
                return {"success": False, "message": f"MySQL connection error: {err_msg}"}

        # -------------------------------------------------------------
        # 3. REST API Connector Test
        # -------------------------------------------------------------
        elif source_type == "rest_api":
            url = config.get("url", "").strip()
            if not url:
                return {"success": False, "message": "REST API URL is required."}

            safe, reason = _is_safe_url(url, allow_private=config.get("allow_private", False))
            if not safe:
                return {"success": False, "message": f"Security check rejected URL: {reason}"}

            method = config.get("method", "GET").upper()
            headers = {"User-Agent": "DataScope-BI/1.0", **(config.get("headers") or {})}

            # Auth header resolution
            auth_type = config.get("auth_type", "none")
            if auth_type == "bearer" and config.get("token"):
                headers["Authorization"] = f"Bearer {config.get('token')}"
            elif auth_type == "api_key" and config.get("api_key"):
                header_name = config.get("api_key_header", "X-API-Key")
                headers[header_name] = config.get("api_key")

            try:
                import httpx

                req_body = config.get("body") if method == "POST" else None
                with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                    if method == "POST":
                        resp = client.post(url, headers=headers, json=req_body)
                    else:
                        resp = client.get(url, headers=headers)

                    if resp.status_code >= 400:
                        return {
                            "success": False,
                            "message": f"API returned HTTP {resp.status_code}: {resp.reason_phrase}",
                        }

                    content_type = resp.headers.get("Content-Type", "").lower()
                    raw_text = resp.text

                    # Try JSON parsing
                    try:
                        parsed = resp.json()
                        records = parsed
                        if isinstance(parsed, dict):
                            # Look for common wrapper arrays
                            for key in ("data", "items", "results", "records", "rows", "payload"):
                                if isinstance(parsed.get(key), list):
                                    records = parsed[key]
                                    break
                            else:
                                records = [parsed]

                        if isinstance(records, list) and len(records) > 0:
                            sample_item = records[0]
                            detected_cols = list(sample_item.keys()) if isinstance(sample_item, dict) else ["value"]
                            return {
                                "success": True,
                                "message": f"Successfully connected to REST API. Detected {len(records)} records with {len(detected_cols)} fields.",
                                "details": {
                                    "status_code": resp.status_code,
                                    "record_count": len(records),
                                    "detected_columns": detected_cols[:15],
                                    "format": "JSON",
                                },
                            }
                    except Exception:
                        pass

                    # Try CSV parsing
                    try:
                        df = pd.read_csv(io.StringIO(raw_text), nrows=5)
                        return {
                            "success": True,
                            "message": f"Successfully connected to REST API CSV stream with {len(df.columns)} columns.",
                            "details": {
                                "status_code": resp.status_code,
                                "detected_columns": list(df.columns),
                                "format": "CSV Stream",
                            },
                        }
                    except Exception:
                        pass

                    return {
                        "success": True,
                        "message": f"Successfully reached REST API (HTTP {resp.status_code}). Response received.",
                        "details": {"status_code": resp.status_code, "content_type": content_type},
                    }

            except httpx.ConnectTimeout:
                return {"success": False, "message": "Connection timed out while reaching REST API."}
            except httpx.ConnectError as e:
                return {"success": False, "message": f"Could not connect to host: {str(e)}"}
            except Exception as e:
                return {"success": False, "message": f"REST API test error: {str(e)}"}

        # -------------------------------------------------------------
        # 4. Google Sheets Connector Test
        # -------------------------------------------------------------
        elif source_type == "google_sheets":
            sheet_url = (config.get("sheet_url") or config.get("sheet_id") or "").strip()
            parsed_info = _parse_google_sheets_url(sheet_url)
            if not parsed_info["is_valid"]:
                return {"success": False, "message": parsed_info["error"]}

            oauth_token = config.get("token") or config.get("access_token")

            # Fetch metadata (title, worksheets)
            meta = _fetch_google_sheets_metadata(parsed_info, oauth_token=oauth_token)
            if not meta.get("is_accessible"):
                return {"success": False, "message": meta.get("error", "Google Sheet is not accessible.")}

            # Fetch sample DataFrame (up to 5 rows) to verify structure
            df, err = _fetch_google_sheets_dataframe(
                parsed_info,
                sheet_gid=config.get("sheet_gid"),
                sheet_name=config.get("sheet_name"),
                limit=5,
                oauth_token=oauth_token,
            )
            if err:
                return {"success": False, "message": err}

            title = meta.get("title", "Google Sheet")
            col_list = list(df.columns) if df is not None else []
            table_tabs = meta.get("tabs", [])
            sheet_id_display = parsed_info["spreadsheet_id"]
            if len(sheet_id_display) > 12:
                safe_id = f"{sheet_id_display[:6]}...{sheet_id_display[-4:]}"
            else:
                safe_id = sheet_id_display

            return {
                "success": True,
                "message": f"Successfully connected to Google Sheet '{title}'. Found {len(col_list)} columns.",
                "details": {
                    "title": title,
                    "spreadsheet_id": safe_id,
                    "columns": col_list,
                    "tables": [t["name"] for t in table_tabs],
                    "available_sheets": table_tabs,
                    "status": "Accessible",
                    "auth_mode": meta.get("auth_mode", "public_url"),
                },
            }

        # -------------------------------------------------------------
        # 5. CSV / Excel File Connectors
        # -------------------------------------------------------------
        elif source_type in ("file_upload", "csv", "excel", "manual_entry"):
            return {
                "success": True,
                "message": f"{source_type.upper()} connector ready for parsing and analysis.",
                "details": {"status": "ready"},
            }

        return {
            "success": False,
            "message": f"Unknown connector type '{source_type}'. Supported: postgres, mysql, rest_api, google_sheets, csv, excel.",
        }

    # -----------------------------------------------------------------
    # Discover Tables and Schemas
    # -----------------------------------------------------------------
    @staticmethod
    def fetch_tables_and_metadata(source_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect the connected database or data source to list available tables, views, or sheets."""
        source_type = source_type.lower().strip()

        if source_type in ("postgres", "postgresql"):
            host = config.get("host", "").strip()
            port = int(config.get("port") or 5432)
            database = config.get("database", "").strip()
            username = config.get("username", "").strip()
            password = config.get("password", "")
            sslmode = config.get("sslmode", "prefer").strip()

            try:
                import psycopg2

                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=database,
                    user=username,
                    password=password,
                    sslmode=sslmode,
                    connect_timeout=6,
                )
                tables: List[Dict[str, Any]] = []
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT table_schema, table_name, table_type 
                        FROM information_schema.tables 
                        WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                        ORDER BY table_schema, table_name;
                    """
                    )
                    rows = cur.fetchall()
                    for s, t, typ in rows:
                        full_name = f"{s}.{t}" if s != "public" else t
                        tables.append({
                            "schema": s,
                            "name": t,
                            "full_name": full_name,
                            "type": typ,
                        })
                conn.close()
                return {"success": True, "tables": tables}
            except Exception as e:
                return {"success": False, "error": str(e), "tables": []}

        elif source_type == "mysql":
            host = config.get("host", "").strip()
            port = int(config.get("port") or 3306)
            database = config.get("database", "").strip()
            username = config.get("username", "").strip()
            password = config.get("password", "")

            try:
                import pymysql

                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database=database,
                    connect_timeout=6,
                )
                tables: List[Dict[str, Any]] = []
                with conn.cursor() as cur:
                    cur.execute("SHOW FULL TABLES;")
                    rows = cur.fetchall()
                    for row in rows:
                        t_name = row[0]
                        t_type = row[1] if len(row) > 1 else "BASE TABLE"
                        tables.append({
                            "schema": database,
                            "name": t_name,
                            "full_name": t_name,
                            "type": t_type,
                        })
                conn.close()
                return {"success": True, "tables": tables}
            except Exception as e:
                return {"success": False, "error": str(e), "tables": []}

        elif source_type == "google_sheets":
            sheet_url = (config.get("sheet_url") or config.get("sheet_id") or "").strip()
            parsed_info = _parse_google_sheets_url(sheet_url)
            if not parsed_info["is_valid"]:
                return {"success": False, "error": parsed_info["error"], "tables": []}

            oauth_token = config.get("token") or config.get("access_token")
            meta = _fetch_google_sheets_metadata(parsed_info, oauth_token=oauth_token)
            if not meta.get("is_accessible"):
                return {"success": False, "error": meta.get("error", "Google Sheet is inaccessible."), "tables": []}

            table_items = []
            for tab in meta.get("tabs", []):
                tab_name = tab.get("name", "Sheet1")
                tab_gid = str(tab.get("gid", "0"))
                table_items.append({
                    "schema": "google_sheets",
                    "name": tab_name,
                    "full_name": tab_name,
                    "type": "WORKSHEET",
                    "gid": tab_gid,
                })

            return {
                "success": True,
                "tables": table_items or [{"schema": "google_sheets", "name": "Sheet1", "full_name": "Sheet1", "type": "WORKSHEET", "gid": "0"}],
            }

        return {"success": True, "tables": []}

    # -----------------------------------------------------------------
    # Live Data Preview (up to 20 sample rows)
    # -----------------------------------------------------------------
    @staticmethod
    def preview_data(source_type: str, config: Dict[str, Any], limit: int = 20) -> Dict[str, Any]:
        """Fetch a limited live data preview (columns + rows) from the selected table or endpoint."""
        source_type = source_type.lower().strip()
        limit = min(limit, 50)

        df: Optional[pd.DataFrame] = None

        if source_type in ("postgres", "postgresql"):
            host = config.get("host", "").strip()
            port = int(config.get("port") or 5432)
            database = config.get("database", "").strip()
            username = config.get("username", "").strip()
            password = config.get("password", "")
            sslmode = config.get("sslmode", "prefer").strip()
            table_name = config.get("table_name", "").strip()
            custom_query = config.get("custom_query", "").strip()

            if not table_name and not custom_query:
                return {"success": False, "error": "Please specify a table name or custom query to preview."}

            try:
                import psycopg2

                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    dbname=database,
                    user=username,
                    password=password,
                    sslmode=sslmode,
                    connect_timeout=6,
                )
                if custom_query:
                    # Sanitize: ensure only SELECT statements
                    clean_q = custom_query.strip().rstrip(";")
                    if not clean_q.lower().startswith("select"):
                        conn.close()
                        return {"success": False, "error": "Only SELECT queries are permitted for safety."}
                    query = f"SELECT * FROM ({clean_q}) AS _preview_subq LIMIT {limit}"
                else:
                    # Parse schema & table
                    if "." in table_name:
                        s, t = table_name.split(".", 1)
                        query = f'SELECT * FROM "{s}"."{t}" LIMIT {limit}'
                    else:
                        query = f'SELECT * FROM "{table_name}" LIMIT {limit}'

                df = pd.read_sql_query(query, conn)
                conn.close()
            except Exception as e:
                return {"success": False, "error": f"PostgreSQL preview failed: {str(e)}"}

        elif source_type == "mysql":
            host = config.get("host", "").strip()
            port = int(config.get("port") or 3306)
            database = config.get("database", "").strip()
            username = config.get("username", "").strip()
            password = config.get("password", "")
            table_name = config.get("table_name", "").strip()
            custom_query = config.get("custom_query", "").strip()

            if not table_name and not custom_query:
                return {"success": False, "error": "Please specify a table name or query to preview."}

            try:
                import pymysql

                conn = pymysql.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database=database,
                    connect_timeout=6,
                )
                if custom_query:
                    clean_q = custom_query.strip().rstrip(";")
                    if not clean_q.lower().startswith("select"):
                        conn.close()
                        return {"success": False, "error": "Only SELECT queries are permitted for safety."}
                    query = f"SELECT * FROM ({clean_q}) AS _preview_subq LIMIT {limit}"
                else:
                    query = f"SELECT * FROM `{table_name}` LIMIT {limit}"

                df = pd.read_sql_query(query, conn)
                conn.close()
            except Exception as e:
                return {"success": False, "error": f"MySQL preview failed: {str(e)}"}

        elif source_type == "rest_api":
            url = config.get("url", "").strip()
            if not url:
                return {"success": False, "error": "REST API URL is required."}

            safe, reason = _is_safe_url(url, allow_private=config.get("allow_private", False))
            if not safe:
                return {"success": False, "error": f"Security check rejected URL: {reason}"}

            method = config.get("method", "GET").upper()
            headers = {"User-Agent": "DataScope-BI/1.0", **(config.get("headers") or {})}
            auth_type = config.get("auth_type", "none")
            if auth_type == "bearer" and config.get("token"):
                headers["Authorization"] = f"Bearer {config.get('token')}"
            elif auth_type == "api_key" and config.get("api_key"):
                headers[config.get("api_key_header", "X-API-Key")] = config.get("api_key")

            try:
                import httpx

                with httpx.Client(timeout=12.0, follow_redirects=True) as client:
                    if method == "POST":
                        resp = client.post(url, headers=headers, json=config.get("body"))
                    else:
                        resp = client.get(url, headers=headers)

                    if resp.status_code >= 400:
                        return {"success": False, "error": f"REST API error HTTP {resp.status_code}"}

                    try:
                        parsed = resp.json()
                        records = parsed
                        if isinstance(parsed, dict):
                            for key in ("data", "items", "results", "records", "rows", "payload"):
                                if isinstance(parsed.get(key), list):
                                    records = parsed[key]
                                    break
                            else:
                                records = [parsed]
                        if isinstance(records, list):
                            df = pd.DataFrame(records[:limit])
                    except Exception:
                        df = pd.read_csv(io.StringIO(resp.text), nrows=limit)

            except Exception as e:
                return {"success": False, "error": f"REST API fetch error: {str(e)}"}

        elif source_type == "google_sheets":
            sheet_url = (config.get("sheet_url") or config.get("sheet_id") or "").strip()
            parsed_info = _parse_google_sheets_url(sheet_url)
            if not parsed_info["is_valid"]:
                return {"success": False, "error": parsed_info["error"]}

            oauth_token = config.get("token") or config.get("access_token")
            sheet_gid = config.get("sheet_gid")
            sheet_name = config.get("table_name") or config.get("sheet_name")

            df, err = _fetch_google_sheets_dataframe(
                parsed_info,
                sheet_gid=sheet_gid,
                sheet_name=sheet_name,
                limit=limit,
                oauth_token=oauth_token,
            )
            if err:
                return {"success": False, "error": err}

        if df is None or len(df) == 0:
            return {"success": False, "error": "No records found from the data source."}

        # Convert NaN to None for clean JSON serialization
        clean_preview = json.loads(df.to_json(orient="records", date_format="iso"))
        dtypes = {str(col): str(df[col].dtype) for col in df.columns}

        return {
            "success": True,
            "row_count_sample": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": dtypes,
            "preview": clean_preview,
        }

    # -----------------------------------------------------------------
    # Extract Full DataFrame & Import to Active DataScope Dataset
    # -----------------------------------------------------------------
    @staticmethod
    def extract_dataframe(source_type: str, config: Dict[str, Any], max_rows: int = 50000) -> pd.DataFrame:
        """Extract full dataset from connected source into Pandas DataFrame."""
        source_type = source_type.lower().strip()

        if config.get("records") and isinstance(config["records"], list) and len(config["records"]) > 0:
            return pd.DataFrame(config["records"])
        if config.get("mock_data") and isinstance(config["mock_data"], list) and len(config["mock_data"]) > 0:
            return pd.DataFrame(config["mock_data"])

        if source_type in ("postgres", "postgresql"):
            import psycopg2

            conn = psycopg2.connect(
                host=config.get("host", "").strip(),
                port=int(config.get("port") or 5432),
                dbname=config.get("database", "").strip(),
                user=config.get("username", "").strip(),
                password=config.get("password", ""),
                sslmode=config.get("sslmode", "prefer").strip(),
                connect_timeout=10,
            )
            table_name = config.get("table_name", "").strip()
            custom_query = config.get("custom_query", "").strip()

            if custom_query:
                clean_q = custom_query.strip().rstrip(";")
                query = f"SELECT * FROM ({clean_q}) AS _extracted_q LIMIT {max_rows}"
            elif "." in table_name:
                s, t = table_name.split(".", 1)
                query = f'SELECT * FROM "{s}"."{t}" LIMIT {max_rows}'
            else:
                query = f'SELECT * FROM "{table_name}" LIMIT {max_rows}'

            df = pd.read_sql_query(query, conn)
            conn.close()
            return df

        elif source_type == "mysql":
            import pymysql

            conn = pymysql.connect(
                host=config.get("host", "").strip(),
                port=int(config.get("port") or 3306),
                user=config.get("username", "").strip(),
                password=config.get("password", ""),
                database=config.get("database", "").strip(),
                connect_timeout=10,
            )
            table_name = config.get("table_name", "").strip()
            custom_query = config.get("custom_query", "").strip()

            if custom_query:
                clean_q = custom_query.strip().rstrip(";")
                query = f"SELECT * FROM ({clean_q}) AS _extracted_q LIMIT {max_rows}"
            else:
                query = f"SELECT * FROM `{table_name}` LIMIT {max_rows}"

            df = pd.read_sql_query(query, conn)
            conn.close()
            return df

        elif source_type == "rest_api":
            if config.get("mock_data"):
                return pd.DataFrame(config["mock_data"])
            import httpx

            url = config.get("url", "").strip()
            method = config.get("method", "GET").upper()
            headers = {"User-Agent": "DataScope-BI/1.0", **(config.get("headers") or {})}
            auth_type = config.get("auth_type", "none")
            if auth_type == "bearer" and config.get("token"):
                headers["Authorization"] = f"Bearer {config.get('token')}"
            elif auth_type == "api_key" and config.get("api_key"):
                headers[config.get("api_key_header", "X-API-Key")] = config.get("api_key")

            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                resp = client.post(url, headers=headers, json=config.get("body")) if method == "POST" else client.get(url, headers=headers)
                resp.raise_for_status()
                try:
                    parsed = resp.json()
                    records = parsed
                    if isinstance(parsed, dict):
                        for key in ("data", "items", "results", "records", "rows", "payload"):
                            if isinstance(parsed.get(key), list):
                                records = parsed[key]
                                break
                        else:
                            records = [parsed]
                    return pd.DataFrame(records)
                except Exception:
                    return pd.read_csv(io.StringIO(resp.text))

        elif source_type == "google_sheets":
            sheet_url = (config.get("sheet_url") or config.get("sheet_id") or "").strip()
            parsed_info = _parse_google_sheets_url(sheet_url)
            if not parsed_info["is_valid"]:
                raise ValueError(parsed_info["error"])

            oauth_token = config.get("token") or config.get("access_token")
            sheet_gid = config.get("sheet_gid")
            sheet_name = config.get("table_name") or config.get("sheet_name")

            df, err = _fetch_google_sheets_dataframe(
                parsed_info,
                sheet_gid=sheet_gid,
                sheet_name=sheet_name,
                limit=max_rows,
                oauth_token=oauth_token,
            )
            if err:
                raise ValueError(err)
            if df is None or len(df) == 0:
                raise ValueError("The selected worksheet contains no data rows.")
            return df

        raise ValueError(f"Unsupported connector extraction type: {source_type}")

    # -----------------------------------------------------------------
    # Ingest Data to DataScope Active Analytics Dataset
    # -----------------------------------------------------------------
    @staticmethod
    def import_to_dataset(
        db: Session,
        company_id: str,
        source_type: str,
        config: Dict[str, Any],
        connection_name: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract data from connection, register into DataScope dataset store, and return dataset summary."""
        import uuid

        df = DataConnectorService.extract_dataframe(source_type, config)
        if df is None or len(df) == 0:
            raise ValueError("No data records could be extracted from the specified connection.")

        dataset_id = uuid.uuid4().hex
        clean_name = f"{connection_name} ({source_type.upper()})"
        filename = f"{connection_name.lower().replace(' ', '_')}_{source_type}.csv"
        now = datetime.now(timezone.utc)

        # 1. Infer semantic types and currency
        from app.models.audit_log import AuditLog
        from app.models.data_record import DataRecord
        from app.models.data_source import DataSource
        from app.core.supabase_client import SupabaseStorageService
        from app.services.column_profiler import profile_dataset
        from app.services.type_inference import detect_dataset_currency, infer_dataset_types
        from app.services.domain_detector import detect_domain

        inferred_types = infer_dataset_types(df)
        detected_currency = detect_dataset_currency(df) or "Rs. "
        profiles = profile_dataset(df)
        detected_dom = detect_domain(df, profiles)
        domain_id = detected_dom.domain_id if detected_dom else "general_business"
        domain_name = detected_dom.name if detected_dom else "General Business"

        # 2. Store in DatasetStore for analytics engine (in-memory fast cache)
        save_dataset(
            filename=filename,
            file_type="csv",
            df=df,
            dataset_id=dataset_id,
        )

        # 3. Create or Link Persistent DataSource Record
        # Sanitize config to ensure credentials are safe
        safe_config = {}
        for k, v in (config or {}).items():
            if any(secret_kw in k.lower() for secret_kw in ("password", "secret", "token", "key")):
                safe_config[k] = "••••••••" if v else ""
            else:
                safe_config[k] = v

        data_source_record = DataSource(
            id=str(uuid.uuid4()),
            company_id=company_id,
            dataset_id=dataset_id,
            name=connection_name,
            source_type=source_type,
            status="active",
            sync_frequency=config.get("sync_frequency", "manual"),
            config_json=json.dumps(safe_config),
            is_paused=False,
            total_records_synced=int(df.shape[0]),
            last_sync_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(data_source_record)

        # 4. Create Persistent Dataset Record
        dataset_record = Dataset(
            id=dataset_id,
            company_id=company_id,
            name=clean_name,
            filename=filename,
            file_type=source_type,
            active_version_number=1,
            current_row_count=int(df.shape[0]),
            current_col_count=int(df.shape[1]),
            currency_symbol=detected_currency,
            domain_id=domain_id,
            domain_name=domain_name,
            created_by_id=user_id,
            created_at=now,
            updated_at=now,
        )
        db.add(dataset_record)

        # 5. Create Version Snapshot
        version_snapshot = DatasetVersion(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            version_number=1,
            row_count=int(df.shape[0]),
            col_count=int(df.shape[1]),
            change_summary=f"Initial ingestion from {source_type.upper()} connection '{connection_name}'",
            column_schema=json.dumps([c.to_dict() for c in inferred_types]),
            created_by_id=user_id,
            created_at=now,
        )
        db.add(version_snapshot)
        db.flush()

        # 6. Bulk Insert All Row Data Records
        raw_rows = json.loads(df.to_json(orient="records", date_format="iso"))
        batch_size = 1000
        for i in range(0, len(raw_rows), batch_size):
            batch = raw_rows[i : i + batch_size]
            mappings = [
                {
                    "id": str(uuid.uuid4()),
                    "dataset_id": dataset_id,
                    "version_id": version_snapshot.id,
                    "row_index": i + offset + 1,
                    "record_json": json.dumps(row_dict),
                    "is_deleted": 0,
                    "created_at": now,
                    "updated_at": now,
                }
                for offset, row_dict in enumerate(batch)
            ]
            db.bulk_insert_mappings(DataRecord, mappings)

        # 7. Audit Log
        audit = AuditLog(
            id=str(uuid.uuid4()),
            company_id=company_id,
            user_id=user_id,
            action="DATASET_IMPORTED",
            target_type="dataset",
            target_id=dataset_id,
            details_json=json.dumps({
                "source_type": source_type,
                "connection_name": connection_name,
                "rows": int(df.shape[0]),
                "cols": int(df.shape[1]),
            }),
        )
        db.add(audit)
        db.commit()

        # 8. Supabase Storage Backup (Cloud-Native Storage) & Cloud Sync
        try:
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            SupabaseStorageService.upload_file(
                bucket="datasets",
                path=f"{company_id}/{dataset_id}.csv",
                file_bytes=csv_bytes,
                content_type="text/csv",
            )
        except Exception:
            pass

        try:
            from app.services.supabase_sync_service import SupabaseSyncService
            SupabaseSyncService.sync_data_source(
                source_id=data_source_record.id,
                company_id=company_id,
                name=connection_name,
                source_type=source_type,
                dataset_id=dataset_id,
                sync_frequency=config.get("sync_frequency", "manual"),
                config_dict=safe_config,
                total_records=int(df.shape[0]),
            )
            SupabaseSyncService.sync_dataset(
                dataset_id=dataset_id,
                company_id=company_id,
                name=clean_name,
                file_type=source_type,
                row_count=int(df.shape[0]),
                col_count=int(df.shape[1]),
                user_id=user_id,
            )
        except Exception:
            pass

        # Build full standard summary payload with inferred_columns, diagnostics, detected_currency, dtypes, preview
        from app.services.dataset_service import build_summary
        summary = build_summary(
            df=df,
            filename=filename,
            file_type="csv",
            dataset_id=dataset_id,
            inferred=inferred_types,
            detected_currency=detected_currency,
        )
        summary["name"] = clean_name
        summary["message"] = f"Successfully imported {len(df):,} records from {source_type.upper()} into DataScope."
        return summary

    # -----------------------------------------------------------------
    # Background / Manual Sync of Existing Source
    # -----------------------------------------------------------------
    @staticmethod
    def sync_source(db: Session, data_source_id: str, company_id: str, sync_type: str = "manual") -> Dict[str, Any]:
        """Execute a synchronization job for a data source, updating dataset and cache."""
        source = db.query(DataSource).filter(
            DataSource.id == data_source_id,
            DataSource.company_id == company_id,
        ).first()

        if not source:
            raise ValueError(f"Data source '{data_source_id}' not found.")

        if source.is_paused and sync_type == "scheduled":
            return {"status": "skipped", "message": "Data source is paused."}

        job = DataSyncJob(
            data_source_id=source.id,
            company_id=company_id,
            status="running",
            sync_type=sync_type,
            started_at=datetime.now(timezone.utc),
        )
        db.add(job)
        source.status = "syncing"
        db.commit()

        start_time = datetime.now(timezone.utc)
        logs: List[str] = [f"[{start_time.strftime('%H:%M:%S')}] Started {sync_type} sync for '{source.name}' ({source.source_type})."]

        try:
            config = json.loads(source.config_json) if isinstance(source.config_json, str) else (source.config_json or {})
            df = DataConnectorService.extract_dataframe(source.source_type, config)
            logs.append(f"Extracted {len(df):,} rows and {len(df.columns)} columns.")

            now = datetime.now(timezone.utc)
            dataset_id = source.dataset_id
            dataset_record: Optional[Dataset] = None
            if dataset_id:
                dataset_record = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.company_id == company_id).first()

            if not dataset_record:
                dataset_record = Dataset(
                    company_id=company_id,
                    name=f"{source.name} (Live Sync)",
                    file_type="csv",
                    active_version_number=1,
                    current_row_count=len(df),
                    current_col_count=len(df.columns),
                    currency_symbol="Rs. ",
                    domain_id="general_business",
                    domain_name="General Business",
                    created_at=now,
                    updated_at=now,
                )
                db.add(dataset_record)
                db.flush()
                source.dataset_id = dataset_record.id
            else:
                dataset_record.current_row_count = len(df)
                dataset_record.current_col_count = len(df.columns)
                dataset_record.active_version_number += 1
                dataset_record.updated_at = now

            filename = f"{source.name.lower().replace(' ', '_')}_synced.csv"
            dataset_store.put(
                filename=filename,
                file_type="csv",
                df=df,
                dataset_id=dataset_record.id,
            )

            version_snapshot = DatasetVersion(
                dataset_id=dataset_record.id,
                version_number=dataset_record.active_version_number,
                row_count=len(df),
                col_count=len(df.columns),
                change_summary=f"Automated sync from {source.source_type} data source '{source.name}'",
                column_schema=json.dumps({str(c): str(df[c].dtype) for c in df.columns}),
                created_at=now,
            )
            db.add(version_snapshot)

            records_count = len(df)
            job.status = "success"
            job.records_added = records_count
            job.completed_at = now
            job.log_output = "\n".join(logs)

            source.status = "active"
            source.last_sync_at = now
            source.last_error_message = None
            source.total_records_synced += records_count

            db.commit()

            return {
                "status": "success",
                "job_id": job.id,
                "dataset_id": dataset_record.id,
                "records_synced": records_count,
                "version": dataset_record.active_version_number,
                "logs": logs,
            }
        except Exception as e:
            now = datetime.now(timezone.utc)
            err_msg = str(e)
            logs.append(f"[{now.strftime('%H:%M:%S')}] SYNC FAILED: {err_msg}")
            job.status = "failed"
            job.error_message = err_msg
            job.completed_at = now
            job.log_output = "\n".join(logs)
            source.status = "error"
            source.last_error_message = err_msg
            db.commit()
            return {"status": "failed", "job_id": job.id, "error": err_msg, "logs": logs}


data_connector_service = DataConnectorService()

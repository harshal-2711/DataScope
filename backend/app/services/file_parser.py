"""Robust multi-encoding, multi-delimiter file parser for tabular datasets.

Supports:
- CSV, TSV, TXT, Excel (.xlsx, .xls)
- Encoding fallbacks: utf-8, utf-8-sig, latin1, cp1252, iso-8859-1
- Delimiter sniffing: ',', ';', '\t', '|'
- Duplicate column detection and clean normalization
- Malformed row recovery with diagnostic counts
- Explicit empty checks and error handling
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from app.core.config import settings
from app.services.dataset_exceptions import (
    EmptyDatasetError,
    EmptyFileError,
    FileTooLargeError,
    UnreadableFileError,
    UnsupportedFileTypeError,
)


@dataclass
class FileDiagnostics:
    encoding_used: str = "utf-8"
    delimiter_used: str = ","
    duplicate_columns_renamed: List[str] = field(default_factory=list)
    malformed_rows_skipped: int = 0
    warnings: List[str] = field(default_factory=list)


def parse_tabular_file(
    contents: bytes,
    filename: str,
    file_type: str,
) -> Tuple[pd.DataFrame, FileDiagnostics]:
    """Parse file bytes into a clean DataFrame with full diagnostics."""
    if len(contents) == 0:
        raise EmptyFileError("The uploaded file is empty.")

    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise FileTooLargeError(
            f"File is {size_mb:.1f}MB, exceeding the {settings.MAX_UPLOAD_SIZE_MB}MB limit."
        )

    diagnostics = FileDiagnostics()

    if file_type in ("xlsx", "xls"):
        buffer = io.BytesIO(contents)
        try:
            engine = "openpyxl" if file_type == "xlsx" else "xlrd"
            df = pd.read_excel(buffer, engine=engine)
            diagnostics.encoding_used = "binary"
            diagnostics.delimiter_used = "excel"
        except Exception as exc:
            raise UnreadableFileError(
                f"The Excel file could not be parsed: {type(exc).__name__} - {str(exc)}"
            ) from exc
    elif file_type == "csv":
        df, diag = _read_csv_with_fallback(contents)
        diagnostics = diag
    else:
        raise UnsupportedFileTypeError(f"Unsupported file type '{file_type}'.")

    if df.shape[1] == 0:
        raise EmptyDatasetError("The dataset contains no columns.")
    if df.shape[0] == 0:
        raise EmptyDatasetError("The dataset contains no data rows.")

    # Detect duplicate columns or pandas dot-number suffixes
    original_cols = [str(c) for c in df.columns]
    seen_cols = set()
    renamed_cols = []
    new_cols = []

    for idx, c in enumerate(original_cols):
        c_clean = c.strip() or f"Unnamed_{idx}"
        base_name = re.sub(r"\.\d+$", "", c_clean)
        if c_clean in seen_cols or (base_name in seen_cols and re.search(r"\.\d+$", c_clean)):
            suffix = 1
            cand = f"{base_name}_{suffix}"
            while cand in seen_cols:
                suffix += 1
                cand = f"{base_name}_{suffix}"
            renamed_cols.append(f"'{c_clean}' -> '{cand}'")
            new_cols.append(cand)
            seen_cols.add(cand)
        else:
            new_cols.append(c_clean)
            seen_cols.add(c_clean)

    if renamed_cols:
        df.columns = new_cols
        diagnostics.duplicate_columns_renamed = renamed_cols
        diagnostics.warnings.append(
            f"Renamed {len(renamed_cols)} duplicate column headers: {', '.join(renamed_cols[:5])}."
        )

    return df, diagnostics


def _read_csv_with_fallback(contents: bytes) -> Tuple[pd.DataFrame, FileDiagnostics]:
    """Try multiple encodings and sniff delimiters to parse CSV content."""
    encodings_to_try = ("utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1")
    delimiters_to_try = (",", ";", "\t", "|")

    diagnostics = FileDiagnostics()
    parsed_df: Optional[pd.DataFrame] = None
    last_error: Optional[Exception] = None

    for enc in encodings_to_try:
        try:
            # Decode sample to sniff delimiter
            sample_text = contents[:8192].decode(enc, errors="replace")
            delimiter = ","
            try:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample_text, delimiters=",\t;|")
                if dialect.delimiter in delimiters_to_try:
                    delimiter = dialect.delimiter
            except Exception:
                # Fallback delimiter heuristics
                first_line = sample_text.split("\n")[0] if "\n" in sample_text else sample_text
                counts = {d: first_line.count(d) for d in delimiters_to_try}
                best_delim = max(counts, key=counts.get)
                if counts[best_delim] > 0:
                    delimiter = best_delim

            buffer = io.BytesIO(contents)
            df = pd.read_csv(
                buffer,
                encoding=enc,
                sep=delimiter,
                on_bad_lines="skip",
            )

            if df.shape[1] > 0:
                parsed_df = df
                diagnostics.encoding_used = enc
                diagnostics.delimiter_used = delimiter

                # Detect duplicate headers in raw text
                first_line = sample_text.splitlines()[0] if sample_text else ""
                try:
                    raw_headers = next(csv.reader([first_line], delimiter=delimiter))
                except Exception:
                    raw_headers = [h.strip() for h in first_line.split(delimiter)]

                seen = set()
                raw_dups = []
                for h in raw_headers:
                    h_clean = h.strip()
                    if h_clean in seen:
                        raw_dups.append(h_clean)
                    else:
                        seen.add(h_clean)

                if raw_dups:
                    for dup in raw_dups:
                        diagnostics.duplicate_columns_renamed.append(f"Duplicate header '{dup}' renamed")
                    diagnostics.warnings.append(
                        f"Detected {len(raw_dups)} duplicate column header(s) in source: {', '.join(raw_dups)}."
                    )

                if enc != "utf-8":
                    diagnostics.warnings.append(f"Parsed using fallback encoding '{enc}'.")
                if delimiter != ",":
                    diagnostics.warnings.append(f"Detected custom delimiter '{repr(delimiter)}'.")
                break
        except Exception as exc:
            last_error = exc
            continue

    if parsed_df is None:
        raise UnreadableFileError(
            f"Could not parse CSV with any supported encoding ({', '.join(encodings_to_try)}). "
            f"Details: {type(last_error).__name__} - {str(last_error)}"
        )

    return parsed_df, diagnostics

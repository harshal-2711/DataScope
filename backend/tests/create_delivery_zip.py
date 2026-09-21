"""Script to create a clean delivery ZIP for DataScope.

Excludes:
- node_modules
- venv, .venv
- .git
- dist, build
- __pycache__, *.pyc, *.pyo
- .DS_Store, Thumbs.db
"""
from __future__ import annotations

import os
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_ZIP = ROOT_DIR / "DataScope_Complete_Product_Delivery.zip"

EXCLUDE_DIRS = {
    "node_modules",
    "venv",
    ".venv",
    ".git",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
}

EXCLUDE_EXTS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".DS_Store",
    ".zip",
}


def make_clean_zip():
    print(f"Creating delivery ZIP from: {ROOT_DIR}")
    print(f"Target archive: {OUTPUT_ZIP}")

    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    file_count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(ROOT_DIR):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

            for file in files:
                file_path = Path(root) / file
                if file_path == OUTPUT_ZIP:
                    continue
                if file_path.suffix.lower() in EXCLUDE_EXTS:
                    continue
                if any(ex in file_path.parts for ex in EXCLUDE_DIRS):
                    continue

                arcname = file_path.relative_to(ROOT_DIR)
                zipf.write(file_path, arcname)
                file_count += 1

    size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"Successfully packaged {file_count} files into {OUTPUT_ZIP.name} ({size_mb:.2f} MB).")
    return str(OUTPUT_ZIP)


if __name__ == "__main__":
    make_clean_zip()

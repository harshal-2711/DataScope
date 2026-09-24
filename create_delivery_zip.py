import os
import zipfile

zip_filename = os.path.join(os.getcwd(), "DataScope_Full_Audit_Stability_Delivery.zip")
exclude_dirs = {"node_modules", ".git", "dist", "__pycache__", ".venv", ".idea", ".vscode", ".gemini", "brain", ".agents"}
exclude_extensions = {".pyc", ".log", ".tmp", ".zip", ".db"}

total_files = 0
root_dir = os.getcwd()

print("Creating ZIP file...")
with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
    for root, dirs, files in os.walk(root_dir):
        # Exclude directories in-place
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        for file in files:
            if file.endswith(".zip"):
                continue
            ext = os.path.splitext(file)[1].lower()
            if ext in exclude_extensions:
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, root_dir)
            zipf.write(full_path, rel_path)
            total_files += 1

print(f"SUCCESS: Created {zip_filename} with {total_files} project files!")

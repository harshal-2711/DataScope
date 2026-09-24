import os
import zipfile

zip_filename = os.path.join(os.getcwd(), "DataScope_Complete_Functional_Build.zip")
exclude_dirs = {"node_modules", ".git", "dist", "__pycache__", ".venv", ".idea", ".vscode", ".gemini", "brain"}
exclude_extensions = {".pyc", ".log", ".tmp"}

total_files = 0
root_dir = os.getcwd()

with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(root_dir):
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

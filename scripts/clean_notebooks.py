"""Sanitize Jupyter notebooks by removing metadata.widgets entries.

This script fixes a common issue with notebooks exported from tools like
Google Colab where notebook-level or cell-level `metadata.widgets` causes
GitHub and some nbconvert versions to fail rendering with errors such as:
"the 'state' key is missing from 'metadata.widgets'".

Usage:
  python3 scripts/clean_notebooks.py <notebook_or_directory> [...]

Behavior:
  - Recursively finds *.ipynb files for any directory arguments.
  - Removes `metadata.widgets` at both the notebook and cell level.
  - Writes changes back in-place.
  - Safe to run repeatedly (idempotent).
"""
import argparse
import json
import sys
from pathlib import Path


def remove_widgets_metadata(nb_data: dict) -> bool:
	"""Remove metadata.widgets from notebook and cells. Returns True if modified."""
	modified = False
	metadata = nb_data.get("metadata", {})
	if isinstance(metadata, dict) and "widgets" in metadata:
		metadata.pop("widgets", None)
		nb_data["metadata"] = metadata
		modified = True

	cells = nb_data.get("cells", [])
	for cell in cells:
		cell_md = cell.get("metadata", {})
		if isinstance(cell_md, dict) and "widgets" in cell_md:
			cell_md.pop("widgets", None)
			cell["metadata"] = cell_md
			modified = True

	return modified


def process_notebook(path: Path) -> bool:
	try:
		with path.open("r", encoding="utf-8") as f:
			nb = json.load(f)
	except Exception as e:
		print(f"Failed to read {path}: {e}", file=sys.stderr)
		return False

	modified = remove_widgets_metadata(nb)
	if not modified:
		print(f"No changes: {path}")
		return False

	try:
		with path.open("w", encoding="utf-8") as f:
			json.dump(nb, f, ensure_ascii=False, indent=1)
			f.write("\n")
		print(f"Fixed: {path}")
		return True
	except Exception as e:
		print(f"Failed to write {path}: {e}", file=sys.stderr)
		return False


def main():
	parser = argparse.ArgumentParser(description="Remove metadata.widgets from Jupyter notebooks.")
	parser.add_argument("paths", nargs="*", help="Notebook files or directories to process")
	args = parser.parse_args()

	if not args.paths:
		print("Provide notebook file paths or directories.", file=sys.stderr)
		sys.exit(2)

	notebook_files = []
	for p in args.paths:
		path = Path(p)
		if path.is_dir():
			notebook_files.extend(path.rglob("*.ipynb"))
		elif path.is_file() and path.suffix == ".ipynb":
			notebook_files.append(path)
		else:
			print(f"Skipping non-notebook path: {path}")

	if not notebook_files:
		print("No notebooks found.", file=sys.stderr)
		sys.exit(1)

	any_modified = False
	for nb_path in notebook_files:
		modified = process_notebook(nb_path)
		any_modified = any_modified or modified

	sys.exit(0 if any_modified else 0)


if __name__ == "__main__":
	main()



#!/usr/bin/env python3
"""Validate dataExports/ against localStorageFormats.md.

Usage: python3 validate.py [service ...]   (default: github notion linear todoist)

Checks, for every dataExports/<service>/*.json file:
  - the file is valid UTF-8 JSON holding an object
  - "service" matches the folder and the filename is <safe id>.json
  - required fields are present and non-empty
  - every *_at / *_time field is ISO 8601 UTC (YYYY-MM-DDTHH:MM:SS[.fff]Z) or null
  - date-only fields (due_date) are YYYY-MM-DD or null
  - no two files share an id
Exits 1 if any problem is found.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from save_items import ROOT, safe_name  # noqa: E402

REQUIRED = {
    "github": ["id", "name", "full_name", "html_url", "created_at", "updated_at", "exported_at"],
    "notion": ["id", "title", "url", "last_edited_time", "body_markdown", "exported_at"],
    "linear": ["id", "identifier", "title", "status", "priority", "url", "created_at", "updated_at", "exported_at"],
    "todoist": ["id", "content", "priority", "project_id", "project_name", "added_at", "exported_at"],
}
# Keys that must exist but may be null or empty, because the source allows that.
PRESENT = {
    "github": ["description", "readme_text"],
    "notion": [],
    "linear": ["description", "due_date", "estimate"],
    "todoist": ["description", "due_date", "section_id", "section_name", "completed_at"],
}
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def check_file(service: str, path: Path) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return [f"invalid JSON: {e}"]
    if not isinstance(data, dict):
        return ["top level is not an object"]

    errors = []
    if data.get("service") != service:
        errors.append(f"service is {data.get('service')!r}, expected {service!r}")
    for key in REQUIRED[service]:
        if data.get(key) in (None, ""):
            errors.append(f"missing required field {key!r}")
    for key in PRESENT[service]:
        if key not in data:
            errors.append(f"missing field {key!r} (use null if the source has no value)")
    if "id" in data and path.name != f"{safe_name(data['id'])}.json":
        errors.append(f"filename should be {safe_name(data['id'])}.json")
    for key, value in data.items():
        if value is None:
            continue
        if key.endswith("_at") or key.endswith("_time"):
            if not isinstance(value, str) or not TIMESTAMP.match(value):
                errors.append(f"{key}={value!r} is not ISO 8601 UTC")
        elif key.endswith("_date") and (not isinstance(value, str) or not DATE.match(value)):
            errors.append(f"{key}={value!r} is not YYYY-MM-DD")
    return errors


def main() -> int:
    services = sys.argv[1:] or list(REQUIRED)
    failed = False
    for service in services:
        folder = ROOT / "dataExports" / service
        files = sorted(folder.glob("*.json")) if folder.is_dir() else []
        seen = {}
        bad = 0
        for path in files:
            errors = check_file(service, path)
            try:
                item_id = json.loads(path.read_text(encoding="utf-8")).get("id")
            except Exception:
                item_id = None
            if item_id is not None:
                if item_id in seen:
                    errors.append(f"duplicate id, also in {seen[item_id]}")
                seen[item_id] = path.name
            for err in errors:
                print(f"FAIL {path.relative_to(ROOT)}: {err}")
            bad += bool(errors)
        print(f"{service}: {len(files)} files, {bad} invalid")
        failed |= bad > 0
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

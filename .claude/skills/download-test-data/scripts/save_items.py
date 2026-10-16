#!/usr/bin/env python3
"""Save normalized export records as one JSON file per item.

Usage: python3 save_items.py <service> <records.json>

<records.json> holds a JSON array of records already shaped as described in
localStorageFormats.md. Each record must have an "id". The file is written to
dataExports/<service>/<safe id>.json. An existing file is only rewritten when
its content (ignoring "exported_at") differs, so unchanged items keep their
original exported_at.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SERVICES = {"github", "notion", "linear"}
ROOT = Path(__file__).resolve().parents[4]


def safe_name(item_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(item_id))


def without_export_time(record: dict) -> dict:
    return {k: v for k, v in record.items() if k != "exported_at"}


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in SERVICES:
        print(__doc__, file=sys.stderr)
        return 2
    service, src = sys.argv[1], Path(sys.argv[2])
    records = json.loads(src.read_text(encoding="utf-8"))
    out_dir = ROOT / "dataExports" / service
    out_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    counts = {"new": 0, "updated": 0, "unchanged": 0}
    for record in records:
        if "id" not in record:
            raise SystemExit(f"record without id: {record!r:.200}")
        record = {"service": service, **without_export_time(record)}
        path = out_dir / f"{safe_name(record['id'])}.json"
        if path.exists():
            old = json.loads(path.read_text(encoding="utf-8"))
            if without_export_time(old) == record:
                counts["unchanged"] += 1
                continue
            counts["updated"] += 1
        else:
            counts["new"] += 1
        record["exported_at"] = now
        path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")

    print(f"{service}: {counts['new']} new, {counts['updated']} updated, {counts['unchanged']} unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Local dashboard for the JSON files in dataExports/.

Run:  python3 webapp/server.py  [--port 8000]

Uses only the Python standard library. It never calls a live API: every
request re-reads dataExports/, so new files and new service folders show up
on the next page refresh without a restart or code change.
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "dataExports"
STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
}

PRIORITY_LABELS = {0: "No priority", 1: "Urgent", 2: "High", 3: "Medium", 4: "Low"}


# ---------------------------------------------------------------------------
# Normalizing records
#
# Every item becomes the same shape so the browser can search and render any
# service the same way:
#   service, id, display_id, title, body, url, dates[], meta[], search_meta
# Known services get a hand-written adapter based on localStorageFormats.md.
# Any other folder (todoist, asana, ...) goes through generic(), which guesses
# from common field names, so new services work without code changes.
# ---------------------------------------------------------------------------

def first(d, *keys):
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v
    return None


def name_of(v):
    """Turn a person/label/project value (string or object) into text."""
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return first(v, "name", "displayName", "display_name", "title", "email", "login")
    return None


def names(v):
    if isinstance(v, list):
        return [n for n in (name_of(x) for x in v) if n]
    n = name_of(v)
    return [n] if n else []


def date_entry(label, value):
    return {"label": label, "value": value} if isinstance(value, str) and value else None


def meta_entry(label, value, kind=None):
    if value is None or value == "" or value == []:
        return None
    if isinstance(value, bool):
        value = "yes" if value else "no"
    if isinstance(value, list):
        value = ", ".join(str(x) for x in value)
    entry = {"label": label, "value": str(value)}
    if kind:
        entry["kind"] = kind
    return entry


def github(d):
    return {
        "title": d.get("full_name") or d.get("name"),
        "body": "\n\n".join(x for x in (d.get("description"), d.get("readme_text")) if x),
        "url": d.get("html_url"),
        "display_id": d.get("name"),
        "dates": [
            date_entry("Updated", d.get("updated_at")),
            date_entry("Pushed", d.get("pushed_at")),
            date_entry("Created", d.get("created_at")),
        ],
        "meta": [
            meta_entry("Visibility", d.get("visibility"), "status"),
            meta_entry("Language", d.get("primary_language")),
            meta_entry("Topics", d.get("topics")),
            meta_entry("License", d.get("license")),
            meta_entry("Stars", d.get("stargazers_count") or None),
            meta_entry("Archived", "yes" if d.get("is_archived") else None, "status"),
        ],
    }


def notion(d):
    icon = d.get("icon") or {}
    path = [name_of(a) for a in d.get("ancestor_path") or []]
    workspace = name_of(d.get("workspace"))
    props = d.get("properties") or {}
    extra = [meta_entry(k, v) for k, v in props.items()
             if k.lower() != "title" and isinstance(v, (str, int, float))]
    return {
        "title": d.get("title"),
        "icon": icon.get("emoji") if isinstance(icon, dict) else None,
        "body": d.get("body_markdown"),
        "url": d.get("url"),
        "display_id": None,
        "dates": [date_entry("Last edited", d.get("last_edited_time"))],
        "meta": [
            meta_entry("Workspace", workspace),
            meta_entry("Path", " / ".join(p for p in path if p)),
        ] + extra,
    }


def linear(d):
    priority = d.get("priority")
    plabel = d.get("priority_label") or PRIORITY_LABELS.get(priority)
    return {
        "title": d.get("title"),
        "body": d.get("description"),
        "url": d.get("url"),
        "display_id": d.get("identifier"),
        "dates": [
            date_entry("Due", d.get("due_date")),
            date_entry("Updated", d.get("updated_at")),
            date_entry("Created", d.get("created_at")),
            date_entry("Completed", d.get("completed_at")),
            date_entry("Canceled", d.get("canceled_at")),
        ],
        "meta": [
            meta_entry("Status", d.get("status"), "status"),
            meta_entry("Priority", plabel if priority else None, "priority"),
            meta_entry("Assignee", ", ".join(names(d.get("assignee")))),
            meta_entry("Labels", names(d.get("labels"))),
            meta_entry("Project", name_of(d.get("project"))),
            meta_entry("Estimate", d.get("estimate")),
        ],
    }


def generic(d):
    dates = []
    for k, v in d.items():
        if k == "exported_at" or not isinstance(v, str):
            continue
        if k.endswith(("_at", "_time", "_date", "_on")) or k in ("due", "date"):
            dates.append(date_entry(k.replace("_", " ").capitalize(), v))
    meta = []
    for k in ("status", "state", "priority", "priority_label", "section", "project",
              "assignee", "labels", "tags", "completed"):
        v = d.get(k)
        n = names(v) if isinstance(v, (list, dict)) else v
        kind = "status" if k in ("status", "state", "completed") else (
            "priority" if k.startswith("priority") else None)
        meta.append(meta_entry(k.replace("_", " ").capitalize(), n, kind))
    due = d.get("due")
    if isinstance(due, dict):
        dates.insert(0, date_entry("Due", first(due, "date", "datetime", "string")))
    return {
        "title": first(d, "title", "name", "content", "subject", "summary", "full_name"),
        "body": first(d, "body", "body_markdown", "description", "notes", "html_notes",
                      "text", "readme_text"),
        "url": first(d, "url", "html_url", "permalink_url", "web_url", "link"),
        "display_id": first(d, "identifier", "key", "gid"),
        "dates": dates,
        "meta": meta,
    }


ADAPTERS = {"github": github, "notion": notion, "linear": linear}


def flatten_text(v, out):
    """Collect every string/number in a value, for metadata search."""
    if isinstance(v, str):
        out.append(v)
    elif isinstance(v, (int, float)) and not isinstance(v, bool):
        out.append(str(v))
    elif isinstance(v, dict):
        for x in v.values():
            flatten_text(x, out)
    elif isinstance(v, list):
        for x in v:
            flatten_text(x, out)


def normalize(service, path, d):
    adapter = ADAPTERS.get(service, generic)
    try:
        rec = adapter(d)
    except Exception:  # an unexpected shape should not drop the record
        rec = generic(d)
    rec["dates"] = [x for x in rec.get("dates", []) if x]
    rec["meta"] = [x for x in rec.get("meta", []) if x]
    item_id = d.get("id")
    rec["id"] = str(item_id) if item_id is not None else path.stem
    rec["service"] = service
    rec["file"] = f"{DATA_DIR.name}/{service}/{path.name}"
    rec["title"] = rec.get("title") or "(untitled)"
    rec["body"] = rec.get("body") or ""
    rec["exported_at"] = d.get("exported_at")
    # Metadata search covers every value in the file except the title and body,
    # which are searched (and ranked) separately.
    skip = {"title", "body_markdown", "readme_text", "description", "body", "notes"}
    parts = []
    for k, v in d.items():
        if k not in skip:
            flatten_text(v, parts)
    rec["search_meta"] = " ".join(parts)
    return rec


def load_all():
    services, records, problems = [], [], []
    if not DATA_DIR.is_dir():
        problems.append({"file": f"{DATA_DIR.name}/", "error": "Folder not found."})
        return {"services": services, "records": records, "problems": problems}
    for folder in sorted(p for p in DATA_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")):
        service = folder.name
        count = 0
        for path in sorted(folder.glob("*.json")):
            rel = f"{DATA_DIR.name}/{service}/{path.name}"
            try:
                d = json.loads(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                problems.append({"file": rel, "error": "Not valid UTF-8 text."})
                continue
            except json.JSONDecodeError as e:
                problems.append({"file": rel, "error": f"Invalid JSON: {e.msg} (line {e.lineno}, column {e.colno})."})
                continue
            except OSError as e:
                problems.append({"file": rel, "error": f"Could not read file: {e.strerror}."})
                continue
            if not isinstance(d, dict):
                problems.append({"file": rel, "error": "Top level is not a JSON object."})
                continue
            records.append(normalize(service, path, d))
            count += 1
        services.append({"name": service, "count": count})
    return {
        "services": services,
        "records": records,
        "problems": problems,
        "loaded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


class Handler(BaseHTTPRequestHandler):
    def send_body(self, status, ctype, body):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/data":
            body = json.dumps(load_all(), ensure_ascii=False).encode("utf-8")
            return self.send_body(200, "application/json; charset=utf-8", body)
        if path in STATIC_FILES:
            name, ctype = STATIC_FILES[path]
            return self.send_body(200, ctype, (STATIC_DIR / name).read_bytes())
        self.send_body(404, "text/plain; charset=utf-8", b"Not found")

    def log_message(self, fmt, *args):
        sys.stderr.write("[dashboard] " + (fmt % args) + "\n")


def main():
    global DATA_DIR
    parser = argparse.ArgumentParser(description="Serve the dataExports dashboard locally.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR,
                        help="folder to read instead of dataExports/ (for testing)")
    args = parser.parse_args()
    DATA_DIR = args.data_dir.resolve()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Dashboard running at http://{args.host}:{args.port}/  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

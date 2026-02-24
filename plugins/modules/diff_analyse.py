#!/usr/bin/env python3
"""
drift_report_generator.py
"""

import json
import hashlib
import argparse
import zipfile
from pathlib import Path
from datetime import datetime, timezone
from html import escape

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

BASELINE = REPORT_DIR / "baseline.json"
CURRENT = REPORT_DIR / "current.json"
DRIFT_JSON = REPORT_DIR / "drift_report.json"
DRIFT_HTML = REPORT_DIR / "drift_report.html"
DRIFT_ZIP = REPORT_DIR / "drift_report_bundle.zip"

VOLATILE_KEYS = {"timestamp", "last_checked"}

CLASSIFICATION_MAP = {
    "q_copygroup": "Policies",
    "q_replrule": "Policies",
    "q_domain": "Domains",
    "q_mgmtclass": "Management Classes",
    "q_devclass": "Device classes",
    "q_stgpool": "Storage hierarchies",
    "q_status": "Node configurations",
    "q_monitorsettings": "Node configurations",
    "q_db": "Node configurations",
    "q_dbspace": "Node configurations",
    "q_log": "Node configurations",
}

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def sha256_of(path: Path):
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build_report_bundle(bundle_path, html_path, json_path, current_path, baseline_path):
    with zipfile.ZipFile(bundle_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in (html_path, json_path, current_path, baseline_path):
            if p.exists():
                zf.write(p, arcname=p.name)

def clean_dict(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in VOLATILE_KEYS:
                continue
            if k in ("resource", "generated_at"):
                continue
            out[k] = clean_dict(v)
        return out
    if isinstance(obj, list):
        return [clean_dict(x) for x in obj]
    return obj

# -------------------------------------------------
# Diff engine
# -------------------------------------------------
def diff_dict(old, new):
    added, removed, changed = {}, {}, {}

    old = old or {}
    new = new or {}

    for k in new.keys() - old.keys():
        added[k] = new[k]

    for k in old.keys() - new.keys():
        removed[k] = old[k]

    for k in old.keys() & new.keys():
        a, b = old[k], new[k]
        if isinstance(a, dict) and isinstance(b, dict):
            ad, rm, ch = diff_dict(a, b)
            if ad:
                added[k] = ad
            if rm:
                removed[k] = rm
            if ch:
                changed[k] = ch
        elif a != b:
            changed[k] = {"old": a, "new": b}

    return added, removed, changed

# -------------------------------------------------
# Flatten to field-level rows
# -------------------------------------------------
def flatten_changes(module, obj, mode):
    rows = []

    def walk(path, old, new):
        if isinstance(old, dict) and isinstance(new, dict):
            for k in set(old) | set(new):
                walk(f"{path}.{k}" if path else k, old.get(k), new.get(k))
        else:
            if mode == "changed" and old != new:
                rows.append((module, path, old, new))
            elif mode == "added" and old is None:
                rows.append((module, path, None, new))
            elif mode == "removed" and new is None:
                rows.append((module, path, old, None))

    if mode == "changed":
        for k, v in obj.items():
            walk(k, v.get("old"), v.get("new"))
    else:
        walk("", None if mode == "added" else obj, obj if mode == "added" else None)

    return rows

# -------------------------------------------------
# HTML helpers
# -------------------------------------------------
def jdump(v):
    return escape(json.dumps(v, indent=2, ensure_ascii=False)) if v is not None else "null"

def classify_module(module_name):
    return CLASSIFICATION_MAP.get(module_name, "Node configurations")

def render_table(title, rows):
    if not rows:
        return ""

    is_changed = title == "Changed"

    html = [f"<div class='card'><h2>{title}</h2><table>"]

    if is_changed:
        html.append("<tr><th>Classification</th><th>Module</th><th>Field</th><th>Previous</th><th>Current</th></tr>")
    else:
        html.append("<tr><th>Classification</th><th>Module</th><th>Previous</th><th>Current</th></tr>")

    last_module = None
    for mod, field, old, new in rows:
        html.append("<tr>")

        html.append(f"<td>{escape(classify_module(mod))}</td>")
        if mod != last_module:
            html.append(f"<td><b>{escape(mod)}</b></td>")
            last_module = mod
        else:
            html.append("<td></td>")

        if is_changed:
            html.append(f"<td>{escape(field)}</td>")
            html.append(f"<td><pre>{jdump(old)}</pre></td>")
            html.append(f"<td><pre>{jdump(new)}</pre></td>")
        else:
            html.append(f"<td><pre>{jdump(old)}</pre></td>")
            html.append(f"<td><pre>{jdump(new)}</pre></td>")

        html.append("</tr>")

    html.append("</table></div>")
    return "\n".join(html)

def render_coverage_table(coverage):
    if not coverage:
        return ""

    per_query = coverage.get("per_query_field_counts", {})

    html = ["<div class='card'><h2>Coverage</h2><table>"]
    html.append("<tr><th>Metric</th><th>Value</th></tr>")
    html.append(f"<tr><td>Total Queries</td><td>{escape(str(coverage.get('total_queries', '')))}</td></tr>")
    html.append(f"<tr><td>Enabled Queries</td><td>{escape(str(coverage.get('enabled_queries', '')))}</td></tr>")
    html.append(f"<tr><td>Query Coverage %</td><td>{escape(str(coverage.get('query_coverage_pct', '')))}</td></tr>")
    html.append(f"<tr><td>Total Returned Fields</td><td>{escape(str(coverage.get('total_returned_fields', '')))}</td></tr>")
    html.append("</table></div>")

    if per_query:
        html.append("<div class='card'><h2>Per Query Field Counts</h2><table>")
        html.append("<tr><th>Query</th><th>Count</th></tr>")
        for k, v in sorted(per_query.items()):
            html.append(f"<tr><td>{escape(str(k))}</td><td>{escape(str(v))}</td></tr>")
        html.append("</table></div>")

    return "\n".join(html)

# -------------------------------------------------
# HTML generation
# -------------------------------------------------
def generate_html(rows, counts, meta, html_uri, json_uri, zip_uri, coverage=None):
    html = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<style>",
        "body{font-family:system-ui;background:#f6f8fb;margin:20px}",
        ".card{background:#fff;padding:14px;margin-bottom:12px;border-radius:8px}",
        "table{width:100%;border-collapse:collapse}",
        "th,td{border:1px solid #ddd;padding:6px;font-size:13px;vertical-align:top}",
        "pre{max-height:180px;overflow:auto;white-space:pre-wrap;word-break:break-word}",
        "</style></head><body>",
        "<div class='card'><h1>Config Drift Report</h1>",
        f"<p><b>Changed:</b> {counts['changed']} | "
        f"<b>Added:</b> {counts['added']} | "
        f"<b>Removed:</b> {counts['removed']}</p>",
        f"<p><a href='{html_uri}'>Open HTML report</a> | "
        f"<a href='{json_uri}'>Open JSON report</a> | "
        f"<a href='{zip_uri}' download>Download report bundle (.zip)</a></p>",
        f"<p>{meta}</p></div>",
    ]

    html.append(render_coverage_table(coverage))
    html.append(render_table("Changed", rows["Changed"]))
    html.append(render_table("Added", rows["Added"]))
    html.append(render_table("Removed", rows["Removed"]))

    html.append("</body></html>")
    return "\n".join(html)

# -------------------------------------------------
# Module-level counting
# -------------------------------------------------
def count_modules(rows):
    return len({r[0] for r in rows})

# -------------------------------------------------
# Main
# -------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", default=str(CURRENT), help="Path to current snapshot JSON")
    parser.add_argument("--baseline", default=str(BASELINE), help="Path to baseline JSON")
    parser.add_argument("--drift-json", default=str(DRIFT_JSON), help="Path to drift JSON output")
    parser.add_argument("--drift-html", default=str(DRIFT_HTML), help="Path to drift HTML output")
    parser.add_argument("--drift-zip", default=str(DRIFT_ZIP), help="Path to drift ZIP output")
    parser.add_argument(
        "--accept",
        action="store_true",
        help="Accept current changes and update baseline.json",
    )
    args = parser.parse_args()

    current_path = Path(args.current)
    baseline_path = Path(args.baseline)
    drift_json_path = Path(args.drift_json)
    drift_html_path = Path(args.drift_html)
    drift_zip_path = Path(args.drift_zip)

    for p in (current_path, baseline_path, drift_json_path, drift_html_path, drift_zip_path):
        p.parent.mkdir(parents=True, exist_ok=True)

    current = load_json(current_path)
    if not current:
        print(f" {current_path} missing")
        return

    # ---------------- ACCEPT MODE ----------------
    if args.accept:
        write_json(baseline_path, current)
        print("Changes accepted. Baseline updated.")

        approval = {
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "baseline_sha": sha256_of(baseline_path),
        }
        write_json(baseline_path.parent / f"baseline_approval_{baseline_path.stem}.json", approval)
        return

    # -------------- NORMAL DIFF MODE -------------
    if not baseline_path.exists():
        write_json(baseline_path, current)
        print(" Baseline created")
        return

    baseline = load_json(baseline_path)
    coverage = current.get("coverage", {})

    prev = clean_dict(baseline["data"]["ansible_module_results"])
    curr = clean_dict(current["data"]["ansible_module_results"])

    added, removed, changed = diff_dict(prev, curr)

    rows = {"Changed": [], "Added": [], "Removed": []}

    for mod, val in changed.items():
        rows["Changed"].extend(flatten_changes(mod, val, "changed"))

    for mod, val in added.items():
        rows["Added"].extend(flatten_changes(mod, val, "added"))

    for mod, val in removed.items():
        rows["Removed"].extend(flatten_changes(mod, val, "removed"))

    counts = {
        "changed": count_modules(rows["Changed"]),
        "added": count_modules(rows["Added"]),
        "removed": count_modules(rows["Removed"]),
    }

    drift = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "baseline_sha": sha256_of(baseline_path),
        "current_sha": sha256_of(current_path),
        "coverage": coverage,
    }

    write_json(drift_json_path, drift)
    drift_html_path.write_text(
        generate_html(
            rows,
            counts,
            f"Baseline: {baseline_path.name} | Current: {current_path.name}",
            html_uri=drift_html_path.resolve().as_uri(),
            json_uri=drift_json_path.resolve().as_uri(),
            zip_uri=drift_zip_path.resolve().as_uri(),
            coverage=coverage,
        ),
        encoding="utf-8",
    )
    build_report_bundle(drift_zip_path, drift_html_path, drift_json_path, current_path, baseline_path)

    print(" Drift report generated")

if __name__ == "__main__":
    main()

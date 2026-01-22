#!/usr/bin/env python3
"""
drift_report_generator.py
"""

import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone
from html import escape

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

BASELINE = REPORT_DIR / "baseline.json"
CURRENT = REPORT_DIR / "current.json"
DRIFT_JSON = REPORT_DIR / "drift_report.json"
DRIFT_HTML = REPORT_DIR / "drift_report.html"

VOLATILE_KEYS = {"timestamp", "last_checked"}

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

def render_table(title, rows):
    if not rows:
        return ""

    is_changed = title == "Changed"

    html = [f"<div class='card'><h2>{title}</h2><table>"]

    if is_changed:
        html.append("<tr><th>Module</th><th>Field</th><th>Previous</th><th>Current</th></tr>")
    else:
        html.append("<tr><th>Module</th><th>Previous</th><th>Current</th></tr>")

    last_module = None
    for mod, field, old, new in rows:
        html.append("<tr>")

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

# -------------------------------------------------
# HTML generation
# -------------------------------------------------
def generate_html(rows, counts, meta):
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
        f"<p>{meta}</p></div>",
    ]

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
    parser.add_argument(
        "--accept",
        action="store_true",
        help="Accept current changes and update baseline.json",
    )
    args = parser.parse_args()

    current = load_json(CURRENT)
    if not current:
        print(" current.json missing")
        return

    # ---------------- ACCEPT MODE ----------------
    if args.accept:
        write_json(BASELINE, current)
        print("Changes accepted. Baseline updated.")

        approval = {
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "baseline_sha": sha256_of(BASELINE),
        }
        write_json(REPORT_DIR / "baseline_approval.json", approval)
        return

    # -------------- NORMAL DIFF MODE -------------
    if not BASELINE.exists():
        write_json(BASELINE, current)
        print(" Baseline created")
        return

    baseline = load_json(BASELINE)

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
        "baseline_sha": sha256_of(BASELINE),
        "current_sha": sha256_of(CURRENT),
    }

    write_json(DRIFT_JSON, drift)
    DRIFT_HTML.write_text(
        generate_html(rows, counts, f"Baseline: {BASELINE.name} | Current: {CURRENT.name}"),
        encoding="utf-8",
    )

    print(" Drift report generated")

if __name__ == "__main__":
    main()

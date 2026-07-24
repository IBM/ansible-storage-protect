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

BASELINE = REPORT_DIR / "baseline.json"
CURRENT = REPORT_DIR / "current.json"
DRIFT_JSON = REPORT_DIR / "drift_report.json"
DRIFT_HTML = REPORT_DIR / "drift_report.html"
DRIFT_ZIP = REPORT_DIR / "drift_report_bundle.zip"

VOLATILE_KEYS = {"timestamp", "last_checked"}

VOLATILE_FIELDS_BY_QUERY = {
    "q_status": {
        "activity_log_number_of_records",
        "used_space_on_file_system_mb",
        "free_space_available_mb",
    },
    "q_dbspace": {
        "used_space_mb",
        "free_space_mb",
    },
    "q_log": {
        "used_space_mb",
        "free_space_mb",
    },
    "q_stgpool": {
        "pct_util",
        "pct_migr",
    },
}

LIST_IDENTITY_FIELDS = {
    "q_dbspace": {
        (): ("location",),
    },
    "q_stgpool": {
        (): ("storage_pool_name",),
    },
    "q_replrule": {
        ("rules",): ("replication_rule_name",),
    },
    "q_devclass": {
        (): ("device_class_name",),
    },
    "q_domain": {
        (): ("policy_domain_name",),
    },
    "q_copygroup": {
        (): (
            "policy_domain_name",
            "policy_set_name",
            "mgmt_class_name",
            "copy_group_name",
        ),
    },
    "q_mgmtclass": {
        (): (
            "policy_domain_name",
            "policy_set_name",
            "mgmt_class_name",
        ),
    },
}

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

def get_host_name(snapshot, current_path):
    return snapshot.get("collected_from") or current_path.stem.replace("current_", "")

def get_host_address(snapshot, host_name):
    return snapshot.get("collected_address") or host_name

def host_label(host_name, host_address=None):
    name = host_name or "unknown"
    addr = host_address or name
    if addr == name:
        return f"Host: {name}"
    return f"Host: {name} ({addr})"

def get_query_keys(snapshot):
    data = snapshot.get("data", {})
    module_results = data.get("ansible_module_results", {})
    if isinstance(module_results, dict):
        return sorted(module_results.keys())
    return []

def clean_dict(obj, query_name=None):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in VOLATILE_KEYS:
                continue
            if k in ("resource", "generated_at"):
                continue
            if k in VOLATILE_FIELDS_BY_QUERY.get(query_name, set()):
                continue
            out[k] = clean_dict(v, query_name)
        return out
    if isinstance(obj, list):
        return [clean_dict(x, query_name) for x in obj]
    return obj

def _identity_label(item, identity_fields):
    missing = [
        field
        for field in identity_fields
        if field not in item or item[field] in (None, "")
    ]
    if missing:
        raise ValueError(
            "Cannot compare list item: missing identity field(s) {0}".format(
                ", ".join(missing)
            )
        )

    if len(identity_fields) == 1:
        return str(item[identity_fields[0]])
    return ", ".join(
        "{0}={1}".format(field, item[field])
        for field in identity_fields
    )


def normalize_lists(query_name, obj, path=()):
    if isinstance(obj, dict):
        return {
            key: normalize_lists(query_name, value, path + (key,))
            for key, value in obj.items()
        }

    if isinstance(obj, list):
        identity_fields = LIST_IDENTITY_FIELDS.get(
            query_name, {}
        ).get(path)
        if not identity_fields:
            return [
                normalize_lists(query_name, value, path)
                for value in obj
            ]

        normalized = {}
        for item in obj:
            if not isinstance(item, dict):
                raise ValueError(
                    "{0} list at {1} contains a non-object item".format(
                        query_name, ".".join(path) or "<root>"
                    )
                )
            identity = "[{0}]".format(
                _identity_label(item, identity_fields)
            )
            if identity in normalized:
                raise ValueError(
                    "{0} list at {1} contains duplicate identity {2}".format(
                        query_name, ".".join(path) or "<root>", identity
                    )
                )
            normalized[identity] = normalize_lists(
                query_name, item, path + ("[]",)
            )
        return normalized

    return obj


def prepare_module_results(module_results):
    return {
        query_name: normalize_lists(
            query_name,
            clean_dict(value, query_name),
        )
        for query_name, value in module_results.items()
    }


_MISSING = object()


def _join_path(path, key):
    if key.startswith("["):
        return "{0}{1}".format(path, key)
    return "{0}.{1}".format(path, key) if path else key


def _compare_values(module, path, old, new, rows):
    if old is _MISSING:
        rows["Added"].append((module, path, None, new))
        return
    if new is _MISSING:
        rows["Removed"].append((module, path, old, None))
        return

    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(old.keys() | new.keys()):
            _compare_values(
                module,
                _join_path(path, key),
                old.get(key, _MISSING),
                new.get(key, _MISSING),
                rows,
            )
        return

    if old != new:
        rows["Changed"].append((module, path, old, new))


def build_change_rows(old, new):
    rows = {"Changed": [], "Added": [], "Removed": []}
    for module in sorted(old.keys() | new.keys()):
        _compare_values(
            module,
            "",
            old.get(module, _MISSING),
            new.get(module, _MISSING),
            rows,
        )
    return rows


def serialize_rows(rows):
    return {
        key.lower(): [
            {
                "module": module,
                "field": field,
                "previous": old,
                "current": new,
            }
            for module, field, old, new in values
        ]
        for key, values in rows.items()
    }

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

    html = [f"<div class='card'><h2>{title}</h2><table>"]
    html.append(
        "<tr><th>Classification</th><th>Module</th><th>Field</th>"
        "<th>Previous</th><th>Current</th></tr>"
    )

    last_module = None
    for mod, field, old, new in rows:
        html.append("<tr>")

        html.append(f"<td>{escape(classify_module(mod))}</td>")
        if mod != last_module:
            html.append(f"<td><b>{escape(mod)}</b></td>")
            last_module = mod
        else:
            html.append("<td></td>")

        html.append(f"<td>{escape(field)}</td>")
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
def generate_html(rows, counts, meta, html_uri, json_uri, zip_uri, coverage=None, host_name=None):
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
        f"<p><b>{escape(host_name or 'Host: unknown')}</b></p>",
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
    host_name = get_host_name(current, current_path)
    host_address = get_host_address(current, host_name)
    accepted_queries = get_query_keys(current)

    # ---------------- ACCEPT MODE ----------------
    if args.accept:
        write_json(baseline_path, current)
        coverage = current.get("coverage", {})
        print(
            f"Changes accepted for {host_label(host_name, host_address)}. "
            f"Accepted query sections ({len(accepted_queries)}): "
            f"{', '.join(accepted_queries) if accepted_queries else 'none'}"
        )

        approval = {
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "baseline_sha": sha256_of(baseline_path),
            "host": host_name,
            "host_address": host_address,
            "accepted_queries": accepted_queries,
            "coverage": coverage,
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

    prev = prepare_module_results(
        baseline["data"]["ansible_module_results"]
    )
    curr = prepare_module_results(
        current["data"]["ansible_module_results"]
    )
    rows = build_change_rows(prev, curr)

    counts = {
        "changed": len(rows["Changed"]),
        "added": len(rows["Added"]),
        "removed": len(rows["Removed"]),
    }

    drift = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "host": host_name,
        "host_address": host_address,
        "queries_in_snapshot": accepted_queries,
        "counts": counts,
        "baseline_sha": sha256_of(baseline_path),
        "current_sha": sha256_of(current_path),
        "coverage": coverage,
        "changes": serialize_rows(rows),
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
            host_name=host_label(host_name, host_address),
        ),
        encoding="utf-8",
    )
    build_report_bundle(drift_zip_path, drift_html_path, drift_json_path, current_path, baseline_path)

    print(f" Drift report generated for {host_label(host_name, host_address)}")

if __name__ == "__main__":
    main()

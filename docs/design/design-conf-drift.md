# SP Configuration Drift Detection — Design Document

## SP Configuration Drift Detection — Design Mapping & Local Diff Script

This document presents simplified, converged strategies for adopting Configuration Drift Detection and Remediation in IBM Storage Protect (SP) environments.  
The goal is to rely on the Policy-Centric (Server DB) model as the foundation and merge complementary elements from other approaches to balance practicality, automation, and governance.

### Options
1. **Policy-Centric (Server DB) + Playbook-Integrated**  
2. **Policy-Centric (Server DB) + Snapshot-Diff**

---

## Organizations needing periodic audits or independent validation of SP configurations without changing existing playbook structures

Such organizations may choose **Option 2 — Policy-Centric (Server DB) + Snapshot-Diff**.  
We describe the design for Option 2 in this document.


## 1. Design-to-Implementation Mapping (4-Step Workflow)

### Step 1 — Baseline (generate `baseline.json`)
Component:
- `sp_server_facts.py`
  - Role: `roles/sp_server_facts`
  - Playbook: `playbooks/sp_server_facts_playbook.yml`

Action:
- Run `sp_server_facts` with selected `q_*` flags
- Save JSON to: 
  - `reports/SpServerResponseMapper.<timestamp>.json`
  - or `baseline.json`

Below are concise, actionable options for "Save JSON to:" 

in Step 1 — with recommended conventions, metadata, atomic write pattern, Ansible task example (control‑node write), optional Git/S3 publishing, and retention/security notes.

Naming & location (recommended)
- Local repo (control node): reports/SpServerResponseMapper.<YYYYmmddTHHMMSSZ>.json  
- Baseline alias: reports/baseline.json (human‑approved snapshot)  
- Current alias: reports/current.json (latest scanned snapshot)  
- Example filename: reports/SpServerResponseMapper.20251202T143000Z.json

Required metadata to embed in snapshot
- resource, collected_by, collected_from, timestamp (ISO8601 UTC)  
- collector_version, playbook/run_id, scan_id, collected_by_user  
- checksums.snapshot_sha256, sensitive_masking (fields masked)  
- optional: git_commit, ci_job_id, tags

Atomic write + checksum (Python snippet)
```python
import json, hashlib, tempfile, shutil, os
from pathlib import Path
from datetime import datetime

def write_snapshot_atomic(obj, out_dir="reports", prefix="SpServerResponseMapper"):
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    fname = f"{prefix}.{ts}.json"
    tmpf = p / (fname + ".tmp")
    final = p / fname
    content = json.dumps(obj, indent=2, sort_keys=True)
    tmpf.write_text(content, encoding="utf-8")
    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    (p / (fname + ".sha256")).write_text(sha256)
    shutil.move(str(tmpf), str(final))
    (p / "current.json").write_text(content, encoding="utf-8")
    return final, sha256
```

Ansible pattern — gather facts on target, write JSON to control node
```yaml
- name: collect sp_server_facts and save on control node
  hosts: "{{ target_hosts }}"
  gather_facts: false
  tasks:
    - name: run sp_server_facts module
      ibm.storage_protect.sp_server_facts:
        q_status: true
        q_db: true
      register: sp_facts_result

    - name: prepare snapshot payload (mask secrets if any)
      set_fact:
        sp_snapshot: "{{ {'resource':'sp_server','collected_by':'sp_server_facts','collected_from':inventory_hostname,'timestamp':ansible_date_time.utc|default(ansible_date_time.iso8601),'data': sp_facts_result} }}"

    - name: write snapshot to control node (atomic)
      delegate_to: localhost
      run_once: true
      vars:
        ts: "{{ lookup('pipe','date -u +%Y%m%dT%H%M%SZ') }}"
        out_file: "reports/SpServerResponseMapper.{{ ts }}.json"
      copy:
        content: "{{ sp_snapshot | to_nice_json }}"
        dest: "{{ out_file }}"
        mode: '0640'
```

Access control & security
- Ensure file perms restrict access (0640), owner=ansible/control user.  
Retention & housekeeping
- Keep N latest snapshots (rotate); keep approved baseline(s) indefinitely.  

---

### Step 2 — Runtime Collection (`current.json`)
Component:
- Same module/playbook as baseline

Execution options:
- Scheduled 
- Or manual run

Output:
- Store `current.json` in `reports/`

---

### Step 3 — Comparison (diff engine)
Component:
- Local diff script (new)

```
python3 scripts/sp_config_diff.py baseline.json current.json --out diff_report.json --ignore-keys timestamp,last_checked
```

Action:
- Read baseline + current
- Normalize objects (remove volatile keys)
- Compute structured diff
- Output → `diff_report.json`


## 3. Script — Compare Baseline & Current → `diff_report.json`

## Abstract: compare baseline.json and current.json -> diff_report.json

### 1. Load inputs
baseline = load_json(path_to_baseline)    # returns nested dict/list
current  = load_json(path_to_current)

### 2. Preprocess / normalization
 - Remove or redact volatile keys (timestamps, counters) per ignore list
 - Canonicalize units and field names (e.g., sizes -> KB)
 - Sort lists deterministically or index-match by identifier (e.g., nodes by name)
baseline_norm = normalize(baseline, ignore_keys, list_key_rules, unit_rules)
current_norm  = normalize(current, ignore_keys, list_key_rules, unit_rules)

### 3. Quick equality check
if sha256(normalize_json(baseline_norm)) == sha256(normalize_json(current_norm)):
    report = minimal_no_change_report(meta)
    write_json(report_path, report)
    exit(0)

### 4. Recursive diff algorithm (dicts, lists, primitives)
 - For dict vs dict: keys present only in current -> added; only in baseline -> removed;
   present in both -> recurse and classify sub-diffs as unchanged/changed.
 - For lists:
   * If elements are primitives: compare as sets -> added/removed.
   * If elements are objects with stable id field: index by id and diff per element.
   * Otherwise fall back to index-based comparison and flag reordering.
diff = recursive_diff(baseline_norm, current_norm, list_id_keys)

### 5. Classify diffs (optional severity rules)
 - Map changed keys/values to severity levels (critical/major/minor/info)
 - Examples: service state stopped -> critical; package minor version change -> minor
severity_summary = classify_diff(diff, severity_rules)

### 6. Build report structure
report = {
    "resource": "sp_server_facts",
    "generated_at": now_utc(),
    "baseline": meta(baseline_path),
    "current": meta(current_path),
    "baseline_sha256": sha256(baseline_norm),
    "current_sha256": sha256(current_norm),
    "diff": diff,                        # added/removed/changed with old/new payloads
    "severity_summary": severity_summary,
    "notes": { "ignored_keys": ignore_keys, "normalization": applied_rules }
}

### 7. Output
write_json(diff_report_path, report)    # atomic write (tmp + move)
optionally_export_tabular(report, csv/xlsx/markdown)

### 8. Optional publish / automation
 - Push report to artifact store (S3, Git branch) or create PR (CI)
 - Trigger remediation playbook if auto-remediate is enabled and severity policy allows

### Configuration knobs to expose:
 - ignore_keys: list of top-level or nested keys to remove
 - list_id_keys: mapping of list paths -> identifier field (e.g., "nodes" -> "name")
 - unit_rules: normalize size/bytes/timestamps
 - severity_rules: match patterns => severity
 - atomic_write: True/False
 - publish_target: { type: git|s3|http, creds, path }

---
---

## 4. Configuration Parameters — Covered vs Not Covered  
(Updated to include SP Server Query Display Information)

### Covered (Extended)
The following configuration domains are collected through `sp_server_facts` using the underlying SP Server queries. These form the baseline for drift detection.

| Parameter / Query | Description (Display Information) |
|-------------------|------------------------------------|
| **query status** | Collects server-wide status information. |
| **query monitorsettings** | Collects monitoring thresholds and rules. |
| **query db** | Collects DB capacity and backup metadata. |
| **query dbspace** | Tablespace-level storage usage. |
| **query log** | Active/archive log usage. |
| **query domain** | Policy domain configuration. |
| **query copygroup** | Backup/archive copygroup rules. |
| **query replrule** | Replication rules. |
| **query devclass** | Device class info. |
| **query mgmtclass** | Management class lifecycle rules. |
| **query stgpool** | Storage pool definitions and usage. |
| **Hostnames, FQDN** | System identity information. |
| **OS metadata** | Linux/Windows version, kernel, architecture. |
| **Hardware summary** | CPU, memory, disk layout. |
| **Network configuration** | IPs, interfaces, service ports. |
| **Installed components** | SP server and client components. |
| **DSM adapters** | Definitions and configuration state. |
| **Packages** | Installed SP packages. |
| **Config files** | Parsed option files. |
| **Nodes summary** | Registered nodes. |
| **Schedules** | Server schedules. |
| **Storage agents** | Agent list and state. |
| **Alerts, audit logs** | Summary indicators. |
| **Checksums** | Snapshot-level checksums. |

---

## QUERY SYSTEM Consolidated Schema (Coverage Table)

| Query / Parameter Category | In Covered? | In Schema? | Gap Status | Description | Display Information |
|---------------------------|-------------|------------|------------|-------------|----------------------|
| STATUS | ✔ | ✔ | — | High-level server status | Server name, version, uptime, ports, licensing |
| MONITORSETTINGS | ✔ | ✔ | — | Monitoring thresholds | Thresholds, intervals, watchdog flags |
| DB | ✔ | ✔ | — | DB capacity | Total/used/free pages, last backup |
| DBSPACE | ✔ | ✔ | — | Tablespace usage | Tablespace name, used/free pages |
| LOG | ✔ | ✔ | — | Log usage | Log type, used/free |
| DOMAIN | ✔ | ✔ | — | Policy domain | Domain name, description |
| COPYGROUP | ✔ | ✔ | — | Copygroup rules | Retention rules |
| MGMTCLASS | ✔ | ✔ | — | Mgmt class rules | Retention values |
| DEVCLASS | ✔ | ✔ | — | Device class | Type, capacity |
| STGPOOL | ✔ | ✔ | — | Storage pools | Pool usage, thresholds |
| STGRULE | ❌ | ✔ | ⚠ Add | Migration rules | Rule name, pools |
| LIBRARY | ⚠ | ✔ | ⚠ Add | Library infra | Library name, type |
| DIRSPACE | ❌ | ✔ | ⚠ Add | Directory pool | Path, free space |
| REPLRULE | ✔ | ✔ | — | Replication rules | Source/target |
| REPLSERVER | ❌ | ✔ | ⚠ Add | Replication partners | Server name, port |
| SCHEDULE | ✔ | ✔ | — | Admin/client schedules | Name, action, time |
| SERVER (peer) | ⚠ | ✔ | ⚠ Add | Multi-server comms | HL/LL address |
| SESSION | ❌ | ✔ | ❌ Exclude | Runtime sessions | Volatile |
| PROCESS | ❌ | ✔ | ❌ Exclude | Server processes | Volatile |
| RETRULE | ❌ | ✔ | ⚠ Add | Retention rules | Retention days |
| RETSET | ❌ | ✔ | ⚠ Add | Retention sets | Volume count |
| VOLHISTORY | ❌ | ✔ | ⚠ Add | Backup history | Volume, timestamp |
| VOLUME | ⚠ | ✔ | ⚠ Enhance | Volume info | Pool, status |
| NODES | ✔ | — | — | Node registry | Node metadata |
| SCHEDULE ASSOC | ✔ | — | — | Node→Schedule | Associations |
| STORAGE AGENTS | ✔ | — | — | SA config | Agents, targets |
| Config Files | ✔ | — | — | Server config | Option files |
| Client Components | ✔ | — | — | Installed software | Version info |
| System Metadata | ✔ | — | — | OS/Hardware | CPU, memory |
| Checksums | ✔ | — | — | Integrity | Snapshot hash |

---



## 5. How to Run

```
python3 scripts/sp_config_diff.py baseline.json current.json --out diff_report.json --ignore-keys timestamp,last_checked
```

---

## 6. Recommended Next Tasks
- Add severity classification  
- Extend `sp_server_facts`  
- Create `drift_scan_playbook.yml`

A baseline configuration snapshot of the SP Server Database is saved as **baseline.json**.  
Periodic snapshots (**current.json**) are collected and compared to detect drift.


## 7. Example Snapshot JSON
(Full JSON preserved as per source document.)
```yaml
{
  "resource": "sp_server",
  "collected_by": "plugins/modules/sp_server_facts.py",
  "collected_from": "sp-server-01.example.com",
  "timestamp": "2025-11-27T13:45:00Z",
  "server": {
    "hostname": "sp-server-01.example.com",
    "fqdn": "sp-server-01.example.com",
    "os": {
      "name": "Red Hat Enterprise Linux",
      "version": "8.9",
      "kernel": "4.18.0-517.el8.x86_64",
      "architecture": "x86_64"
    },
    "hardware": {
      "cpu": {
        "model": "Intel(R) Xeon(R) Gold 6130",
        "cores": 32,
        "threads": 64
      },
      "memory_gb": 256,
      "disks": [
        {
          "device": "/dev/sda",
          "size_gb": 1024,
          "type": "nvme"
        },
        {
          "device": "/dev/sdb",
          "size_gb": 2048,
          "type": "nvme"
        }
      ]
    },
    "network": {
      "interfaces": [
        {
          "name": "eth0",
          "mac": "00:1A:4B:16:01:23",
          "ipv4": "10.0.1.10",
          "netmask": "255.255.255.0",
          "gateway": "10.0.1.1"
        },
        {
          "name": "mgmt0",
          "mac": "00:1A:4B:16:01:24",
          "ipv4": "192.168.100.10",
          "netmask": "255.255.255.0",
          "gateway": "192.168.100.1"
        }
      ],
      "dns": ["8.8.8.8", "8.8.4.4"]
    }
  },
  "installed_components": {
    "storage_protect_server": {
      "version": "8.1.25",
      "install_path": "/opt/ibm/storage_protect/server",
      "status": "running",
      "services": [
        {
          "name": "sp-server",
          "state": "running",
          "enabled": true
        },
        {
          "name": "sp-scheduler",
          "state": "running",
          "enabled": true
        }
      ]
    },
    "backup_archive_client": {
      "version": "8.1.25",
      "installed_nodes_count": 128
    },
    "operations_center": {
      "version": "3.2.1",
      "status": "not_installed"
    }
  },
  "dsm_adapters": {
    "dsmadmc_cli_version": "8.1.25.0",
    "dsmc_cli_version": "8.1.25.0",
    "imcl_version": null
  },
  "packages": [
    {
      "name": "python3",
      "version": "3.6.8",
      "source": "rpm"
    },
    {
      "name": "glibc",
      "version": "2.28",
      "source": "rpm"
    }
  ],
  "configuration_files": {
    "dsm.sys": {
      "path": "/opt/ibm/dsm/dsm.sys",
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "modified": "2025-10-12T08:15:22Z",
      "content_summary": {
        "node_name": null,
        "servers": [
          {
            "name": "MASTER",
            "address": "sp-server-01.example.com",
            "port": 1500
          }
        ]
      }
    },
    "dsm.opt": {
      "path": "/opt/ibm/dsm/dsm.opt",
      "sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
      "modified": "2025-11-03T15:34:10Z",
      "content_summary": {
        "options_count": 42
      }
    }
  },
  "nodes_summary": {
    "total_nodes": 128,
    "registered_nodes": 128,
    "nodes_sample": [
      {
        "name": "client-01",
        "type": "client",
        "policy_domain": "PD1",
        "last_registered": "2025-06-10T08:21:00Z",
        "dsm_client_version": "8.1.25"
      },
      {
        "name": "nas-02",
        "type": "nas",
        "policy_domain": "PD1",
        "schedules": ["daily_backup", "weekly_archive"]
      }
    ]
  },
  "schedules": {
    "total_schedules": 12,
    "schedules_sample": [
      {
        "name": "daily_backup",
        "type": "backup",
        "frequency": "daily",
        "last_run": "2025-11-27T02:00:00Z",
        "next_run": "2025-11-28T02:00:00Z"
      },
      {
        "name": "weekly_archive",
        "type": "archive",
        "frequency": "weekly",
        "last_run": "2025-11-23T03:00:00Z"
      }
    ]
  },
  "storage_agents": [
    {
      "name": "storage-agent-01",
      "type": "ibm_flashsystem",
      "version": "1.4.0",
      "configured_containers": 4,
      "status": "online"
    }
  ],
  "alerts_and_issues": {
    "critical_alerts": 0,
    "warnings": [
      {
        "id": "WARN-001",
        "message": "dsm.opt contains deprecated option 'old_opt_flag'",
        "first_seen": "2025-11-01T09:12:00Z"
      }
    ]
  },
  "audit": {
    "scan_id": "scan-20251127-134500-abcdef",
    "collected_by_user": "ansible",
    "collection_method": "dsmadmc_queries + local file reads",
    "notes": "Snapshot excludes sensitive fields (passwords masked)"
  },
  "raw_outputs": {
    "dsmadmc_server_show": "Server: MASTER ...\nNodes: 128\nSchedules: 12\n",
    "dsmadmc_list_nodes": "client-01 | client | PD1 | 8.1.25\nnas-02 | nas | PD1 | 8.1.25\n..."
  },
  "checksums": {
    "snapshot_sha256": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0"
  }
}
```

## 8. Example drift_report.json
(Full JSON preserved.)
```yaml
{
  "resource": "sp_server_facts",
  "generated_at": "2025-11-27T14:45:00Z",
  "previous_snapshot": {
    "name": "SpServerResponseMapper.20251126-120000.json",
    "collected_at": "2025-11-26T12:00:00Z"
  },
  "current_snapshot": {
    "name": "SpServerResponseMapper.20251127-134500.json",
    "collected_at": "2025-11-27T13:45:00Z",
    "path": "reports/SpServerResponseMapper.20251127-134500.json"
  },
  "diff": {
    "added": {
      "nodes": [
        {
          "name": "client-129",
          "type": "client",
          "policy_domain": "PD1",
          "dsm_client_version": "8.1.25",
          "last_registered": "2025-11-27T02:10:00Z"
        }
      ]
    },
    "removed": {
      "storage_agents": []
    },
    "changed": {
      "storage_pools": {
        "stgpool1": {
          "old": {
            "name": "stgpool1",
            "total_gb": 10240,
            "used_gb": 6144,
            "status": "online"
          },
          "new": {
            "name": "stgpool1",
            "total_gb": 12288,
            "used_gb": 7168,
            "status": "online"
          }
        }
      },
      "nodes": {
        "client-01": {
          "old": {
            "dsm_client_version": "8.1.23",
            "schedules": [
              "daily_backup",
              "weekly_archive"
            ]
          },
          "new": {
            "dsm_client_version": "8.1.25",
            "schedules": [
              "daily_backup",
              "weekly_archive"
            ]
          }
        }
      },
      "services": {
        "sp-scheduler": {
          "old": {
            "state": "running",
            "enabled": true
          },
          "new": {
            "state": "stopped",
            "enabled": true
          }
        }
      },
      "packages": {
        "python3": {
          "old": {
            "version": "3.6.8",
            "source": "rpm"
          },
          "new": {
            "version": "3.6.9",
            "source": "rpm"
          }
        }
      },
      "schedules": {
        "daily_backup": {
          "old": {
            "next_run": "2025-11-27T02:00:00Z"
          },
          "new": {
            "next_run": "2025-11-28T02:00:00Z"
          }
        }
      },
      "configuration_files": {
        "dsm.opt": {
          "old": {
            "sha256": "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            "options_count": 42
          },
          "new": {
            "sha256": "d41d8cd98f00b204e9800998ecf8427e",
            "options_count": 44
          }
        }
      }
    }
  },
  "previous_sha256": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
  "current_sha256": "b3b2f6d9f1e7c4a6e8a4d9c0f3a2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a",
  "notes": {
    "volatile_keys_ignored": [
      "timestamp",
      "last_checked"
    ],
    "sensitive_masking": [
      "passwords masked in both snapshots"
    ]
  }
}
```
## 9. Tabular Diff Summary
### Added
| Resource | Key | Details |
|---------|-----|---------|
| nodes | client-129 | type: client; PD1; version 8.1.25 |

### Removed
| Resource | Details |
|----------|---------|
| storage_agents | None |

### Changed — Storage Pools
| Pool | Field | Previous | Current |
|------|--------|----------|----------|
| stgpool1 | total_gb | 10240 | 12288 |
| stgpool1 | used_gb | 6144 | 7168 |

### Changed — Nodes
| Node | Field | Previous | Current |
|------|--------|----------|----------|
| client-01 | dsm_client_version | 8.1.23 | 8.1.25 |

### Changed — Services
| Service | Field | Previous | Current |
|---------|--------|----------|----------|
| sp-scheduler | state | running | stopped |

### Changed — Packages
| Package | Field | Previous | Current |
|---------|--------|----------|----------|
| python3 | version | 3.6.8 | 3.6.9 |

### Changed — configuration_files (dsm.opt)
| File | Field | Previous | Current |
|------|--------|----------|----------|
| dsm.opt | sha256 | oldhash | newhash |
| dsm.opt | options_count | 42 | 44 |

## 10. Are Data Points Enough?
Recommended additions include firmware, driver versions, certificate metadata, firewall rules, and replication metrics.


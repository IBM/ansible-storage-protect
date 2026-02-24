# Ansible Role: sp_server_facts

This Ansible role retrieves IBM Storage Protect Server facts using the `sp_server_facts` module and performs per-host configuration drift reporting.

It now supports:
- fact collection controlled by `sp_server_facts_flags`
- per-host snapshot generation
- baseline/current drift comparison
- coverage metrics (enabled queries, per-query field counts, totals)
- downloadable per-host report bundles

## Requirements

- Ansible 2.9+
- The `sp_server_facts` module must be installed and accessible
- Access to a running Storage Protect Server (SP) with valid credentials

## Environment Variables

Before running the playbook, set:

```bash
export STORAGE_PROTECT_SERVERNAME="your_server_name"
export STORAGE_PROTECT_USERNAME="your_username"
export STORAGE_PROTECT_PASSWORD="your_password"
```

## Role Variables

### Fact Collection Configuration

Use `sp_server_facts_flags` to enable or disable specific queries.

| Key                 | Description                           | Default |
|---------------------|---------------------------------------|---------|
| `q_status`          | Collect server status information     | `false` |
| `q_monitorsettings` | Collect monitor settings information  | `false` |
| `q_db`              | Collect database information          | `false` |
| `q_dbspace`         | Collect database space information    | `false` |
| `q_log`             | Collect log information               | `false` |
| `q_domain`          | Collect domain information            | `false` |
| `q_copygroup`       | Collect copy group information        | `false` |
| `q_replrule`        | Collect replication rule information  | `false` |
| `q_devclass`        | Collect device class information      | `false` |
| `q_mgmtclass`       | Collect management class information  | `false` |
| `q_stgpool`         | Collect storage pool information      | `false` |

## Multi-Server Behavior

The role runs for each host in the play and writes per-host outputs on the control node.

Generated files per host (`<host>` = `inventory_hostname`):

- `reports/current_<host>.json`
- `reports/baseline_<host>.json`
- `reports/drift_report_<host>.json`
- `reports/drift_report_<host>.html`
- `reports/drift_report_bundle_<host>.zip`
- `reports/sp_field_distribution_<host>.md`

## Snapshot Schema Requirement

Drift comparison expects this structure in snapshot JSON:

```json
{
  "data": {
    "ansible_module_results": {
      "q_status": {}
    }
  }
}
```

## Coverage in Report

Each snapshot includes:
- `enabled_queries`
- `total_queries`
- `query_coverage_pct`
- `total_returned_fields`
- `per_query_field_counts`

These are rendered in drift report HTML and saved in drift report JSON.

## Classification in Drift Report

Drift entries are classified by query module:
- Policies: `q_copygroup`, `q_replrule`
- Domains: `q_domain`
- Management Classes: `q_mgmtclass`
- Device classes: `q_devclass`
- Storage hierarchies: `q_stgpool`
- Node configurations: `q_status`, `q_monitorsettings`, `q_db`, `q_dbspace`, `q_log`

## Example Inventory (Multi-Host)

```ini
[vms]
v1 ansible_host=10.0.0.11
v2 ansible_host=10.0.0.12
v3 ansible_host=10.0.0.13

[all:vars]
ansible_user=your_user
ansible_connection=ssh
```

## Example vars file

```yaml
# vars.yml
sp_server_facts_flags:
  q_status: true
  q_monitorsettings: true
  q_db: true
  q_dbspace: true
  q_log: true
  q_domain: true
  q_copygroup: true
  q_replrule: true
  q_devclass: true
  q_mgmtclass: true
  q_stgpool: true
```

## Run

- Example playbooks are available under the playbooks directory of [IBM/ansible-storage-protect](https://github.com/IBM/ansible-storage-protect/tree/main/playbooks/)
- `target_hosts` can be passed at runtime; default is `all`

```bash
ansible-playbook -i inventory.ini ibm.storage_protect.sp_server_facts_playbook.yml -e @vars.yml
```

## Baseline Acceptance

After drift generation, the role prompts:
- `Accept drift changes and update baseline_<host>.json files? (yes/no)`

If `yes`, the baseline is updated for each host in the play.

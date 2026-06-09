# Single-Site Disk Solution - Folder Structure

## Overview

This document describes the restructured folder organization for the Single-Site Disk Solution, aligned with IBM Storage Protect 8.2.1 documentation.

**Reference:** https://www.ibm.com/docs/en/storage-protect/8.2.1?topic=deployment-single-site-disk-solution

---

## Directory Structure

```
single-site-disk/
├── README.md                          # Solution documentation
├── STRUCTURE.md                       # This file
├── requirements.yml                   # Ansible dependencies
│
├── inventory/
│   └── production.ini                 # Inventory file
│
├── group_vars/
│   ├── sp_servers.yml                 # Server configuration variables
│   └── ba_clients.yml                 # Client configuration variables
│
├── vars/
│   ├── dp_db2_client_vars.yml        # DB2 client variables (if needed)
│   └── ...                            # Other variable files
│
├── playbooks/
│   ├── server/                        # Server lifecycle management
│   │   ├── sp_server_install_playbook.yml
│   │   ├── sp_server_configure_playbook.yml
│   │   ├── sp_server_upgrade_playbook.yml
│   │   └── sp_server_uninstall_playbook.yml
│   │
│   ├── client/                        # Client lifecycle management
│   │   ├── ba_client_facts_playbook.yml
│   │   └── ba_client_install/
│   │       ├── vars/
│   │       │   └── main.yml
│   │       └── playbooks/
│   │           ├── linux/
│   │           │   ├── ba_client_install_playbook.yml
│   │           │   ├── ba_client_uninstall_playbook.yml
│   │           │   └── ba_client_facts_playbook.yml
│   │           ├── windows/
│   │           │   ├── ba_client_install_playbook.yml
│   │           │   ├── ba_client_uninstall_playbook.yml
│   │           │   ├── ba_client_facts_playbook.yml
│   │           │   └── README_BA_CLIENT_FACTS.md
│   │           └── aix/
│   │               ├── ba_client_install_playbook.yml
│   │               ├── ba_client_uninstall_playbook.yml
│   │               └── ba_client_facts_playbook.yml
│   │
│   ├── storage/                       # Storage management
│   │   ├── storage_prepare_playbook.yml
│   │   └── storage_cleanup_playbook.yml
│   │
│   └── operations/                    # Operational tasks
│       └── sp_server_facts_playbook.yml
│
├── roles/                             # Vendored Ansible roles (17 roles)
│   ├── ba_client_install/
│   ├── dp_db2_manage/
│   ├── dp_db2_postcheck/
│   ├── dp_db2_precheck/
│   ├── dsm_opt/
│   ├── erp_install/
│   ├── global_vars/
│   ├── node_file_backup/
│   ├── nodes/
│   ├── oc_configure/
│   ├── python_version_install/
│   ├── schedules/
│   ├── sp_server_facts/
│   ├── sp_server_install/
│   ├── storage_agent_configure/
│   ├── storage_prepare/
│   └── system_info/
│
└── plugins/                           # Vendored Ansible modules (26 files)
    ├── README.md
    ├── doc_fragments/
    │   └── auth.py
    ├── module_utils/
    │   ├── ba_client_facts.py
    │   ├── ba_client_updated_linux_win_aix.py
    │   ├── ba_client_utils.py
    │   ├── dsmadmc_adapter.py
    │   ├── dsmc_adapter.py
    │   ├── sp_server_constants.py
    │   ├── sp_server_facts.py
    │   ├── sp_server_utils.py
    │   └── sp_utils.py
    └── modules/
        ├── ba_client_facts.py
        ├── ba_client_install.py
        ├── diff_analyse.py
        ├── dsm_sysfile.py
        ├── node_file_backup.py
        ├── node.py
        ├── oc_configure.py
        ├── schedule.py
        ├── sp_baclient_install_lin_win_aix.py
        ├── sp_baclient_install.py
        ├── sp_server_configure.py
        ├── sp_server_facts.py
        ├── sp_server.py
        ├── storage_agent_config.py
        ├── orchestrations/
        │   └── ORCH_ba_serverinstall.py
        └── tasks/
            └── utils.py
```

---

## Playbook Organization

### 1. Server Playbooks (`playbooks/server/`)

**Purpose:** Manage the IBM Storage Protect Server lifecycle

| Playbook | Function | When to Use |
|----------|----------|-------------|
| `sp_server_install_playbook.yml` | Install SP Server | Initial deployment |
| `sp_server_configure_playbook.yml` | Configure SP Server | Post-installation, reconfiguration |
| `sp_server_upgrade_playbook.yml` | Upgrade SP Server | Version upgrades |
| `sp_server_uninstall_playbook.yml` | Uninstall SP Server | Decommissioning |

**Key Features:**
- Automated installation with response files
- Policy domain and storage pool configuration
- Database setup and tuning
- Service management

---

### 2. Client Playbooks (`playbooks/client/`)

**Purpose:** Deploy and manage Backup-Archive clients across platforms

| Platform | Install | Uninstall | Facts |
|----------|---------|-----------|-------|
| **Linux** | `ba_client_install/playbooks/linux/ba_client_install_playbook.yml` | `ba_client_uninstall_playbook.yml` | `ba_client_facts_playbook.yml` |
| **Windows** | `ba_client_install/playbooks/windows/ba_client_install_playbook.yml` | `ba_client_uninstall_playbook.yml` | `ba_client_facts_playbook.yml` |
| **AIX** | `ba_client_install/playbooks/aix/ba_client_install_playbook.yml` | `ba_client_uninstall_playbook.yml` | `ba_client_facts_playbook.yml` |

**Key Features:**
- Multi-platform support (Linux, Windows, AIX)
- Automated node registration
- Client configuration (dsm.opt, dsm.sys)
- Service/daemon setup

---

### 3. Storage Playbooks (`playbooks/storage/`)

**Purpose:** Manage disk storage infrastructure

| Playbook | Function | When to Use |
|----------|----------|-------------|
| `storage_prepare_playbook.yml` | Prepare disk storage | Pre-deployment, expansion |
| `storage_cleanup_playbook.yml` | Cleanup storage | Decommissioning, maintenance |

**Key Features:**
- Disk pool creation and configuration
- File system preparation
- Storage validation
- Cleanup and reclamation

---

### 4. Operations Playbooks (`playbooks/operations/`)

**Purpose:** Operational monitoring and management

| Playbook | Function | When to Use |
|----------|----------|-------------|
| `sp_server_facts_playbook.yml` | Collect server state | Monitoring, troubleshooting, validation |

**Key Features:**
- Server status collection
- Configuration validation
- Performance metrics
- Health checks

---

## Changes from Previous Structure

### Removed Playbooks

The following playbooks were **removed** as they are not core to a basic single-site disk solution:

1. **DB2-Specific Playbooks** (moved to database protection add-on)
   - `dp_db2_install_playbook.yml`
   - `dp_db2_backup_playbook.yml`
   - `dp_db2_restore_playbook.yml`
   - `dp_db2_query_playbook.yml`
   - `dp_db2_delete_playbook.yml`

**Rationale:** Database protection is an advanced feature, not required for basic file/system backup scenarios.

### Reorganized Structure

**Before:**
```
playbooks/
├── sp_server_install_playbook.yml
├── sp_server_configure_playbook.yml
├── ba_client_install_playbook.yml
├── dp_db2_backup_playbook.yml
└── ...
```

**After:**
```
playbooks/
├── server/
│   ├── sp_server_install_playbook.yml
│   └── sp_server_configure_playbook.yml
├── client/
│   └── ba_client_install/
├── storage/
│   └── storage_prepare_playbook.yml
└── operations/
    └── sp_server_facts_playbook.yml
```

**Benefits:**
- Clear functional separation
- Easier navigation
- Better alignment with IBM documentation
- Simplified deployment workflows

---

## Deployment Workflow

### Standard Deployment Sequence

```
1. Storage Preparation
   └─> playbooks/storage/storage_prepare_playbook.yml

2. Server Installation
   └─> playbooks/server/sp_server_install_playbook.yml

3. Server Configuration
   └─> playbooks/server/sp_server_configure_playbook.yml

4. Client Deployment (per platform)
   ├─> playbooks/client/ba_client_install/playbooks/linux/ba_client_install_playbook.yml
   ├─> playbooks/client/ba_client_install/playbooks/windows/ba_client_install_playbook.yml
   └─> playbooks/client/ba_client_install/playbooks/aix/ba_client_install_playbook.yml

5. Validation
   └─> playbooks/operations/sp_server_facts_playbook.yml
```

---

## Validation Checklist

- [x] Playbooks organized by function (server, client, storage, operations)
- [x] DB2-specific playbooks removed
- [x] Multi-platform client support maintained
- [x] All roles and plugins vendored
- [x] No external dependencies (except ansible.builtin)
- [x] Documentation updated
- [x] Aligned with IBM single-site disk solution architecture

---

## Playbook Count Summary

| Category | Count | Description |
|----------|-------|-------------|
| **Server** | 4 | Install, configure, upgrade, uninstall |
| **Client** | 10 | 3 platforms × (install, uninstall, facts) + 1 generic facts |
| **Storage** | 2 | Prepare, cleanup |
| **Operations** | 1 | Server facts collection |
| **Total** | 17 | Core playbooks for single-site disk solution |

**Removed:** 5 DB2-specific playbooks

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-19 | Initial structure with all playbooks |
| 2.0.0 | 2026-05-20 | Restructured based on IBM documentation, removed DB2 playbooks |

---

## References

- IBM Storage Protect 8.2.1 Documentation: https://www.ibm.com/docs/en/storage-protect/8.2.1
- Single-Site Disk Solution: https://www.ibm.com/docs/en/storage-protect/8.2.1?topic=deployment-single-site-disk-solution
- Solution README: [`README.md`](README.md)
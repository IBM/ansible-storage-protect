# Tape Archival Solution - Folder Structure

## Overview

This document describes the restructured folder organization for the Tape Archival Solution, aligned with IBM Storage Protect 8.2.1 documentation.

**Reference:** https://www.ibm.com/docs/en/storage-protect/8.2.1?topic=deployment-tape-solution

---

## Directory Structure

```
tape-archival/
├── README.md                          # Solution documentation
├── STRUCTURE.md                       # This file
├── requirements.yml                   # Ansible dependencies
│
├── inventory/
│   └── production.ini                 # Inventory file
│
├── group_vars/
│   ├── sp_servers.yml                 # Server configuration
│   ├── storage_agents.yml             # Storage agent configuration
│   └── tape_libraries.yml             # Tape library configuration
│
├── playbooks/
│   ├── server/                        # Server lifecycle
│   │   ├── sp_server_install_playbook.yml
│   │   └── sp_server_configure_playbook.yml
│   │
│   ├── storage-agent/                 # Tape library management
│   │   ├── storage_agent_configure_playbook.yml
│   │   ├── storage_prepare_playbook.yml
│   │   └── storage_cleanup_playbook.yml
│   │
│   ├── client/                        # Client lifecycle
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
│   └── operations/                    # Operational tasks
│       └── sp_server_facts_playbook.yml
│
├── roles/                             # Vendored Ansible roles (17 roles)
└── plugins/                           # Vendored Ansible modules (26 files)
```

---

## Playbook Organization

### 1. Server Playbooks (`playbooks/server/`)

**Purpose:** Manage SP Server lifecycle with tape support

| Playbook | Function | Usage |
|----------|----------|-------|
| `sp_server_install_playbook.yml` | Install SP Server | Initial deployment |
| `sp_server_configure_playbook.yml` | Configure SP Server for tape | Post-installation, tape pool setup |

**Key Features:**
- Tape-aware configuration
- Storage pool management (tape pools)
- Device class configuration
- Library integration

---

### 2. Storage Agent & Tape Library Playbooks (`playbooks/storage-agent/`)

**Purpose:** Manage tape library and storage agent

| Playbook | Function | Usage |
|----------|----------|-------|
| `storage_agent_configure_playbook.yml` | Configure storage agent | Tape library integration |
| `storage_prepare_playbook.yml` | Prepare tape devices | Pre-deployment, device discovery |
| `storage_cleanup_playbook.yml` | Cleanup tape resources | Decommissioning, maintenance |

**Key Features:**
- Tape library definition
- Drive configuration
- Device class setup
- SAN/FC connectivity
- Automated library audit

---

### 3. Client Playbooks (`playbooks/client/`)

**Purpose:** Deploy and manage Backup-Archive clients

| Platform | Install | Uninstall | Facts |
|----------|---------|-----------|-------|
| **Linux** | `ba_client_install/playbooks/linux/ba_client_install_playbook.yml` | `ba_client_uninstall_playbook.yml` | `ba_client_facts_playbook.yml` |
| **Windows** | `ba_client_install/playbooks/windows/ba_client_install_playbook.yml` | `ba_client_uninstall_playbook.yml` | `ba_client_facts_playbook.yml` |
| **AIX** | `ba_client_install/playbooks/aix/ba_client_install_playbook.yml` | `ba_client_uninstall_playbook.yml` | `ba_client_facts_playbook.yml` |

**Key Features:**
- Multi-platform support
- Automated node registration
- Client configuration (dsm.opt, dsm.sys)
- Service/daemon setup

---

### 4. Operations Playbooks (`playbooks/operations/`)

**Purpose:** Operational monitoring and management

| Playbook | Function | Usage |
|----------|----------|-------|
| `sp_server_facts_playbook.yml` | Collect server state | Monitoring, tape library status |

**Key Features:**
- Server status collection
- Tape library status
- Drive utilization
- Mount queue monitoring

---

## Changes from Previous Structure

### Added Playbooks

The following playbooks were **added** to complete the tape solution:

1. **Server Playbooks** (copied from main collection)
   - `sp_server_install_playbook.yml`
   - `sp_server_configure_playbook.yml`

2. **Storage Playbooks** (copied from main collection)
   - `storage_prepare_playbook.yml`
   - `storage_cleanup_playbook.yml`

3. **Operations Playbooks** (copied from main collection)
   - `sp_server_facts_playbook.yml`

**Rationale:** The original tape-archival solution was incomplete, missing essential server and storage management playbooks.

### Reorganized Structure

**Before:**
```
playbooks/
├── storage_agent_configure_playbook.yml
├── ba_client_facts_playbook.yml
└── ba_client_install/
```

**After:**
```
playbooks/
├── server/
│   ├── sp_server_install_playbook.yml
│   └── sp_server_configure_playbook.yml
├── storage-agent/
│   ├── storage_agent_configure_playbook.yml
│   ├── storage_prepare_playbook.yml
│   └── storage_cleanup_playbook.yml
├── client/
│   └── ba_client_install/
└── operations/
    └── sp_server_facts_playbook.yml
```

**Benefits:**
- Complete tape solution lifecycle
- Clear functional separation
- Better alignment with IBM tape solution architecture
- Simplified deployment workflows

---

## Deployment Workflow

### Standard Tape Solution Deployment Sequence

```
Phase 1: Server Deployment
├─> 1. playbooks/server/sp_server_install_playbook.yml
└─> 2. playbooks/server/sp_server_configure_playbook.yml (storage_type=tape)

Phase 2: Tape Infrastructure
├─> 3. playbooks/storage-agent/storage_prepare_playbook.yml (storage_type=tape)
└─> 4. playbooks/storage-agent/storage_agent_configure_playbook.yml

Phase 3: Client Deployment
└─> 5. playbooks/client/ba_client_install/playbooks/*/ba_client_install_playbook.yml

Phase 4: Validation
└─> 6. playbooks/operations/sp_server_facts_playbook.yml (check_tape_library=true)
```

---

## Tape-Specific Features

### 1. Tape Library Configuration

The storage agent playbook automates tape library setup:

```yaml
# group_vars/storage_agents.yml
tape_library_config:
  library_name: "TAPELIB01"
  library_type: "SCSI"  # or "ACSLS", "349X"
  drives:
    - name: "DRIVE01"
      device: "/dev/smc0"
      type: "LTO8"
    - name: "DRIVE02"
      device: "/dev/smc1"
      type: "LTO8"
  device_class: "TAPECLASS"
  storage_pool: "TAPEPOOL"
```

### 2. Hierarchical Storage Management (HSM)

Configure automatic migration from disk to tape:

```yaml
# group_vars/sp_servers.yml
hsm_enabled: true
hsm_migration_days: 90
hsm_source_pool: "DISKPOOL"
hsm_target_pool: "TAPEPOOL"
```

### 3. Tape Reclamation

Automated tape reclamation configuration:

```yaml
# group_vars/sp_servers.yml
tape_reclamation:
  enabled: true
  threshold: 60  # Reclaim when 60% fragmented
  schedule: "DAILY 02:00"
```

### 4. Off-Site Vaulting

Support for tape checkout/checkin workflows:

```yaml
# group_vars/tape_libraries.yml
offsite_vaulting:
  enabled: true
  vault_location: "OFFSITE_VAULT"
  checkout_schedule: "WEEKLY"
  retention_days: 2555  # 7 years
```

---

## Tape Library Types

### Supported Libraries

1. **IBM TS Series**
   - TS4500 (Enterprise)
   - TS4300 (Mid-range)
   - TS3500 (Legacy)
   - TS3310 (Entry)

2. **LTO Libraries**
   - HP MSL Series
   - Dell ML3 Series
   - Quantum Scalar Series

3. **Virtual Tape Libraries (VTL)**
   - IBM ProtecTIER
   - Dell EMC Data Domain
   - Quantum DXi

### Library Connection Types

- **SCSI:** Direct-attached libraries
- **FC (Fibre Channel):** SAN-attached libraries
- **ACSLS:** Automated Cartridge System Library Software
- **349X:** IBM 3494 library protocol

---

## Validation Checklist

- [x] Playbooks organized by function (server, storage-agent, client, operations)
- [x] Server playbooks added for complete lifecycle
- [x] Storage preparation playbooks added
- [x] Multi-platform client support maintained
- [x] Tape library configuration automated
- [x] All roles and plugins vendored
- [x] No external dependencies (except ansible.builtin)
- [x] Documentation updated
- [x] Aligned with IBM tape solution architecture

---

## Playbook Count Summary

| Category | Count | Description |
|----------|-------|-------------|
| **Server** | 2 | Install, configure (tape-aware) |
| **Storage Agent** | 3 | Configure, prepare, cleanup |
| **Client** | 10 | 3 platforms × (install, uninstall, facts) + 1 generic facts |
| **Operations** | 1 | Server facts collection |
| **Total** | 16 | Core playbooks for tape archival solution |

**Added:** 5 playbooks (2 server + 2 storage + 1 operations)

---

## Tape Management Operations

### Daily Operations

```bash
# Check tape library status
ansible-playbook -i inventory/production.ini \
  playbooks/operations/sp_server_facts_playbook.yml \
  -e "check_tape_library=true"

# Monitor tape mounts
dsmadmc -id=admin "QUERY MOUNT"

# Check drive utilization
dsmadmc -id=admin "QUERY DRIVE * F=D"
```

### Weekly Operations

```bash
# Audit tape library
dsmadmc -id=admin "AUDIT LIBRARY TAPELIB01"

# Check reclamation candidates
dsmadmc -id=admin "QUERY VOLUME * STGPOOL=TAPEPOOL"

# Checkout tapes for off-site
dsmadmc -id=admin "CHECKOUT LIBVOLUME TAPELIB01 SEARCH=YES"
```

### Monthly Operations

```bash
# Inventory verification
dsmadmc -id=admin "QUERY LIBVOLUME TAPELIB01"

# Drive maintenance check
dsmadmc -id=admin "QUERY DRIVE * F=D"

# Clean drives
dsmadmc -id=admin "CLEAN DRIVE TAPELIB01 *"
```

---

## Troubleshooting Guide

### Common Issues

**1. Library Not Detected**
```bash
# Check SAN connectivity
ansible -i inventory/production.ini storage_agents \
  -m shell -a "lsscsi -g"

# Verify library definition
dsmadmc -id=admin "QUERY LIBRARY TAPELIB01 F=D"
```

**2. Drive Errors**
```bash
# Check drive status
dsmadmc -id=admin "QUERY DRIVE TAPELIB01 F=D"

# Clean drive
dsmadmc -id=admin "CLEAN DRIVE TAPELIB01 DRIVE01"

# Reset drive
dsmadmc -id=admin "DISABLE DRIVE TAPELIB01 DRIVE01"
dsmadmc -id=admin "ENABLE DRIVE TAPELIB01 DRIVE01"
```

**3. Mount Failures**
```bash
# Check mount queue
dsmadmc -id=admin "QUERY MOUNT"

# Check available tapes
dsmadmc -id=admin "QUERY LIBVOLUME TAPELIB01 STATUS=SCRATCH"

# Cancel stuck mount
dsmadmc -id=admin "CANCEL MOUNT <request_number>"
```

**4. Reclamation Issues**
```bash
# Check reclamation status
dsmadmc -id=admin "QUERY PROCESS"

# Check fragmentation
dsmadmc -id=admin "QUERY VOLUME * STGPOOL=TAPEPOOL"

# Manual reclamation
dsmadmc -id=admin "RECLAIM STGPOOL TAPEPOOL THRESHOLD=60"
```

---

## Performance Tuning

### Drive Optimization

```yaml
# group_vars/storage_agents.yml
drive_optimization:
  max_concurrent_mounts: 8
  mount_retention: 60  # minutes
  mount_limit: 10  # per session
  data_format: "NATIVE"  # or "COMPRESSED"
```

### Network Optimization

```yaml
# group_vars/sp_servers.yml
network_optimization:
  tcp_window_size: "8MB"
  tcp_buffer_size: "4MB"
  max_sessions: 100
```

### Reclamation Optimization

```yaml
# group_vars/sp_servers.yml
reclamation_optimization:
  threshold: 60
  max_processes: 4
  schedule: "DAILY 02:00"
  duration: "4 HOURS"
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-19 | Initial structure (incomplete) |
| 2.0.0 | 2026-05-25 | Complete restructure with all required playbooks |

---

## References

- IBM Storage Protect 8.2.1 Documentation: https://www.ibm.com/docs/en/storage-protect/8.2.1
- Tape Solution: https://www.ibm.com/docs/en/storage-protect/8.2.1?topic=deployment-tape-solution
- Solution README: [`README.md`](README.md)
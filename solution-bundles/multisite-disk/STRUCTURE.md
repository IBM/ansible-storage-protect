# Multi-Site Disk Solution - Folder Structure

## Overview

This document describes the restructured folder organization for the Multi-Site Disk Solution, aligned with IBM Storage Protect 8.2.1 documentation.

**Reference:** https://www.ibm.com/docs/en/storage-protect/8.2.1?topic=deployment-multisite-disk-solution

---

## Directory Structure

```
multisite-disk/
├── README.md                          # Solution documentation
├── STRUCTURE.md                       # This file
├── requirements.yml                   # Ansible dependencies
│
├── inventory/
│   ├── primary_site.ini               # Primary site inventory
│   └── secondary_site.ini             # Secondary site inventory
│
├── group_vars/
│   ├── primary_servers.yml            # Primary site configuration
│   ├── secondary_servers.yml          # Secondary site configuration
│   └── all.yml                        # Common variables
│
├── vars/
│   ├── small_server_vars.yml          # Small deployment config
│   ├── medium_server_vars.yml         # Medium deployment config
│   ├── large_server_vars.yml          # Large deployment config
│   └── xsmall_server_vars.yml         # Extra-small deployment config
│
├── playbooks/
│   ├── server/                        # Server lifecycle (both sites)
│   │   ├── sp_server_install_playbook.yml
│   │   ├── sp_server_configure_playbook.yml
│   │   ├── sp_server_upgrade_playbook.yml
│   │   └── storage_prepare_playbook.yml
│   │
│   ├── client/                        # Client lifecycle (both sites)
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
│   ├── replication/                   # Replication management
│   │   └── (placeholder for future replication playbooks)
│   │
│   ├── monitoring/                    # Centralized monitoring
│   │   ├── oc_configure_playbook.yml
│   │   └── sp_server_facts_playbook.yml
│   │
│   └── security/                      # Security & certificates
│       └── cert_distribute.yml
│
├── roles/                             # Vendored Ansible roles
└── plugins/                           # Vendored Ansible modules
```

---

## Playbook Organization

### 1. Server Playbooks (`playbooks/server/`)

**Purpose:** Manage SP Server lifecycle at both primary and secondary sites

| Playbook | Function | Sites |
|----------|----------|-------|
| `sp_server_install_playbook.yml` | Install SP Server | Primary, Secondary |
| `sp_server_configure_playbook.yml` | Configure SP Server | Primary, Secondary |
| `sp_server_upgrade_playbook.yml` | Upgrade SP Server | Primary, Secondary |
| `storage_prepare_playbook.yml` | Prepare disk storage | Primary, Secondary |

**Key Features:**
- Site-aware configuration (primary vs secondary)
- Replication setup
- Storage pool configuration
- Network configuration for inter-site communication

---

### 2. Client Playbooks (`playbooks/client/`)

**Purpose:** Deploy and manage Backup-Archive clients at both sites

| Platform | Install | Uninstall | Facts |
|----------|---------|-----------|-------|
| **Linux** | `ba_client_install/playbooks/linux/ba_client_install_playbook.yml` | `ba_client_uninstall_playbook.yml` | `ba_client_facts_playbook.yml` |
| **Windows** | `ba_client_install/playbooks/windows/ba_client_install_playbook.yml` | `ba_client_uninstall_playbook.yml` | `ba_client_facts_playbook.yml` |
| **AIX** | `ba_client_install/playbooks/aix/ba_client_install_playbook.yml` | `ba_client_uninstall_playbook.yml` | `ba_client_facts_playbook.yml` |

**Key Features:**
- Multi-platform support
- Site-specific server configuration
- Failover server configuration
- Automated node registration

---

### 3. Replication Playbooks (`playbooks/replication/`)

**Purpose:** Manage data replication between sites

**Status:** Placeholder directory for future development

**Planned Features:**
- Configure node replication
- Monitor replication status
- Manage replication schedules
- Handle replication failures

**Current Implementation:**
Replication is currently configured via the `sp_server_configure_playbook.yml` with appropriate variables.

---

### 4. Monitoring Playbooks (`playbooks/monitoring/`)

**Purpose:** Centralized monitoring and management

| Playbook | Function | Scope |
|----------|----------|-------|
| `oc_configure_playbook.yml` | Configure Operations Center | Cross-site monitoring |
| `sp_server_facts_playbook.yml` | Collect server state | Both sites |

**Key Features:**
- Multi-server dashboard
- Cross-site alerting
- Performance monitoring
- Capacity planning
- Compliance reporting

---

### 5. Security Playbooks (`playbooks/security/`)

**Purpose:** Security configuration and certificate management

| Playbook | Function | Scope |
|----------|----------|-------|
| `cert_distribute.yml` | Distribute SSL/TLS certificates | Cross-site |

**Key Features:**
- Certificate distribution
- SSL/TLS configuration
- Secure inter-site communication
- Certificate renewal automation

---

## Changes from Previous Structure

### Removed Playbooks

The following playbooks were **removed** as they are not core to a multi-site disk solution:

1. **DB2-Specific Playbooks** (moved to database protection add-on)
   - `dp_db2_install_playbook.yml`
   - `dp_db2_backup_playbook.yml`
   - `dp_db2_restore_playbook.yml`
   - `dp_db2_query_playbook.yml`

2. **Blueprint Playbook** (specific to blueprint configuration solution)
   - `sp_server_blueprint_playbook.yml`

**Rationale:** Multi-site solution focuses on replication and disaster recovery, not database-specific protection or IaC templates.

### Reorganized Structure

**Before:**
```
playbooks/
├── sp_server_install_playbook.yml
├── sp_server_configure_playbook.yml
├── oc_configure_playbook.yml
├── cert_distribute.yml
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
├── replication/
│   └── (placeholder)
├── monitoring/
│   ├── oc_configure_playbook.yml
│   └── sp_server_facts_playbook.yml
└── security/
    └── cert_distribute.yml
```

**Benefits:**
- Clear functional separation
- Site-aware organization
- Better alignment with multi-site architecture
- Simplified disaster recovery workflows

---

## Deployment Workflow

### Standard Multi-Site Deployment Sequence

```
Phase 1: Primary Site Deployment
├─> 1. playbooks/server/storage_prepare_playbook.yml (primary)
├─> 2. playbooks/server/sp_server_install_playbook.yml (primary)
├─> 3. playbooks/server/sp_server_configure_playbook.yml (primary, site_role=primary)
└─> 4. playbooks/client/ba_client_install/playbooks/*/ba_client_install_playbook.yml (primary)

Phase 2: Secondary Site Deployment
├─> 5. playbooks/server/storage_prepare_playbook.yml (secondary)
├─> 6. playbooks/server/sp_server_install_playbook.yml (secondary)
├─> 7. playbooks/server/sp_server_configure_playbook.yml (secondary, site_role=secondary)
└─> 8. playbooks/client/ba_client_install/playbooks/*/ba_client_install_playbook.yml (secondary)

Phase 3: Replication Configuration
└─> 9. playbooks/server/sp_server_configure_playbook.yml (configure_replication=true)

Phase 4: Monitoring Setup
├─> 10. playbooks/monitoring/oc_configure_playbook.yml
└─> 11. playbooks/security/cert_distribute.yml

Phase 5: Validation
└─> 12. playbooks/monitoring/sp_server_facts_playbook.yml (both sites)
```

---

## Multi-Site Specific Features

### 1. Site-Aware Configuration

Playbooks support site-specific configuration via variables:

```yaml
# group_vars/primary_servers.yml
site_role: "primary"
site_name: "DataCenter1"
replication_enabled: true
replication_target: "sp-secondary"

# group_vars/secondary_servers.yml
site_role: "secondary"
site_name: "DataCenter2"
replication_source: "sp-primary"
```

### 2. Replication Management

**Current Implementation:**
```bash
# Configure replication via server configuration
ansible-playbook -i inventory/primary_site.ini \
  playbooks/server/sp_server_configure_playbook.yml \
  -e "configure_replication=true" \
  -e "target_server=sp-secondary"
```

**Future Enhancement:**
Dedicated replication playbooks in `playbooks/replication/` directory.

### 3. Operations Center Integration

The Operations Center provides centralized monitoring:

```bash
# Deploy OC to monitor both sites
ansible-playbook -i inventory/primary_site.ini \
  playbooks/monitoring/oc_configure_playbook.yml \
  -e "monitor_servers=sp-primary,sp-secondary"
```

### 4. Cross-Site Security

Certificate distribution across sites:

```bash
# Distribute certificates to both sites
ansible-playbook -i inventory/primary_site.ini,inventory/secondary_site.ini \
  playbooks/security/cert_distribute.yml
```

---

## Inventory Structure

### Primary Site Inventory

```ini
# inventory/primary_site.ini
[sp_servers_primary]
sp-primary ansible_host=10.1.1.10

[ba_clients_primary_linux]
client-p-linux-01 ansible_host=10.1.1.20

[ba_clients_primary_windows]
client-p-win-01 ansible_host=10.1.1.30

[ba_clients_primary_aix]
client-p-aix-01 ansible_host=10.1.1.40
```

### Secondary Site Inventory

```ini
# inventory/secondary_site.ini
[sp_servers_secondary]
sp-secondary ansible_host=10.2.1.10

[ba_clients_secondary_linux]
client-s-linux-01 ansible_host=10.2.1.20

[ba_clients_secondary_windows]
client-s-win-01 ansible_host=10.2.1.30

[ba_clients_secondary_aix]
client-s-aix-01 ansible_host=10.2.1.40
```

---

## Validation Checklist

- [x] Playbooks organized by function (server, client, replication, monitoring, security)
- [x] DB2-specific playbooks removed
- [x] Blueprint playbook removed
- [x] Multi-platform client support maintained
- [x] Operations Center integration included
- [x] Certificate management included
- [x] All roles and plugins vendored
- [x] No external dependencies (except ansible.builtin)
- [x] Documentation updated
- [x] Aligned with IBM multi-site disk solution architecture

---

## Playbook Count Summary

| Category | Count | Description |
|----------|-------|-------------|
| **Server** | 4 | Install, configure, upgrade, storage |
| **Client** | 10 | 3 platforms × (install, uninstall, facts) + 1 generic facts |
| **Replication** | 0 | Placeholder for future development |
| **Monitoring** | 2 | Operations Center, server facts |
| **Security** | 1 | Certificate distribution |
| **Total** | 17 | Core playbooks for multi-site disk solution |

**Removed:** 5 playbooks (4 DB2-specific + 1 blueprint)

---

## Disaster Recovery Considerations

### Failover Scenarios

1. **Primary Site Failure**
   - Activate secondary server
   - Redirect clients to secondary
   - Monitor replication lag

2. **Secondary Site Failure**
   - Continue operations on primary
   - Alert on replication failure
   - Plan secondary site recovery

3. **Network Failure**
   - Both sites operate independently
   - Replication resumes when connectivity restored
   - Monitor for data consistency

### Recovery Procedures

All DR procedures are documented in the main [`README.md`](README.md) under "Disaster Recovery Procedures" section.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-19 | Initial structure with all playbooks |
| 2.0.0 | 2026-05-25 | Restructured based on IBM documentation, removed DB2 and blueprint playbooks |

---

## References

- IBM Storage Protect 8.2.1 Documentation: https://www.ibm.com/docs/en/storage-protect/8.2.1
- Multi-Site Disk Solution: https://www.ibm.com/docs/en/storage-protect/8.2.1?topic=deployment-multisite-disk-solution
- Solution README: [`README.md`](README.md)
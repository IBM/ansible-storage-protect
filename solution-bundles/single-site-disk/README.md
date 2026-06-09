# Single-Site Disk Solution

## Overview

**Solution Category:** Single-site disk solution  
**Reference:** [IBM Storage Protect 8.2.1 - Single-Site Disk Solution](https://www.ibm.com/docs/en/storage-protect/8.2.1?topic=deployment-single-site-disk-solution)

This solution provides automated deployment and management of IBM Storage Protect in a single-site configuration using disk storage. It is designed for organizations that need reliable data protection within a single data center without geographic replication requirements.

**Status:** ✅ Production Ready

---

## Solution Characteristics

- **Deployment Topology:** Single data center, standalone server
- **Storage Medium:** Disk-based storage pools
- **Scale:** Small to medium enterprises (up to 100TB, 500 clients)
- **High Availability:** Optional (not included in base solution)
- **Disaster Recovery:** Local backup only (no geo-replication)

---

## Use Cases

1. **Small to Medium Business Backup**
   - Centralized backup for file servers, workstations, and applications
   - Single data center operations
   - Cost-effective disk-based protection

2. **Departmental Data Protection**
   - Department-level backup infrastructure
   - Isolated from enterprise-wide systems
   - Local control and management

3. **Development/Test Environments**
   - Non-production workload protection
   - Rapid deployment and teardown
   - Lower cost and complexity

4. **Branch Office Backup**
   - Remote office data protection
   - Standalone operation
   - Minimal infrastructure requirements

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│           Single-Site Data Center               │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │     IBM Storage Protect Server           │  │
│  │     - Server Instance                    │  │
│  │     - Database (DB2)                     │  │
│  │     - Storage Pools (Disk)               │  │
│  └──────────────┬───────────────────────────┘  │
│                 │                               │
│                 │ TCP/IP Network                │
│                 │                               │
│  ┌──────────────┴───────────────────────────┐  │
│  │     Backup-Archive Clients               │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  │  │
│  │  │ Linux   │  │ Windows │  │  AIX    │  │  │
│  │  │ Clients │  │ Clients │  │ Clients │  │  │
│  │  └─────────┘  └─────────┘  └─────────┘  │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │     Disk Storage Infrastructure          │  │
│  │     - Primary Storage Pool               │  │
│  │     - Copy Storage Pool (optional)       │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## Folder Structure

```
single-site-disk/
├── README.md                          # This file
├── requirements.yml                   # Ansible dependencies
├── inventory/
│   └── production.ini                 # Inventory file
├── group_vars/
│   ├── sp_servers.yml                 # Server variables
│   └── ba_clients.yml                 # Client variables
├── playbooks/
│   ├── server/                        # Server lifecycle playbooks
│   │   ├── sp_server_install_playbook.yml
│   │   ├── sp_server_configure_playbook.yml
│   │   ├── sp_server_upgrade_playbook.yml
│   │   └── sp_server_uninstall_playbook.yml
│   ├── client/                        # Client lifecycle playbooks
│   │   ├── ba_client_facts_playbook.yml
│   │   └── ba_client_install/
│   │       └── playbooks/
│   │           ├── linux/
│   │           ├── windows/
│   │           └── aix/
│   ├── storage/                       # Storage management playbooks
│   │   ├── storage_prepare_playbook.yml
│   │   └── storage_cleanup_playbook.yml
│   └── operations/                    # Operational playbooks
│       └── sp_server_facts_playbook.yml
├── roles/                             # Vendored Ansible roles
└── plugins/                           # Vendored Ansible modules
```

---

## Quick Start

### Prerequisites

- Ansible >= 2.15.0
- Python >= 3.9
- Target systems: RHEL/CentOS 7+, Windows Server 2016+, AIX 7.2+
- IBM Storage Protect installation media in local repository

### 1. Configure Inventory

Edit [`inventory/production.ini`](inventory/production.ini):

```ini
[sp_servers]
sp-server-01 ansible_host=192.168.1.10

[ba_clients_linux]
client-linux-01 ansible_host=192.168.1.20
client-linux-02 ansible_host=192.168.1.21

[ba_clients_windows]
client-win-01 ansible_host=192.168.1.30

[ba_clients_aix]
client-aix-01 ansible_host=192.168.1.40
```

### 2. Configure Variables

Edit [`group_vars/sp_servers.yml`](group_vars/sp_servers.yml):

```yaml
sp_server_instance_name: "TSMSERVER1"
sp_server_admin_user: "admin"
sp_server_admin_password: "{{ vault_sp_admin_password }}"
sp_server_port: 1500

# Storage configuration
storage_pool_name: "DISKPOOL"
storage_pool_path: "/data/tsmpool"
storage_pool_size: "10TB"
```

### 3. Deploy Solution

```bash
# Step 1: Prepare storage infrastructure
ansible-playbook -i inventory/production.ini \
  playbooks/storage/storage_prepare_playbook.yml

# Step 2: Install SP Server
ansible-playbook -i inventory/production.ini \
  playbooks/server/sp_server_install_playbook.yml

# Step 3: Configure SP Server
ansible-playbook -i inventory/production.ini \
  playbooks/server/sp_server_configure_playbook.yml

# Step 4: Deploy Linux clients
ansible-playbook -i inventory/production.ini \
  playbooks/client/ba_client_install/playbooks/linux/ba_client_install_playbook.yml

# Step 5: Deploy Windows clients
ansible-playbook -i inventory/production.ini \
  playbooks/client/ba_client_install/playbooks/windows/ba_client_install_playbook.yml

# Step 6: Verify deployment
ansible-playbook -i inventory/production.ini \
  playbooks/operations/sp_server_facts_playbook.yml
```

---

## Playbook Reference

### Server Lifecycle

| Playbook | Purpose | Usage |
|----------|---------|-------|
| [`server/sp_server_install_playbook.yml`](playbooks/server/sp_server_install_playbook.yml) | Install SP Server | Initial deployment |
| [`server/sp_server_configure_playbook.yml`](playbooks/server/sp_server_configure_playbook.yml) | Configure SP Server | Post-installation setup |
| [`server/sp_server_upgrade_playbook.yml`](playbooks/server/sp_server_upgrade_playbook.yml) | Upgrade SP Server | Version upgrades |
| [`server/sp_server_uninstall_playbook.yml`](playbooks/server/sp_server_uninstall_playbook.yml) | Uninstall SP Server | Decommissioning |

### Client Lifecycle

| Playbook | Purpose | Platform |
|----------|---------|----------|
| [`client/ba_client_install/playbooks/linux/ba_client_install_playbook.yml`](playbooks/client/ba_client_install/playbooks/linux/ba_client_install_playbook.yml) | Install BA client | Linux |
| [`client/ba_client_install/playbooks/windows/ba_client_install_playbook.yml`](playbooks/client/ba_client_install/playbooks/windows/ba_client_install_playbook.yml) | Install BA client | Windows |
| [`client/ba_client_install/playbooks/aix/ba_client_install_playbook.yml`](playbooks/client/ba_client_install/playbooks/aix/ba_client_install_playbook.yml) | Install BA client | AIX |
| [`client/ba_client_facts_playbook.yml`](playbooks/client/ba_client_facts_playbook.yml) | Collect client info | All platforms |

### Storage Management

| Playbook | Purpose | Usage |
|----------|---------|-------|
| [`storage/storage_prepare_playbook.yml`](playbooks/storage/storage_prepare_playbook.yml) | Prepare disk storage | Pre-deployment |
| [`storage/storage_cleanup_playbook.yml`](playbooks/storage/storage_cleanup_playbook.yml) | Cleanup storage | Decommissioning |

### Operations

| Playbook | Purpose | Usage |
|----------|---------|-------|
| [`operations/sp_server_facts_playbook.yml`](playbooks/operations/sp_server_facts_playbook.yml) | Collect server state | Monitoring, validation |

---

## Configuration Examples

### Small Environment (< 10TB, < 50 clients)

```yaml
# group_vars/sp_servers.yml
sp_server_size: "small"
storage_pool_size: "5TB"
max_concurrent_sessions: 50
buffer_pool_size: "2GB"
```

### Medium Environment (10-50TB, 50-200 clients)

```yaml
# group_vars/sp_servers.yml
sp_server_size: "medium"
storage_pool_size: "25TB"
max_concurrent_sessions: 150
buffer_pool_size: "8GB"
```

### Large Environment (50-100TB, 200-500 clients)

```yaml
# group_vars/sp_servers.yml
sp_server_size: "large"
storage_pool_size: "75TB"
max_concurrent_sessions: 300
buffer_pool_size: "16GB"
```

---

## Operational Tasks

### Daily Operations

```bash
# Check server status
ansible-playbook -i inventory/production.ini \
  playbooks/operations/sp_server_facts_playbook.yml

# Check client status
ansible-playbook -i inventory/production.ini \
  playbooks/client/ba_client_facts_playbook.yml
```

### Maintenance

```bash
# Upgrade server
ansible-playbook -i inventory/production.ini \
  playbooks/server/sp_server_upgrade_playbook.yml \
  -e "sp_server_version=8.2.1"

# Reconfigure server
ansible-playbook -i inventory/production.ini \
  playbooks/server/sp_server_configure_playbook.yml
```

### Troubleshooting

```bash
# Collect detailed facts
ansible-playbook -i inventory/production.ini \
  playbooks/operations/sp_server_facts_playbook.yml \
  -e "verbose=true"

# Check specific client
ansible-playbook -i inventory/production.ini \
  playbooks/client/ba_client_facts_playbook.yml \
  --limit client-linux-01
```

---

## Best Practices

### Storage Configuration

1. **Separate Storage Pools**
   - Primary pool for active backups
   - Copy pool for redundancy (optional)
   - Archive pool for long-term retention

2. **Disk Space Planning**
   - Plan for 1.5x data growth
   - Monitor pool utilization (alert at 80%)
   - Implement reclamation policies

3. **Performance Optimization**
   - Use dedicated disk arrays
   - Enable compression for space savings
   - Configure appropriate buffer sizes

### Security

1. **Access Control**
   - Use strong passwords (stored in Ansible Vault)
   - Implement role-based access
   - Enable SSL/TLS for client-server communication

2. **Network Security**
   - Firewall rules (port 1500 for SP Server)
   - Network segmentation
   - VPN for remote clients

### Backup Policies

1. **Retention**
   - Daily backups: 7 days
   - Weekly backups: 4 weeks
   - Monthly backups: 12 months

2. **Scheduling**
   - Stagger client backups
   - Avoid peak business hours
   - Monitor backup windows

---

## Limitations

This single-site solution has the following limitations:

1. **No Geographic Redundancy**
   - All data resides in single location
   - Vulnerable to site-wide disasters
   - Consider multi-site solution for DR

2. **No High Availability**
   - Single server instance
   - Downtime during maintenance
   - Consider HA configuration for critical workloads

3. **Scale Limits**
   - Recommended maximum: 100TB, 500 clients
   - For larger scale, use peta-scale solution
   - Performance degrades beyond recommended limits

4. **No Cloud Integration**
   - Disk-only storage
   - No cloud tiering
   - Consider cloud solution for hybrid needs

---

## Migration Path

### To Multi-Site Solution

If you need disaster recovery:
1. Deploy second site using multi-site solution
2. Configure replication between sites
3. Implement failover procedures

### To Peta-Scale Solution

If you exceed scale limits:
1. Plan for larger infrastructure
2. Deploy peta-scale solution
3. Migrate data using export/import

---

## Independence Validation

✅ **Self-Contained:** All playbooks, roles, and plugins included  
✅ **No External Dependencies:** Only requires `ansible.builtin`  
✅ **No Cross-Solution References:** Fully independent  
✅ **Offline Capable:** Works without internet access  

---

## Support and Documentation

- **IBM Documentation:** https://www.ibm.com/docs/en/storage-protect/8.2.1
- **Solution Guide:** `../../docs/guides/sp-server-lifecycle-guide.md`
- **Playbook Analysis:** `../../docs/playbook-solution-mapping.md`

---

## Version Information

- **Solution Version:** 2.0.0
- **IBM Storage Protect Version:** 8.2.1
- **Ansible Collection:** ibm.storage_protect v1.0.0
- **Last Updated:** 2026-05-20

---

## License

This solution is part of the IBM Storage Protect Ansible Collection.  
See the main collection LICENSE file for details.
# Tape Archival Solution

## Overview

**Solution Category:** Tape solution  
**Reference:** [IBM Storage Protect 8.2.1 - Tape Solution](https://www.ibm.com/docs/en/storage-protect/8.2.1?topic=deployment-tape-solution)

This solution provides automated deployment and management of IBM Storage Protect with tape library integration for long-term archival and compliance requirements. It is designed for organizations requiring cost-effective, long-term data retention on tape media.

**Status:** ✅ Production Ready

---

## Solution Characteristics

- **Deployment Topology:** Single or multi-site with tape library
- **Storage Medium:** Tape cartridges (LTO, TS series)
- **Scale:** Medium to large enterprises with archival needs
- **Retention:** Long-term (7+ years typical)
- **Use Case:** Compliance, archival, disaster recovery
- **Cost Profile:** Low cost per TB for long-term storage

---

## Use Cases

1. **Long-Term Data Archival**
   - Regulatory compliance (7-10 year retention)
   - Historical data preservation
   - Legal hold requirements
   - Cold storage for infrequently accessed data

2. **Disaster Recovery**
   - Off-site tape vaulting
   - Air-gapped backup copies
   - Geographic distribution of tape media

3. **Cost Optimization**
   - Lower cost per TB vs disk
   - Reduced power and cooling costs
   - Scalable capacity without infrastructure expansion

4. **Compliance & Governance**
   - WORM (Write Once Read Many) capability
   - Audit trail for data access
   - Encryption for data security
   - Chain of custody tracking

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              IBM Storage Protect Server                 │
│                                                         │
│  ┌──────────────┐         ┌──────────────┐            │
│  │   Database   │         │  Disk Pool   │            │
│  │    (DB2)     │         │  (Primary)   │            │
│  └──────────────┘         └──────────────┘            │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Storage Agent                          │  │
│  │  - Tape library management                       │  │
│  │  - Drive allocation                              │  │
│  │  - Media management                              │  │
│  └──────────────┬───────────────────────────────────┘  │
└─────────────────┼───────────────────────────────────────┘
                  │
                  │ SAN/FC Connection
                  │
┌─────────────────┴───────────────────────────────────────┐
│              Tape Library (Physical)                    │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  Drive 1 │  │  Drive 2 │  │  Drive N │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         Tape Cartridge Slots                    │  │
│  │  [T001] [T002] [T003] ... [T999]               │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         Robotic Arm (Picker)                    │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                  │
                  │ Network
                  │
┌─────────────────┴───────────────────────────────────────┐
│              Backup-Archive Clients                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                │
│  │  Linux  │  │ Windows │  │   AIX   │                │
│  └─────────┘  └─────────┘  └─────────┘                │
└─────────────────────────────────────────────────────────┘
```

---

## Folder Structure

```
tape-archival/
├── README.md                          # This file
├── STRUCTURE.md                       # Detailed structure documentation
├── requirements.yml                   # Ansible dependencies
├── inventory/
│   └── production.ini                 # Inventory file
├── group_vars/
│   ├── sp_servers.yml                 # Server configuration
│   ├── storage_agents.yml             # Storage agent configuration
│   └── tape_libraries.yml             # Tape library configuration
├── playbooks/
│   ├── server/                        # Server lifecycle
│   │   ├── sp_server_install_playbook.yml
│   │   └── sp_server_configure_playbook.yml
│   ├── storage-agent/                 # Tape library management
│   │   ├── storage_agent_configure_playbook.yml
│   │   ├── storage_prepare_playbook.yml
│   │   └── storage_cleanup_playbook.yml
│   ├── client/                        # Client lifecycle
│   │   ├── ba_client_facts_playbook.yml
│   │   └── ba_client_install/
│   │       └── playbooks/
│   │           ├── linux/
│   │           ├── windows/
│   │           └── aix/
│   └── operations/                    # Operational tasks
│       └── sp_server_facts_playbook.yml
├── roles/                             # Vendored Ansible roles
└── plugins/                           # Vendored Ansible modules
```

---

## Quick Start

### Prerequisites

- Ansible >= 2.15.0
- Python >= 3.9
- Tape library with SAN/FC connectivity
- IBM Storage Protect installation media
- Tape cartridges (LTO-7, LTO-8, LTO-9, or IBM TS series)

### 1. Configure Inventory

Edit [`inventory/production.ini`](inventory/production.ini):

```ini
[sp_servers]
sp-tape-server ansible_host=192.168.1.10

[storage_agents]
storage-agent-01 ansible_host=192.168.1.11

[tape_libraries]
tape-library-01 ansible_host=192.168.1.20 library_type="IBM TS4500"

[ba_clients_linux]
client-linux-01 ansible_host=192.168.1.30
```

### 2. Configure Variables

**Server Configuration** ([`group_vars/sp_servers.yml`](group_vars/sp_servers.yml)):
```yaml
sp_server_instance_name: "TAPESERVER"
sp_server_admin_user: "admin"
sp_server_admin_password: "{{ vault_sp_admin_password }}"

# Tape-specific configuration
tape_enabled: true
tape_pool_name: "TAPEPOOL"
tape_reclamation_threshold: 60
```

**Storage Agent Configuration** ([`group_vars/storage_agents.yml`](group_vars/storage_agents.yml)):
```yaml
storage_agent_name: "TAPEAGENT"
tape_library_name: "TAPELIB01"
tape_library_type: "IBM TS4500"
tape_drive_count: 8
san_connection_type: "FC"
```

**Tape Library Configuration** ([`group_vars/tape_libraries.yml`](group_vars/tape_libraries.yml)):
```yaml
library_name: "TAPELIB01"
library_type: "IBM TS4500"
library_serial: "12345678"
drive_type: "LTO8"
slot_count: 500
cleaning_cartridges: 5
```

### 3. Deploy Solution

```bash
# Step 1: Install SP Server
ansible-playbook -i inventory/production.ini \
  playbooks/server/sp_server_install_playbook.yml

# Step 2: Configure SP Server for tape
ansible-playbook -i inventory/production.ini \
  playbooks/server/sp_server_configure_playbook.yml \
  -e "storage_type=tape"

# Step 3: Prepare tape infrastructure
ansible-playbook -i inventory/production.ini \
  playbooks/storage-agent/storage_prepare_playbook.yml \
  -e "storage_type=tape"

# Step 4: Configure storage agent
ansible-playbook -i inventory/production.ini \
  playbooks/storage-agent/storage_agent_configure_playbook.yml

# Step 5: Deploy clients
ansible-playbook -i inventory/production.ini \
  playbooks/client/ba_client_install/playbooks/linux/ba_client_install_playbook.yml

# Step 6: Verify deployment
ansible-playbook -i inventory/production.ini \
  playbooks/operations/sp_server_facts_playbook.yml
```

---

## Playbook Reference

### Server Lifecycle (`playbooks/server/`)

| Playbook | Purpose | Usage |
|----------|---------|-------|
| [`sp_server_install_playbook.yml`](playbooks/server/sp_server_install_playbook.yml) | Install SP Server | Initial deployment |
| [`sp_server_configure_playbook.yml`](playbooks/server/sp_server_configure_playbook.yml) | Configure SP Server for tape | Post-installation setup |

### Storage Agent & Tape Library (`playbooks/storage-agent/`)

| Playbook | Purpose | Usage |
|----------|---------|-------|
| [`storage_agent_configure_playbook.yml`](playbooks/storage-agent/storage_agent_configure_playbook.yml) | Configure storage agent | Tape library integration |
| [`storage_prepare_playbook.yml`](playbooks/storage-agent/storage_prepare_playbook.yml) | Prepare tape devices | Pre-deployment |
| [`storage_cleanup_playbook.yml`](playbooks/storage-agent/storage_cleanup_playbook.yml) | Cleanup tape resources | Decommissioning |

### Client Lifecycle (`playbooks/client/`)

| Playbook | Purpose | Platform |
|----------|---------|----------|
| [`client/ba_client_install/playbooks/linux/ba_client_install_playbook.yml`](playbooks/client/ba_client_install/playbooks/linux/ba_client_install_playbook.yml) | Install BA client | Linux |
| [`client/ba_client_install/playbooks/windows/ba_client_install_playbook.yml`](playbooks/client/ba_client_install/playbooks/windows/ba_client_install_playbook.yml) | Install BA client | Windows |
| [`client/ba_client_install/playbooks/aix/ba_client_install_playbook.yml`](playbooks/client/ba_client_install/playbooks/aix/ba_client_install_playbook.yml) | Install BA client | AIX |
| [`client/ba_client_facts_playbook.yml`](playbooks/client/ba_client_facts_playbook.yml) | Collect client info | All platforms |

### Operations (`playbooks/operations/`)

| Playbook | Purpose | Usage |
|----------|---------|-------|
| [`sp_server_facts_playbook.yml`](playbooks/operations/sp_server_facts_playbook.yml) | Collect server state | Monitoring, validation |

---

## Tape Library Configuration

### Supported Tape Libraries

- **IBM TS Series:** TS4500, TS4300, TS3500, TS3310
- **LTO Drives:** LTO-7, LTO-8, LTO-9
- **Other:** HP MSL, Dell ML3, Quantum Scalar

### Library Definition

```bash
# Define tape library via dsmadmc
dsmadmc -id=admin -password=xxx \
  "DEFINE LIBRARY TAPELIB01 LIBTYPE=SCSI"

# Define tape drives
dsmadmc -id=admin -password=xxx \
  "DEFINE DRIVE TAPELIB01 DRIVE01"

# Define tape device class
dsmadmc -id=admin -password=xxx \
  "DEFINE DEVCLASS TAPECLASS DEVTYPE=LTO LIBRARY=TAPELIB01"

# Define tape storage pool
dsmadmc -id=admin -password=xxx \
  "DEFINE STGPOOL TAPEPOOL TAPECLASS"
```

### Automated Configuration

The storage agent playbook automates library configuration:

```yaml
# group_vars/storage_agents.yml
tape_library_config:
  library_name: "TAPELIB01"
  library_type: "SCSI"
  drives:
    - name: "DRIVE01"
      device: "/dev/smc0"
    - name: "DRIVE02"
      device: "/dev/smc1"
  device_class: "TAPECLASS"
  storage_pool: "TAPEPOOL"
```

---

## Tape Management Operations

### Media Management

```bash
# Check tape inventory
dsmadmc -id=admin "QUERY LIBVOLUME TAPELIB01"

# Check tape drives
dsmadmc -id=admin "QUERY DRIVE TAPELIB01"

# Check tape mounts
dsmadmc -id=admin "QUERY MOUNT"

# Audit library
dsmadmc -id=admin "AUDIT LIBRARY TAPELIB01"
```

### Tape Reclamation

```bash
# Check reclamation candidates
dsmadmc -id=admin "QUERY VOLUME * STGPOOL=TAPEPOOL"

# Run reclamation
dsmadmc -id=admin "RECLAIM STGPOOL TAPEPOOL THRESHOLD=60"
```

### Tape Checkout/Checkin

```bash
# Checkout tape for off-site storage
dsmadmc -id=admin "CHECKOUT LIBVOLUME TAPELIB01 T00001 CHECKLABEL=YES"

# Checkin tape from off-site
dsmadmc -id=admin "CHECKIN LIBVOLUME TAPELIB01 SEARCH=YES"
```

---

## Hierarchical Storage Management (HSM)

### Migration Policy

Configure automatic migration from disk to tape:

```yaml
# group_vars/sp_servers.yml
hsm_enabled: true
hsm_migration_days: 90  # Migrate data older than 90 days
hsm_source_pool: "DISKPOOL"
hsm_target_pool: "TAPEPOOL"
```

### Manual Configuration

```bash
# Define migration policy
dsmadmc -id=admin \
  "DEFINE COPYSTGPOOL TAPEPOOL DISKPOOL"

# Set migration threshold
dsmadmc -id=admin \
  "UPDATE STGPOOL DISKPOOL HIGHMIG=90 LOWMIG=70"
```

---

## Best Practices

### Tape Library Management

1. **Regular Audits**
   - Weekly library audits
   - Monthly inventory verification
   - Quarterly cleaning cartridge replacement

2. **Drive Maintenance**
   - Monitor drive usage hours
   - Replace drives at manufacturer recommendations
   - Keep cleaning cartridges available

3. **Media Rotation**
   - Implement tape rotation schedule
   - Off-site vaulting for DR
   - Track tape age and usage

### Performance Optimization

1. **Drive Allocation**
   - Dedicate drives for specific workloads
   - Balance load across drives
   - Monitor drive utilization

2. **Reclamation**
   - Schedule during off-peak hours
   - Set appropriate threshold (60-70%)
   - Monitor reclamation progress

3. **Network Configuration**
   - Use dedicated SAN fabric
   - Optimize FC zoning
   - Monitor SAN performance

### Data Protection

1. **Encryption**
   - Enable tape encryption
   - Key management strategy
   - Compliance requirements

2. **WORM Capability**
   - Use WORM tapes for compliance
   - Implement retention policies
   - Audit trail maintenance

3. **Off-Site Storage**
   - Regular tape checkout
   - Secure transportation
   - Environmental controls

---

## Monitoring & Alerting

### Key Metrics

- **Tape Library Status:** Online/offline, errors
- **Drive Utilization:** Active mounts, idle time
- **Tape Capacity:** Used/available slots
- **Reclamation Status:** Pending volumes
- **Mount Wait Time:** Queue depth

### Alert Thresholds

```yaml
# Recommended alert thresholds
library_offline_alert: "immediate"
drive_error_threshold: "3 errors/day"
tape_capacity_warning: "90%"
tape_capacity_critical: "95%"
mount_wait_warning: "5 minutes"
reclamation_backlog_warning: "100 volumes"
```

### Monitoring Commands

```bash
# Check library status
ansible-playbook -i inventory/production.ini \
  playbooks/operations/sp_server_facts_playbook.yml \
  -e "check_tape_library=true"

# Monitor tape operations
dsmadmc -id=admin "QUERY ACTLOG SEARCH=TAPE"
```

---

## Troubleshooting

### Common Issues

**1. Library Not Responding**
```bash
# Check library connection
dsmadmc -id=admin "QUERY LIBRARY TAPELIB01"

# Restart library manager
dsmadmc -id=admin "DISABLE LIBRARY TAPELIB01"
dsmadmc -id=admin "ENABLE LIBRARY TAPELIB01"
```

**2. Drive Errors**
```bash
# Check drive status
dsmadmc -id=admin "QUERY DRIVE TAPELIB01 F=D"

# Clean drive
dsmadmc -id=admin "CLEAN DRIVE TAPELIB01 DRIVE01"
```

**3. Mount Failures**
```bash
# Check mount queue
dsmadmc -id=admin "QUERY MOUNT"

# Cancel stuck mount
dsmadmc -id=admin "CANCEL MOUNT <request_number>"
```

**4. Reclamation Issues**
```bash
# Check reclamation status
dsmadmc -id=admin "QUERY PROCESS"

# Cancel reclamation
dsmadmc -id=admin "CANCEL PROCESS <process_number>"
```

---

## Tape Media Specifications

### LTO Specifications

| Generation | Native Capacity | Compressed Capacity | Transfer Rate |
|------------|----------------|---------------------|---------------|
| LTO-7 | 6 TB | 15 TB | 300 MB/s |
| LTO-8 | 12 TB | 30 TB | 360 MB/s |
| LTO-9 | 18 TB | 45 TB | 400 MB/s |

### IBM TS Series

| Model | Capacity | Drives | Slots |
|-------|----------|--------|-------|
| TS4500 | Up to 11 PB | Up to 256 | Up to 11,000 |
| TS4300 | Up to 2.8 PB | Up to 24 | Up to 280 |
| TS3500 | Up to 5.6 PB | Up to 128 | Up to 5,600 |

---

## Compliance & Retention

### Retention Policies

```yaml
# group_vars/sp_servers.yml
retention_policies:
  - name: "COMPLIANCE_7YEAR"
    retention_days: 2555  # 7 years
    media_type: "WORM"
  - name: "ARCHIVE_10YEAR"
    retention_days: 3650  # 10 years
    media_type: "WORM"
  - name: "STANDARD_1YEAR"
    retention_days: 365
    media_type: "REWRITABLE"
```

### Audit Requirements

- Tape checkout/checkin logs
- Data access audit trail
- Retention policy compliance
- Chain of custody documentation

---

## Cost Considerations

### Capital Costs

- Tape library hardware
- Tape drives
- SAN infrastructure
- Initial tape cartridge purchase

### Operational Costs

- Tape cartridge replenishment
- Drive maintenance/replacement
- Off-site storage fees
- Power and cooling (minimal)

### Cost Benefits

- Lower $/TB vs disk (10-20x cheaper)
- No power cost when not in use
- Long media lifespan (15-30 years)
- Scalable without infrastructure changes

---

## Independence Validation

✅ **Self-Contained:** All playbooks, roles, and plugins included  
✅ **No External Dependencies:** Only requires `ansible.builtin`  
✅ **No Cross-Solution References:** Fully independent  
✅ **Offline Capable:** Works without internet access  

---

## Support and Documentation

- **IBM Documentation:** https://www.ibm.com/docs/en/storage-protect/8.2.1
- **Tape Solution Guide:** https://www.ibm.com/docs/en/storage-protect/8.2.1?topic=deployment-tape-solution
- **Playbook Analysis:** `../../docs/playbook-solution-mapping.md`

---

## Version Information

- **Solution Version:** 2.0.0
- **IBM Storage Protect Version:** 8.2.1
- **Ansible Collection:** ibm.storage_protect v1.0.0
- **Last Updated:** 2026-05-25

---

## License

This solution is part of the IBM Storage Protect Ansible Collection.  
See the main collection LICENSE file for details.
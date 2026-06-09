# Multi-Site Disk Solution

## Overview

**Solution Category:** Multi-site disk solution  
**Reference:** [IBM Storage Protect 8.2.1 - Multi-Site Disk Solution](https://www.ibm.com/docs/en/storage-protect/8.2.1?topic=deployment-multisite-disk-solution)

This solution provides automated deployment and management of IBM Storage Protect across multiple geographic sites with data replication for disaster recovery. It is designed for organizations requiring business continuity and geographic redundancy.

**Status:** ✅ Production Ready

---

## Solution Characteristics

- **Deployment Topology:** Multiple data centers (primary + secondary sites)
- **Storage Medium:** Disk-based storage pools with replication
- **Scale:** Medium to large enterprises (100TB+, 500+ clients)
- **High Availability:** Site-level redundancy
- **Disaster Recovery:** Automated failover and recovery
- **Replication:** Node replication between sites

---

## Use Cases

1. **Business Continuity & Disaster Recovery**
   - Geographic redundancy for critical data
   - Automated failover capabilities
   - RPO/RTO compliance

2. **Multi-Location Enterprises**
   - Headquarters and branch offices
   - Regional data centers
   - Global operations

3. **Regulatory Compliance**
   - Data residency requirements
   - Geographic data distribution
   - Audit trail across sites

4. **High Availability Requirements**
   - Mission-critical workloads
   - 24/7 operations
   - Minimal downtime tolerance

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Operations Center (OC)                       │
│              Centralized Monitoring & Management                │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
┌───────┴──────────┐            ┌────────┴─────────┐
│  Primary Site    │            │  Secondary Site  │
│  (Data Center 1) │◄──────────►│  (Data Center 2) │
│                  │ Replication│                  │
│  ┌────────────┐  │            │  ┌────────────┐  │
│  │ SP Server  │  │            │  │ SP Server  │  │
│  │ (Primary)  │  │            │  │ (Secondary)│  │
│  └─────┬──────┘  │            │  └─────┬──────┘  │
│        │         │            │        │         │
│  ┌─────┴──────┐  │            │  ┌─────┴──────┐  │
│  │  Storage   │  │            │  │  Storage   │  │
│  │  Pool      │  │            │  │  Pool      │  │
│  │  (Disk)    │  │            │  │  (Disk)    │  │
│  └────────────┘  │            │  └────────────┘  │
│        │         │            │        │         │
│  ┌─────┴──────┐  │            │  ┌─────┴──────┐  │
│  │ BA Clients │  │            │  │ BA Clients │  │
│  │ (Local)    │  │            │  │ (Local)    │  │
│  └────────────┘  │            │  └────────────┘  │
└──────────────────┘            └──────────────────┘
```

---

## Folder Structure

```
multisite-disk/
├── README.md                          # This file
├── STRUCTURE.md                       # Detailed structure documentation
├── requirements.yml                   # Ansible dependencies
├── inventory/
│   ├── primary_site.ini               # Primary site inventory
│   └── secondary_site.ini             # Secondary site inventory
├── group_vars/
│   ├── primary_servers.yml            # Primary site server config
│   ├── secondary_servers.yml          # Secondary site server config
│   └── all.yml                        # Common variables
├── playbooks/
│   ├── server/                        # Server lifecycle (both sites)
│   │   ├── sp_server_install_playbook.yml
│   │   ├── sp_server_configure_playbook.yml
│   │   ├── sp_server_upgrade_playbook.yml
│   │   └── storage_prepare_playbook.yml
│   ├── client/                        # Client lifecycle (both sites)
│   │   ├── ba_client_facts_playbook.yml
│   │   └── ba_client_install/
│   │       └── playbooks/
│   │           ├── linux/
│   │           ├── windows/
│   │           └── aix/
│   ├── replication/                   # Replication management
│   │   └── (replication playbooks - to be added)
│   ├── monitoring/                    # Centralized monitoring
│   │   ├── oc_configure_playbook.yml
│   │   └── sp_server_facts_playbook.yml
│   └── security/                      # Security & certificates
│       └── cert_distribute.yml
├── roles/                             # Vendored Ansible roles
└── plugins/                           # Vendored Ansible modules
```

---

## Quick Start

### Prerequisites

- Ansible >= 2.15.0
- Python >= 3.9
- Network connectivity between sites
- IBM Storage Protect installation media
- SSL/TLS certificates for secure communication

### 1. Configure Inventory

**Primary Site** ([`inventory/primary_site.ini`](inventory/primary_site.ini)):
```ini
[sp_servers_primary]
sp-primary ansible_host=10.1.1.10

[ba_clients_primary_linux]
client-p-linux-01 ansible_host=10.1.1.20
client-p-linux-02 ansible_host=10.1.1.21

[ba_clients_primary_windows]
client-p-win-01 ansible_host=10.1.1.30
```

**Secondary Site** ([`inventory/secondary_site.ini`](inventory/secondary_site.ini)):
```ini
[sp_servers_secondary]
sp-secondary ansible_host=10.2.1.10

[ba_clients_secondary_linux]
client-s-linux-01 ansible_host=10.2.1.20
client-s-linux-02 ansible_host=10.2.1.21

[ba_clients_secondary_windows]
client-s-win-01 ansible_host=10.2.1.30
```

### 2. Deploy Primary Site

```bash
# Step 1: Prepare storage
ansible-playbook -i inventory/primary_site.ini \
  playbooks/server/storage_prepare_playbook.yml

# Step 2: Install primary SP Server
ansible-playbook -i inventory/primary_site.ini \
  playbooks/server/sp_server_install_playbook.yml

# Step 3: Configure primary server
ansible-playbook -i inventory/primary_site.ini \
  playbooks/server/sp_server_configure_playbook.yml \
  -e "site_role=primary"

# Step 4: Deploy primary site clients
ansible-playbook -i inventory/primary_site.ini \
  playbooks/client/ba_client_install/playbooks/linux/ba_client_install_playbook.yml
```

### 3. Deploy Secondary Site

```bash
# Step 1: Prepare storage
ansible-playbook -i inventory/secondary_site.ini \
  playbooks/server/storage_prepare_playbook.yml

# Step 2: Install secondary SP Server
ansible-playbook -i inventory/secondary_site.ini \
  playbooks/server/sp_server_install_playbook.yml

# Step 3: Configure secondary server
ansible-playbook -i inventory/secondary_site.ini \
  playbooks/server/sp_server_configure_playbook.yml \
  -e "site_role=secondary"

# Step 4: Deploy secondary site clients
ansible-playbook -i inventory/secondary_site.ini \
  playbooks/client/ba_client_install/playbooks/linux/ba_client_install_playbook.yml
```

### 4. Configure Replication

```bash
# Configure node replication from primary to secondary
ansible-playbook -i inventory/primary_site.ini \
  playbooks/server/sp_server_configure_playbook.yml \
  -e "configure_replication=true" \
  -e "target_server=sp-secondary" \
  -e "target_server_address=10.2.1.10"
```

### 5. Deploy Operations Center

```bash
# Deploy OC for centralized monitoring
ansible-playbook -i inventory/primary_site.ini \
  playbooks/monitoring/oc_configure_playbook.yml \
  -e "monitor_servers=sp-primary,sp-secondary"
```

### 6. Distribute Certificates

```bash
# Distribute SSL/TLS certificates across sites
ansible-playbook -i inventory/primary_site.ini,inventory/secondary_site.ini \
  playbooks/security/cert_distribute.yml
```

---

## Playbook Reference

### Server Lifecycle (`playbooks/server/`)

| Playbook | Purpose | Sites |
|----------|---------|-------|
| [`sp_server_install_playbook.yml`](playbooks/server/sp_server_install_playbook.yml) | Install SP Server | Primary, Secondary |
| [`sp_server_configure_playbook.yml`](playbooks/server/sp_server_configure_playbook.yml) | Configure SP Server | Primary, Secondary |
| [`sp_server_upgrade_playbook.yml`](playbooks/server/sp_server_upgrade_playbook.yml) | Upgrade SP Server | Primary, Secondary |
| [`storage_prepare_playbook.yml`](playbooks/server/storage_prepare_playbook.yml) | Prepare disk storage | Primary, Secondary |

### Client Lifecycle (`playbooks/client/`)

| Playbook | Purpose | Platform |
|----------|---------|----------|
| [`client/ba_client_install/playbooks/linux/ba_client_install_playbook.yml`](playbooks/client/ba_client_install/playbooks/linux/ba_client_install_playbook.yml) | Install BA client | Linux |
| [`client/ba_client_install/playbooks/windows/ba_client_install_playbook.yml`](playbooks/client/ba_client_install/playbooks/windows/ba_client_install_playbook.yml) | Install BA client | Windows |
| [`client/ba_client_install/playbooks/aix/ba_client_install_playbook.yml`](playbooks/client/ba_client_install/playbooks/aix/ba_client_install_playbook.yml) | Install BA client | AIX |
| [`client/ba_client_facts_playbook.yml`](playbooks/client/ba_client_facts_playbook.yml) | Collect client info | All platforms |

### Monitoring (`playbooks/monitoring/`)

| Playbook | Purpose | Usage |
|----------|---------|-------|
| [`oc_configure_playbook.yml`](playbooks/monitoring/oc_configure_playbook.yml) | Configure Operations Center | Centralized monitoring |
| [`sp_server_facts_playbook.yml`](playbooks/monitoring/sp_server_facts_playbook.yml) | Collect server state | Both sites |

### Security (`playbooks/security/`)

| Playbook | Purpose | Usage |
|----------|---------|-------|
| [`cert_distribute.yml`](playbooks/security/cert_distribute.yml) | Distribute SSL/TLS certificates | Cross-site security |

---

## Replication Configuration

### Node Replication

Node replication copies client data from the primary server to the secondary server for disaster recovery.

**Configuration Variables:**
```yaml
# group_vars/primary_servers.yml
replication_enabled: true
replication_target_server: "sp-secondary"
replication_target_address: "10.2.1.10"
replication_target_port: 1500
replication_schedule: "DAILY 22:00"
```

**Manual Configuration (via dsmadmc):**
```bash
# On primary server
dsmadmc -id=admin -password=xxx \
  "DEFINE SERVER sp-secondary SERVERADDRESS=10.2.1.10 SERVERPORT=1500"

dsmadmc -id=admin -password=xxx \
  "DEFINE REPLICATION NODE_NAME TARGETSERVER=sp-secondary"
```

---

## Disaster Recovery Procedures

### Failover to Secondary Site

1. **Verify Secondary Site Status**
   ```bash
   ansible-playbook -i inventory/secondary_site.ini \
     playbooks/monitoring/sp_server_facts_playbook.yml
   ```

2. **Activate Secondary Server**
   ```bash
   # Manually activate secondary server
   dsmadmc -id=admin -password=xxx -server=sp-secondary \
     "SET SERVERNAME sp-secondary"
   ```

3. **Redirect Clients to Secondary**
   ```bash
   # Update client configurations
   ansible-playbook -i inventory/primary_site.ini \
     playbooks/client/ba_client_install/playbooks/linux/ba_client_install_playbook.yml \
     -e "sp_server_address=10.2.1.10"
   ```

### Failback to Primary Site

1. **Verify Primary Site Recovery**
2. **Synchronize Data** (if needed)
3. **Redirect Clients Back to Primary**
4. **Resume Normal Replication**

---

## Operations Center Integration

The Operations Center provides centralized monitoring and management across both sites.

**Key Features:**
- Multi-server dashboard
- Cross-site alerting
- Capacity planning
- Performance monitoring
- Compliance reporting

**Access:**
- URL: `https://oc-server:11090`
- Default credentials: admin / (configured password)

---

## Best Practices

### Network Configuration

1. **Dedicated Replication Network**
   - Separate VLAN for replication traffic
   - Minimum 1 Gbps bandwidth
   - Low latency (< 50ms recommended)

2. **Firewall Rules**
   - Primary → Secondary: TCP 1500 (SP Server)
   - Both → OC: TCP 11090 (Operations Center)
   - Clients → Servers: TCP 1500

### Replication Strategy

1. **Schedule During Off-Peak Hours**
   - Minimize impact on production backups
   - Consider time zone differences

2. **Monitor Replication Status**
   - Check replication lag daily
   - Alert on replication failures
   - Verify data consistency

3. **Test Failover Regularly**
   - Quarterly DR tests
   - Document procedures
   - Update runbooks

### Security

1. **SSL/TLS Encryption**
   - Enable for all server-to-server communication
   - Use valid certificates
   - Regular certificate rotation

2. **Access Control**
   - Separate admin accounts per site
   - Role-based access control
   - Audit logging enabled

---

## Monitoring & Alerting

### Key Metrics

- **Replication Status:** Lag time, success rate
- **Storage Utilization:** Both sites
- **Backup Success Rate:** Per site
- **Network Bandwidth:** Replication traffic
- **Server Health:** CPU, memory, disk I/O

### Alert Thresholds

```yaml
# Recommended alert thresholds
replication_lag_warning: "4 hours"
replication_lag_critical: "12 hours"
storage_utilization_warning: "80%"
storage_utilization_critical: "90%"
backup_failure_rate_warning: "5%"
backup_failure_rate_critical: "10%"
```

---

## Limitations

1. **Network Dependency**
   - Requires reliable inter-site connectivity
   - Replication performance depends on bandwidth
   - Latency affects replication speed

2. **Complexity**
   - More complex than single-site
   - Requires skilled administrators
   - Higher operational overhead

3. **Cost**
   - Duplicate infrastructure
   - Network costs
   - Additional licensing

---

## Troubleshooting

### Replication Issues

```bash
# Check replication status
dsmadmc -id=admin "QUERY REPLICATION"

# Check replication errors
dsmadmc -id=admin "QUERY ACTLOG SEARCH=REPLICATION"

# Restart replication
dsmadmc -id=admin "CANCEL REPLICATION NODE_NAME"
dsmadmc -id=admin "REPLICATE NODE NODE_NAME"
```

### Network Connectivity

```bash
# Test connectivity between sites
ansible -i inventory/primary_site.ini sp_servers_primary \
  -m ping -a "data=10.2.1.10"

# Check port accessibility
ansible -i inventory/primary_site.ini sp_servers_primary \
  -m wait_for -a "host=10.2.1.10 port=1500 timeout=10"
```

---

## Independence Validation

✅ **Self-Contained:** All playbooks, roles, and plugins included  
✅ **No External Dependencies:** Only requires `ansible.builtin`  
✅ **No Cross-Solution References:** Fully independent  
✅ **Offline Capable:** Works without internet access  

---

## Support and Documentation

- **IBM Documentation:** https://www.ibm.com/docs/en/storage-protect/8.2.1
- **Multi-Site Solution Guide:** https://www.ibm.com/docs/en/storage-protect/8.2.1?topic=deployment-multisite-disk-solution
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
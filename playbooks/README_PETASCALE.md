# Petascale Data Protection Playbooks

## Overview

This directory contains playbooks and configuration files for deploying and managing petascale IBM Storage Protect Server deployments (500+ TB capacity).

## Documentation

- **Design Document**: [docs/design/design-petascale.md](../docs/design/design-petascale.md)
- **User Guide**: [docs/guides/petascale-guide.md](../docs/guides/petascale-guide.md)
- **IBM White Paper**: [Petascale Data Protection](https://www.ibm.com/support/pages/system/files/inline-files/$FILE/Petascale_Data_Protection.pdf)

## Playbooks

### 1. petascale_deploy.yml

**Purpose**: Deploy a petascale-capable IBM Storage Protect Server using the blueprint orchestration pattern.

**Features**:
- Automated 3-phase deployment (Install → Storage → Configure)
- Pre-deployment validation
- Post-deployment verification
- Support for Large configuration (500+ TB)

**Usage**:
```bash
ansible-playbook petascale_deploy.yml \
  -i inventory/petascale.ini \
  -e @vars/petascale_large_vars.yml \
  -e @vars/petascale_secrets.yml \
  --vault-password-file vault_pass.txt
```

**Tags**:
- `install`, `phase1`: Installation phase only
- `storage`, `phase2`: Storage preparation only
- `configure`, `phase3`: Configuration phase only
- `verify`, `post`: Post-deployment verification only

### 2. petascale_monitor.yml

**Purpose**: Comprehensive monitoring and health checks for petascale deployments.

**Features**:
- Server service status
- Database utilization
- Storage pool utilization
- Active sessions monitoring
- Filesystem utilization
- LVM volume information
- Recent error detection
- Database backup status
- Health summary report

**Usage**:
```bash
ansible-playbook petascale_monitor.yml \
  -i inventory/petascale.ini \
  -e @vars/petascale_secrets.yml \
  --vault-password-file vault_pass.txt
```

**Tags**:
- `service`, `health`: Service status checks
- `status`: Server status
- `database`, `capacity`: Database utilization
- `storage`: Storage pool utilization
- `sessions`, `performance`: Session monitoring
- `filesystem`: Filesystem checks
- `lvm`: LVM volume information
- `errors`: Error detection
- `backup`: Backup status
- `summary`: Health summary

## Configuration Files

### vars/petascale_large_vars.yml

Main configuration file for Large/Petascale deployments.

**Key Settings**:
- `server_size: "large"` - Petascale configuration
- `storage_prepare_size: "large"` - 500+ TB storage
- `sp_server_active_log_size: 524032` - 512 GB active log
- `maxcap: "500G"` - Database backup capacity
- `dbbk_streams: "8"` - Parallel backup streams

**Storage Allocation** (automatically configured):
- Database: 4-4.05 TB
- Active Log: 550-600 GB (LVM striped)
- Archive Log: 4-4.05 TB (LVM striped)
- File Storage: 500-500.05 TB
- Backup: 16-16.05 TB

### vars/petascale_secrets.yml.example

Template for sensitive credentials. Copy and encrypt with Ansible Vault.

**Setup**:
```bash
# Copy template
cp vars/petascale_secrets.yml.example vars/petascale_secrets.yml

# Edit with your passwords
vi vars/petascale_secrets.yml

# Encrypt with Ansible Vault
ansible-vault encrypt vars/petascale_secrets.yml

# Create vault password file
echo "your-vault-password" > vault_pass.txt
chmod 600 vault_pass.txt

# Add to .gitignore
echo "vault_pass.txt" >> ../.gitignore
echo "vars/petascale_secrets.yml" >> ../.gitignore
```

### inventory/petascale.ini.example

Example inventory file for petascale deployments.

**Setup**:
```bash
# Copy template
cp inventory/petascale.ini.example inventory/petascale.ini

# Edit with your host information
vi inventory/petascale.ini

# Test connectivity
ansible -i inventory/petascale.ini sp_servers -m ping
```

## Deployment Sizes

| Size | Storage | Sessions | Database | Use Case |
|------|---------|----------|----------|----------|
| **XSmall** | ~10 TB | 75 | ~250 GB | Development/Test |
| **Small** | ~40 TB | 250 | ~1 TB | Small Production |
| **Medium** | ~180 TB | 500 | ~2 TB | Medium Production |
| **Large** | ~500+ TB | 1000+ | ~4+ TB | **Petascale Production** |

## Quick Start

### 1. Prerequisites

- Ansible >= 2.15.0
- Python 3.9+ on managed nodes
- IBM Storage Protect 8.1.23+
- Sufficient disk space (500+ TB for Large)
- High-performance network (10+ GbE)
- Root/sudo access

### 2. Install Collection

```bash
ansible-galaxy collection install ibm.storage_protect
```

### 3. Prepare Configuration

```bash
# Copy and customize inventory
cp inventory/petascale.ini.example inventory/petascale.ini
vi inventory/petascale.ini

# Copy and customize variables
cp vars/petascale_secrets.yml.example vars/petascale_secrets.yml
vi vars/petascale_secrets.yml

# Encrypt secrets
ansible-vault encrypt vars/petascale_secrets.yml
```

### 4. Deploy

```bash
ansible-playbook petascale_deploy.yml \
  -i inventory/petascale.ini \
  -e @vars/petascale_large_vars.yml \
  -e @vars/petascale_secrets.yml \
  --vault-password-file vault_pass.txt
```

### 5. Monitor

```bash
ansible-playbook petascale_monitor.yml \
  -i inventory/petascale.ini \
  -e @vars/petascale_secrets.yml \
  --vault-password-file vault_pass.txt
```

## Performance Targets (Large Configuration)

| Metric | Target | Notes |
|--------|--------|-------|
| **Backup Throughput** | 10-50 TB/hour | Network and storage dependent |
| **Restore Throughput** | 5-25 TB/hour | Data location dependent |
| **Concurrent Sessions** | 1000+ | Configurable |
| **Database Size** | 4+ TB | Scales with data volume |
| **Storage Capacity** | 500+ TB | Per storage pool |
| **Deduplication Ratio** | 10:1 to 50:1 | Workload dependent |
| **Supported Clients** | 1000+ | Backup agents |

## Hardware Requirements (Large Configuration)

### Minimum Specifications

- **CPU**: 32+ cores
- **RAM**: 128+ GB
- **Network**: 10 GbE (25/40/100 GbE recommended)
- **Storage**:
  - Database: 4-4.05 TB (multiple disks)
  - Active Log: 550-600 GB (LVM striped)
  - Archive Log: 4-4.05 TB (LVM striped)
  - File Storage: 500-500.05 TB (multiple disks)
  - Backup: 16-16.05 TB (multiple disks)

### Supported Operating Systems

- Red Hat Enterprise Linux 7.x, 8.x, 9.x
- SUSE Linux Enterprise Server 12, 15
- Ubuntu 18.04, 20.04, 22.04

## Scaling Strategies

### Vertical Scaling (Expand Existing Server)

1. **Add Storage Volumes**:
   - Add disks to existing storage pools
   - Expand database capacity
   - Increase backup storage

2. **Increase Performance**:
   - Increase session limits beyond 1000
   - Add CPU/RAM resources
   - Optimize network bandwidth

3. **Expand Capacity**:
   - Add more file storage volumes
   - Expand database volumes
   - Increase backup capacity

### Horizontal Scaling (Multiple Servers)

1. **Deploy Additional Servers**:
   - Use same playbooks with different inventory
   - Configure server-to-server replication
   - Implement load balancing

2. **Distribute Clients**:
   - Assign clients to specific servers
   - Balance load across servers
   - Configure failover

3. **Multi-Site Deployment**:
   - Deploy servers in multiple datacenters
   - Configure replication between sites
   - Implement disaster recovery

## Troubleshooting

### Common Issues

#### 1. Storage Preparation Fails

**Symptom**: "No disks available" error

**Solution**:
```bash
# Check available disks
lsblk -b -o NAME,SIZE,MOUNTPOINT,TYPE

# Verify disk sizes match configuration
# Large config requires:
# - Database: 4-4.05 TB disks
# - Active Log: 550-600 GB disks
# - Archive Log: 4-4.05 TB disks
# - File Storage: 500-500.05 TB disks
# - Backup: 16-16.05 TB disks
```

#### 2. Performance Issues

**Symptom**: Slow backup/restore operations

**Diagnosis**:
```bash
# Check database utilization
ansible-playbook petascale_monitor.yml -i inventory/petascale.ini --tags database

# Check active sessions
ansible-playbook petascale_monitor.yml -i inventory/petascale.ini --tags sessions

# Check network performance
iperf3 -c sp-server-01 -t 60
```

**Solutions**:
- Increase active log size
- Run database reorganization
- Add more database volumes
- Optimize network (enable jumbo frames)

#### 3. Session Limit Reached

**Symptom**: Clients cannot connect

**Solution**:
```bash
# Check current sessions
dsmadmc -id=admin -pa='password' "query session"

# Increase max sessions
dsmadmc -id=admin -pa='password' "set maxsessions 1500"
```

### Debug Mode

Run playbooks with verbose output:

```bash
ansible-playbook petascale_deploy.yml \
  -i inventory/petascale.ini \
  -e @vars/petascale_large_vars.yml \
  -e @vars/petascale_secrets.yml \
  --vault-password-file vault_pass.txt \
  -vvv
```

## Best Practices

### Deployment

1. **Start Small, Scale Up**:
   - Test with xsmall or small configuration first
   - Validate thoroughly before scaling to large
   - Use blueprint for consistent deployments

2. **Plan Storage Carefully**:
   - Plan for 3-5 years of growth
   - Use high-performance storage (NVMe, SSD)
   - Separate storage pools by workload

3. **Network Design**:
   - Use dedicated backup network (separate VLAN)
   - Implement QoS for backup traffic
   - Enable jumbo frames (MTU 9000)
   - Plan for bandwidth growth

### Operations

1. **Monitoring**:
   - Run petascale_monitor.yml daily
   - Set up alerts for critical thresholds
   - Track growth trends
   - Monitor performance metrics

2. **Maintenance**:
   - Daily: Database backups, activity log review
   - Weekly: Storage pool reclamation, expiration processing
   - Monthly: Database reorganization, capacity planning review

3. **Security**:
   - Use Ansible Vault for all sensitive data
   - Implement SSL/TLS for all connections
   - Regular security audits
   - Role-based access control

## Support and Resources

### Documentation

- [Petascale Design Document](../docs/design/design-petascale.md)
- [Petascale User Guide](../docs/guides/petascale-guide.md)
- [SP Server Lifecycle Guide](../docs/guides/sp-server-lifecycle-guide.md)
- [Blueprint Configuration Guide](../docs/guides/sp-blueprint-conf-solution-guide.md)

### IBM Resources

- [IBM Storage Protect 8.1.27 Documentation](https://www.ibm.com/docs/en/storage-protect/8.1.27)
- [Petascale Data Protection White Paper](https://www.ibm.com/support/pages/system/files/inline-files/$FILE/Petascale_Data_Protection.pdf)
- [IBM Support](https://www.ibm.com/support)

### Community

- [Ansible Galaxy](https://galaxy.ansible.com/ibm/storage_protect)
- [GitHub Repository](https://github.com/IBM/ansible-storage-protect)

## Contributing

For contributions, please refer to [CONTRIBUTING.md](../CONTRIBUTING.md).

## License

See [LICENSE](../LICENSE) for license information.

---

**Version**: 1.0  
**Last Updated**: 2026-03-29  
**Maintainer**: IBM Storage Protect Ansible Team
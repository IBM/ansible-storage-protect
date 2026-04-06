# IBM Storage Protect Ansible Solutions - User Guides

## Overview

This directory contains comprehensive user guides for all IBM Storage Protect Ansible solutions. Each guide provides detailed operational procedures, configuration references, troubleshooting steps, and best practices.

## Available User Guides

### 1. [SP Server Lifecycle Management](sp-server-lifecycle-guide.md)
Complete lifecycle management for IBM Storage Protect Server including installation, configuration, monitoring, upgrade, and removal.

**Key Operations:**
- Complete deployment (end-to-end)
- Installation only
- Configuration only
- Monitoring and health checks
- Server upgrade
- Server uninstallation

**Use Cases:**
- New server deployment
- Server upgrades
- Disaster recovery
- Capacity expansion

---

### 2. [BA Client Lifecycle Management](ba-client-lifecycle-guide.md)
Complete lifecycle management for Backup-Archive Client across Linux and Windows platforms.

**Key Operations:**
- Complete deployment (Linux/Windows)
- Installation only
- Client configuration
- Schedule configuration
- Client upgrade
- Client uninstallation

**Use Cases:**
- Mass client deployment
- Client standardization
- Version upgrades
- Client migration

---

### 3. Storage Agent Lifecycle Management

#### Overview
Manages Storage Agent configuration for LAN-Free backup operations, enabling direct data movement between clients and storage devices.

#### Key Operations

##### 3.1 Complete Deployment
```bash
ansible-playbook solutions/storage-agent-lifecycle/deploy.yml \
  -i inventory.ini \
  -e @vars/prod.yml \
  -e @vars/secrets.yml \
  --ask-vault-pass
```

**Configuration Parameters:**
```yaml
# vars/prod.yml
stg_agent_name: "stgagent01"
stg_agent_password: "AgentPassword@@123"
stg_agent_server_name: "SERVER1"
stg_agent_hl_add: "192.168.1.50"
lladdress: "1502"
server_tcp_port: "1500"
server_hl_address: "192.168.1.10"
library: "TAPELIB01"
device: "/dev/sg1"
copygroup_domain: "LANFREEDOMAIN"
stg_pool: "LANFREEPOOL"
```

##### 3.2 LAN-Free Validation
```bash
ansible-playbook solutions/storage-agent-lifecycle/validate.yml \
  -i inventory.ini \
  -e "validate_lan_free=true" \
  -e "node_name=client01" \
  -e "stg_agent_name=stgagent01" \
  -e "max_attempts=3"
```

#### Common Issues

**Issue: Storage Agent Not Responding**
```bash
# Check agent process
ps aux | grep dsmsta

# View agent log
tail -100 /opt/tivoli/tsm/StorageAgent/bin/dsmsta.log

# Restart agent
pkill dsmsta
nohup /opt/tivoli/tsm/StorageAgent/bin/dsmsta &
```

**Issue: LAN-Free Validation Fails**
```bash
# Verify SCSI path
dsmadmc -id=admin -pa=admin "q path * * srctype=server"

# Check device access
ls -l /dev/sg1

# Test device
mt -f /dev/sg1 status
```

---

### 4. Operations Center Management

#### Overview
Manages IBM Storage Protect Operations Center for web-based administration and monitoring.

#### Key Operations

##### 4.1 Configure Operations Center
```bash
ansible-playbook solutions/operations-center/configure.yml \
  -i inventory.ini \
  -e "admin_name=admin" \
  -e "action=configure" \
  -e @vars/secrets.yml \
  --ask-vault-pass
```

##### 4.2 Manage OC Service
```bash
# Start OC
ansible-playbook solutions/operations-center/manage.yml \
  -i inventory.ini \
  -e "action=restart"

# Stop OC
ansible-playbook solutions/operations-center/manage.yml \
  -i inventory.ini \
  -e "action=stop"
```

#### Access Operations Center
After configuration, access at: `https://<hostname>:11443/oc`

#### Common Issues

**Issue: OC Service Won't Start**
```bash
# Check service status
systemctl status opscenter.service

# View logs
journalctl -u opscenter.service -n 50

# Check port availability
netstat -tuln | grep 11443

# Restart service
systemctl restart opscenter.service
```

---

### 5. Data Protection for DB2

#### Overview
Complete DB2 data protection lifecycle including installation, backup, restore, query, and delete operations.

#### Key Operations

##### 5.1 Complete Deployment
```bash
ansible-playbook solutions/data-protection-db2/deploy.yml \
  -i inventory.ini \
  -e @vars/prod.yml \
  -e @vars/secrets.yml \
  --ask-vault-pass
```

**Configuration:**
```yaml
# vars/prod.yml
storage_protect_server_name: "SERVER1"
storage_protect_server_ip: "192.168.1.10"
db2_instance: "db2inst1"
db2_database: "SAMPLE"
```

##### 5.2 Backup Operations
```bash
# Full backup
ansible-playbook solutions/data-protection-db2/backup.yml \
  -i inventory.ini \
  -e "db2_database=SAMPLE" \
  -e "db2_instance=db2inst1" \
  -e "db2_backup_online=true"

# Incremental backup
ansible-playbook solutions/data-protection-db2/backup.yml \
  -i inventory.ini \
  -e "db2_database=SAMPLE" \
  -e "db2_backup_type=incremental"
```

##### 5.3 Restore Operations
```bash
ansible-playbook solutions/data-protection-db2/restore.yml \
  -i inventory.ini \
  -e "db2_database=SAMPLE" \
  -e "db2_instance=db2inst1" \
  -e "db2_restore_replace_existing=true" \
  -e "db2_restore_taken_at=20260326120000"
```

##### 5.4 Query Operations
```bash
ansible-playbook solutions/data-protection-db2/query.yml \
  -i inventory.ini \
  -e "db2_database=SAMPLE" \
  -e "db2_query_type=full" \
  -e "db2_query_verbose=true"
```

##### 5.5 Delete Operations
```bash
ansible-playbook solutions/data-protection-db2/delete.yml \
  -i inventory.ini \
  -e "db2_database=SAMPLE" \
  -e "db2_delete_type=full" \
  -e "db2_delete_filter_type=taken_at" \
  -e "db2_delete_filter_value=20260301000000"
```

#### Common Issues

**Issue: Backup Fails - API Not Found**
```bash
# Verify API installation
rpm -q TIVsm-API64

# Check dsm.opt configuration
cat /opt/tivoli/tsm/client/api/bin64/dsm.opt

# Test API connectivity
dsmc query session
```

**Issue: Restore Fails - Insufficient Space**
```bash
# Check available space
df -h /db2/data

# Query backup size
dsmadmc -id=admin -pa=admin "q occupancy SAMPLE"

# Free up space or expand filesystem
```

---

### 6. Data Protection for SAP HANA

#### Overview
SAP HANA data protection using IBM Storage Protect for ERP.

#### Key Operations

##### 6.1 Complete Deployment
```bash
ansible-playbook solutions/data-protection-sap/deploy.yml \
  -i inventory.ini \
  -e @vars/prod.yml \
  -e @vars/secrets.yml \
  --ask-vault-pass
```

**Configuration:**
```yaml
# vars/prod.yml
sap_system_id: "H01"
hana_instance: "00"
hana_database: "SYSTEMDB"
hana_user: "SYSTEM"
backup_prefix: "COMPLETE_DATA_BACKUP"
```

##### 6.2 HANA Backup
```bash
ansible-playbook solutions/data-protection-sap/hana/backup.yml \
  -i inventory.ini \
  -e "sap_system_id=H01" \
  -e "backup_type=complete" \
  -e @vars/secrets.yml \
  --ask-vault-pass
```

##### 6.3 HANA Restore
```bash
ansible-playbook solutions/data-protection-sap/hana/restore.yml \
  -i inventory.ini \
  -e "sap_system_id=H01" \
  -e "backup_id=1234567890" \
  -e @vars/secrets.yml \
  --ask-vault-pass
```

#### Common Issues

**Issue: HANA Backup Fails**
```bash
# Check HANA status
su - h01adm
HDB info

# Verify backint configuration
cat /usr/sap/H01/SYS/global/hdb/opt/hdbconfig/param

# Check Storage Protect connectivity
dsmc query session

# Review HANA backup log
cat /usr/sap/H01/HDB00/backup.log
```

---

### 7. Security Management

#### Overview
Manages SSL/TLS certificates for secure communication between Storage Protect components.

#### Key Operations

##### 7.1 Complete Certificate Deployment
```bash
ansible-playbook solutions/security-management/deploy.yml \
  -i inventory.ini \
  -e @vars/prod.yml \
  -e @vars/secrets.yml \
  --ask-vault-pass
```

**Configuration:**
```yaml
# vars/prod.yml
cert_admin_client: "admin-client"
cert_sp_server: "sp-server"
cert_sp_clients: "ba_clients"
local_cert_dir: "/tmp/certificates"
```

##### 7.2 Generate Certificate
```bash
ansible-playbook solutions/security-management/certificate-management.yml \
  -i inventory.ini \
  -e "operation=generate" \
  -e "cert_label=SP_CERT_2026" \
  -e @vars/secrets.yml \
  --ask-vault-pass
```

##### 7.3 Distribute Certificate
```bash
ansible-playbook solutions/security-management/certificate-management.yml \
  -i inventory.ini \
  -e "operation=distribute" \
  -e "cert_label=SP_CERT_2026" \
  -e "target_clients=ba_clients"
```

#### Certificate Management Commands

```bash
# List certificates on server
dsmadmc -id=admin -pa=admin "q certificate"

# List certificates on client
gsk8capicmd_64 -cert -list -db /opt/tivoli/tsm/client/ba/bin/dsmcert.kdb -stashed

# Add certificate to client
gsk8capicmd_64 -cert -add \
  -label SP_CERT_2026 \
  -file /tmp/SP_CERT_2026.arm \
  -db /opt/tivoli/tsm/client/ba/bin/dsmcert.kdb \
  -stashed

# Delete old certificate
gsk8capicmd_64 -cert -delete \
  -label OLD_CERT \
  -db /opt/tivoli/tsm/client/ba/bin/dsmcert.kdb \
  -stashed
```

#### Common Issues

**Issue: Certificate Import Fails**
```bash
# Verify certificate file
file /tmp/SP_CERT_2026.arm

# Check keystore
ls -l /opt/tivoli/tsm/client/ba/bin/dsmcert.kdb

# Verify keystore password
gsk8capicmd_64 -cert -list \
  -db /opt/tivoli/tsm/client/ba/bin/dsmcert.kdb \
  -stashed

# Recreate keystore if corrupted
gsk8capicmd_64 -keydb -create \
  -db /opt/tivoli/tsm/client/ba/bin/dsmcert.kdb \
  -pw password \
  -stash
```

---

## Common Operational Patterns

### 1. Multi-Environment Deployment

```bash
# Deploy to development
ansible-playbook solutions/*/deploy.yml \
  -i inventory.ini \
  -e @vars/dev.yml \
  -e @vars/secrets.yml \
  --ask-vault-pass \
  --limit dev_hosts

# Deploy to production
ansible-playbook solutions/*/deploy.yml \
  -i inventory.ini \
  -e @vars/prod.yml \
  -e @vars/secrets.yml \
  --ask-vault-pass \
  --limit prod_hosts
```

### 2. Phased Rollout

```bash
# Phase 1: Deploy to pilot group
ansible-playbook solutions/*/deploy.yml \
  -i inventory.ini \
  -e @vars/prod.yml \
  --limit pilot_group

# Phase 2: Verify pilot
ansible-playbook solutions/*/monitor.yml \
  -i inventory.ini \
  --limit pilot_group

# Phase 3: Deploy to remaining hosts
ansible-playbook solutions/*/deploy.yml \
  -i inventory.ini \
  -e @vars/prod.yml \
  --limit '!pilot_group'
```

### 3. Disaster Recovery

```bash
# 1. Deploy SP Server
ansible-playbook solutions/sp-server-lifecycle/deploy.yml \
  -i dr-inventory.ini \
  -e @vars/dr.yml

# 2. Deploy BA Clients
ansible-playbook solutions/ba-client-lifecycle/deploy.yml \
  -i dr-inventory.ini \
  -e @vars/dr.yml

# 3. Configure Storage Agent
ansible-playbook solutions/storage-agent-lifecycle/deploy.yml \
  -i dr-inventory.ini \
  -e @vars/dr.yml

# 4. Verify all components
ansible-playbook solutions/*/monitor.yml \
  -i dr-inventory.ini
```

### 4. Health Check Automation

```bash
# Create health check script
cat > /usr/local/bin/sp-health-check.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
LOG_DIR=/var/log/sp-health-checks
mkdir -p $LOG_DIR

# Check all solutions
for solution in sp-server-lifecycle ba-client-lifecycle storage-agent-lifecycle; do
  ansible-playbook solutions/${solution}/monitor.yml \
    -i inventory.ini \
    > ${LOG_DIR}/${solution}_${DATE}.log 2>&1
done

# Send report
mail -s "SP Health Check Report" admin@example.com < ${LOG_DIR}/report_${DATE}.txt
EOF

chmod +x /usr/local/bin/sp-health-check.sh

# Schedule daily health checks
echo "0 6 * * * /usr/local/bin/sp-health-check.sh" | crontab -
```

## Security Best Practices

### 1. Ansible Vault Usage

```bash
# Create encrypted secrets file
ansible-vault create vars/secrets.yml

# Edit encrypted file
ansible-vault edit vars/secrets.yml

# Change vault password
ansible-vault rekey vars/secrets.yml

# View encrypted file
ansible-vault view vars/secrets.yml
```

### 2. Credential Management

```yaml
# vars/secrets.yml (encrypted)
---
# Server Credentials
sp_server_admin_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...

# Client Credentials
node_passwords:
  client01: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...
  client02: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...

# Database Credentials
db2_passwords:
  instance: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          ...
```

### 3. Access Control

```ini
# inventory.ini with access control
[sp_servers]
sp-server-01 ansible_host=192.168.1.10

[sp_servers:vars]
ansible_user=spuser
ansible_become=yes
ansible_become_method=sudo
ansible_become_user=root
```

## Troubleshooting Resources

### Log Aggregation

```bash
# Collect logs from all hosts
ansible all -i inventory.ini -m fetch \
  -a "src=/var/log/tsm/dsmerror.log dest=/tmp/logs/{{ inventory_hostname }}/"

# Search logs for errors
grep -r "ANS" /tmp/logs/ | grep -i error
```

### Performance Analysis

```bash
# Check resource usage
ansible all -i inventory.ini -m shell \
  -a "top -b -n 1 | head -20"

# Check disk I/O
ansible all -i inventory.ini -m shell \
  -a "iostat -x 1 5"

# Check network throughput
ansible all -i inventory.ini -m shell \
  -a "iftop -t -s 10"
```

### Connectivity Testing

```bash
# Test all connections
ansible all -i inventory.ini -m ping

# Test specific ports
ansible all -i inventory.ini -m wait_for \
  -a "host=192.168.1.10 port=1500 timeout=5"
```

## Support and Resources

### Documentation
- [IBM Storage Protect Documentation](https://www.ibm.com/docs/en/storage-protect)
- [Ansible Documentation](https://docs.ansible.com/)
- [Collection GitHub](https://github.com/IBM/ansible-storage-protect)

### Community
- [IBM Community](https://community.ibm.com/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/ibm-spectrum-protect)
- [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/)

### Training
- IBM Storage Protect Administration (Course Code: TS619G)
- Ansible Automation Platform (Red Hat DO374)
- Linux System Administration (RHCSA)

### Support Channels
- IBM Support Portal: https://www.ibm.com/support
- GitHub Issues: https://github.com/IBM/ansible-storage-protect/issues
- Email: support@ibm.com

---

## Quick Reference

### Common Commands

```bash
# Deploy solution
ansible-playbook solutions/<solution>/deploy.yml -i inventory.ini -e @vars/prod.yml --ask-vault-pass

# Monitor solution
ansible-playbook solutions/<solution>/monitor.yml -i inventory.ini

# Upgrade solution
ansible-playbook solutions/<solution>/upgrade.yml -i inventory.ini -e "version=X.Y.Z"

# Uninstall solution
ansible-playbook solutions/<solution>/uninstall.yml -i inventory.ini --extra-vars "confirm_uninstall=yes"
```

### Environment Variables

```bash
# Set Ansible configuration
export ANSIBLE_CONFIG=/path/to/ansible.cfg
export ANSIBLE_INVENTORY=/path/to/inventory.ini
export ANSIBLE_VAULT_PASSWORD_FILE=/path/to/.vault_pass

# Set Storage Protect credentials
export STORAGE_PROTECT_SERVERNAME=SERVER1
export STORAGE_PROTECT_USERNAME=admin
export STORAGE_PROTECT_PASSWORD=password
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-03-26  
**Maintained By**: IBM Storage Protect Ansible Team
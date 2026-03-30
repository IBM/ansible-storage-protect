'password' "query node"

# Update node
dsmadmc -id=admin -pa='password' \
  "update node NODE01 maxnummp=8"
```

#### Database Management
```bash
# Query database
dsmadmc -id=admin -pa='password' "query db f=d"

# Backup database
dsmadmc -id=admin -pa='password' "backup db type=full"

# Query backup history
dsmadmc -id=admin -pa='password' "query dbbackup"
```

### B. Variable Reference

#### Required Variables

```yaml
# Installation
sp_server_version: "8.1.27.0"
sp_server_state: "present"
sp_server_bin_repo: "/path/to/binaries"

# Blueprint
server_blueprint: true
server_size: "large"  # xsmall, small, medium, large
storage_prepare_size: "large"

# Server
server_name: "SERVER01"
instance_dir: "/tsminst1"

# Passwords (use vault)
ssl_password: "{{ vault_ssl_password }}"
server_password: "{{ vault_server_password }}"
admin_password: "{{ vault_admin_password }}"
dbbk_password: "{{ vault_dbbk_password }}"
```

#### Optional Variables

```yaml
# Backup schedule
backup_start_time: "22:00"
backup_start_time_string: "10PM"

# Database backup
maxcap: "500G"
dbbk_streams: "8"
dbbk_compress: "YES"

# User configuration
tsm_user: "tsminst1"
tsm_group: "tsmusers"
tsm_user_password: "{{ vault_tsm_user_password }}"
```

### C. Sizing Reference Table

| Configuration | Database | Active Log | Archive Log | File Storage | Backup | Sessions | Clients |
|---------------|----------|------------|-------------|--------------|--------|----------|---------|
| **XSmall** | 200-250 GB | 30-80 GB | 251-300 GB | 10-10.05 TB | 1-1.05 TB | 75 | <100 |
| **Small** | 1-1.05 TB | 140-190 GB | 1-1.005 TB | 38-38.05 TB | 3-3.05 TB | 250 | 100-500 |
| **Medium** | 2-2.005 TB | 140-190 GB | 2-2.005 TB | 180-180.05 TB | 10-10.05 TB | 500 | 500-1000 |
| **Large** | 4-4.05 TB | 550-600 GB | 4-4.05 TB | 500-500.05 TB | 16-16.05 TB | 1000+ | 1000+ |

### D. Port Reference

| Port | Protocol | Purpose | Required |
|------|----------|---------|----------|
| 1500 | TCP | Client-Server communication | Yes |
| 1543 | TCP | Administrative console (HTTPS) | Yes |
| 1580 | TCP | HTTP administrative console | Optional |
| 32768-65535 | TCP | Dynamic ports for data transfer | Yes |

### E. File Locations

```bash
# SP Server installation
/opt/tivoli/tsm/server/

# Instance directory
/tsminst1/

# Database volumes
/tsminst1/TSMdbspace*/

# Active log
/tsminst1/TSMalog/

# Archive log
/tsminst1/TSMarchlog/

# File storage pools
/tsminst1/TSMfile*/

# Backup volumes
/tsminst1/TSMbkup*/

# Activity log
/tsminst1/actlog/dsmserv.log

# DB2 diagnostic log
/tsminst1/db2dump/db2diag.log

# Server options
/opt/tivoli/tsm/server/bin/dsmserv.opt

# Server configuration
/opt/tivoli/tsm/server/bin/dsmserv.dsk
```

### F. Troubleshooting Checklist

#### Pre-Deployment Checklist

- [ ] Ansible version >= 2.15.0
- [ ] Python 3.9+ on managed nodes
- [ ] Collection installed and up-to-date
- [ ] Vault file created and encrypted
- [ ] Inventory file configured
- [ ] Variables file prepared
- [ ] Sufficient disk space available
- [ ] Disks unformatted and unmounted
- [ ] Network connectivity verified
- [ ] Firewall rules configured
- [ ] Root/sudo access confirmed

#### Post-Deployment Checklist

- [ ] Server started successfully
- [ ] Database initialized
- [ ] Storage pools created
- [ ] Policies configured
- [ ] Schedules defined
- [ ] Admin user created
- [ ] SSL certificates configured
- [ ] Systemd service enabled
- [ ] Monitoring configured
- [ ] Backup schedule tested
- [ ] Documentation updated

#### Health Check Checklist

- [ ] Server status: Running
- [ ] Database utilization: <80%
- [ ] Storage pool utilization: <80%
- [ ] Active log utilization: <80%
- [ ] No critical errors in activity log
- [ ] Database backup completed successfully
- [ ] Session count within limits
- [ ] Network connectivity normal
- [ ] Disk I/O performance normal
- [ ] No filesystem full warnings

### G. Performance Targets

#### Petascale Performance Targets (Large Configuration)

| Metric | Target | Notes |
|--------|--------|-------|
| **Backup Throughput** | 10-50 TB/hour | Network and storage dependent |
| **Restore Throughput** | 5-25 TB/hour | Data location dependent |
| **Concurrent Sessions** | 1000+ | Configurable |
| **Database Size** | 4+ TB | Scales with data volume |
| **Storage Capacity** | 500+ TB | Per storage pool |
| **Deduplication Ratio** | 10:1 to 50:1 | Workload dependent |
| **Database Backup Time** | <4 hours | For 4 TB database |
| **Reclamation Rate** | 50-100 GB/hour | Depends on fragmentation |

### H. Glossary

| Term | Definition |
|------|------------|
| **Active Log** | Transaction log for current database operations |
| **Archive Log** | Historical transaction logs for recovery |
| **Blueprint** | Pre-configured deployment template |
| **Deduplication** | Elimination of redundant data |
| **LVM** | Logical Volume Manager for disk management |
| **Node** | Client system registered with SP Server |
| **Petascale** | Data volumes in petabytes (1000+ TB) |
| **Policy Domain** | Collection of policies for data management |
| **Reclamation** | Process to reclaim unused storage space |
| **Session** | Connection between client and server |
| **Storage Pool** | Logical container for backup data |
| **XFS** | High-performance filesystem used for SP Server |

### I. Support and Resources

#### IBM Documentation

- [IBM Storage Protect 8.1.27 Documentation](https://www.ibm.com/docs/en/storage-protect/8.1.27)
- [Installation Guide](https://www.ibm.com/docs/en/storage-protect/8.1.27?topic=servers-installing)
- [Administrator's Guide](https://www.ibm.com/docs/en/storage-protect/8.1.27?topic=servers-administering)
- [Petascale Data Protection White Paper](https://www.ibm.com/support/pages/system/files/inline-files/$FILE/Petascale_Data_Protection.pdf)

#### Collection Documentation

- [Design Document](../design/design-petascale.md)
- [SP Server Lifecycle Guide](sp-server-lifecycle-guide.md)
- [Blueprint Configuration Guide](sp-blueprint-conf-solution-guide.md)
- [BA Client Guide](ba-client-lifecycle-guide.md)

#### Community Resources

- [Ansible Galaxy](https://galaxy.ansible.com/ibm/storage_protect)
- [GitHub Repository](https://github.com/IBM/ansible-storage-protect)
- [IBM Support](https://www.ibm.com/support)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-29 | IBM Storage Protect Ansible Team | Initial release |

---

**End of Document**
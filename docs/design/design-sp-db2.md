# IBM Storage Protect Data Protection for DB2 Design

## Overview

The Data Protection for DB2 solution provides Ansible automation for complete DB2 database protection lifecycle using IBM Storage Protect. It enables administrators to install, configure, backup, restore, query, and delete DB2 database backups through a unified Ansible interface across AIX, Linux, and Windows platforms.

## Architecture

### Component Overview

```mermaid
graph TB
    subgraph "Ansible Control Node"
        InstallPB[dp_db2_install_playbook.yml]
        BackupPB[dp_db2_backup_playbook.yml]
        RestorePB[dp_db2_restore_playbook.yml]
        QueryPB[dp_db2_query_playbook.yml]
        DeletePB[dp_db2_delete_playbook.yml]
        
        PreCheckRole[dp_db2_precheck Role]
        ManageRole[dp_db2_manage Role]
        PostCheckRole[dp_db2_postcheck Role]
    end
    
    subgraph "Target DB2 Host"
        DB2Instance[DB2 Instance]
        TSMAPIClient[TSM API Client]
        DSMIConfig[DSMI Configuration]
        db2adutl[db2adutl Utility]
    end
    
    subgraph "Storage Protect Server"
        SPServer[SP Server]
        NodeRegistry[Node Registry]
        BackupData[Backup Storage]
    end
    
    InstallPB --> PreCheckRole
    InstallPB --> PostCheckRole
    BackupPB --> ManageRole
    RestorePB --> ManageRole
    QueryPB --> ManageRole
    DeletePB --> ManageRole
    
    PreCheckRole --> DB2Instance
    ManageRole --> DB2Instance
    PostCheckRole --> DSMIConfig
    
    DB2Instance --> TSMAPIClient
    TSMAPIClient --> SPServer
    db2adutl --> TSMAPIClient
    SPServer --> NodeRegistry
    SPServer --> BackupData
    
    style InstallPB fill:#e1f5ff
    style BackupPB fill:#e1f5ff
    style ManageRole fill:#fff4e1
    style DB2Instance fill:#ffe1f5
    style TSMAPIClient fill:#f0e1ff
    style SPServer fill:#e1ffe1
```

### Component Relationships

```mermaid
classDiagram
    class dp_db2_install_playbook {
        +target_hosts: string
        +become: true
        +roles: list
        +ba_client_install
        +dp_db2_precheck
        +dp_db2_postcheck
    }
    
    class dp_db2_manage_playbook {
        +target_hosts: string
        +db2_operation: string
        +db2_database: string
        +db2_instance: string
        +roles: list
    }
    
    class dp_db2_precheck_role {
        +check_db2_processes()
        +check_db2_binaries()
        +determine_architecture()
        +validate_environment()
    }
    
    class dp_db2_manage_role {
        +db2_operation: string
        +dispatch_operation()
        +backup_database()
        +restore_database()
        +query_backups()
        +delete_backups()
    }
    
    class dp_db2_postcheck_role {
        +validate_dsmi_config()
        +set_tsm_password()
        +recycle_db2_instance()
    }
    
    class TSMAPIClient {
        +DSMI_DIR: string
        +DSMI_CONFIG: string
        +DSMI_LOG: string
        +backup_api()
        +restore_api()
    }
    
    dp_db2_install_playbook --> dp_db2_precheck_role
    dp_db2_install_playbook --> dp_db2_postcheck_role
    dp_db2_manage_playbook --> dp_db2_manage_role
    dp_db2_manage_role --> TSMAPIClient
    dp_db2_postcheck_role --> TSMAPIClient
```

## Data Flow

### Installation Flow

```mermaid
sequenceDiagram
    participant User
    participant InstallPB as Install Playbook
    participant PreCheck as Precheck Role
    participant BAClient as BA Client Role
    participant PostCheck as Postcheck Role
    participant DB2 as DB2 Instance
    participant TSM as TSM API
    participant SP as SP Server
    
    User->>InstallPB: Execute installation
    InstallPB->>PreCheck: Validate environment
    PreCheck->>DB2: Check DB2 processes
    DB2-->>PreCheck: Process status
    PreCheck->>DB2: Check DB2 binaries
    DB2-->>PreCheck: Binary paths
    PreCheck->>DB2: Determine architecture
    DB2-->>PreCheck: 32/64-bit info
    
    alt Validation Failed
        PreCheck-->>User: Fail: Environment issues
    else Validation Passed
        InstallPB->>BAClient: Install BA Client
        BAClient->>TSM: Install TSM API
        TSM-->>BAClient: Installation complete
        
        InstallPB->>PostCheck: Configure DSMI
        PostCheck->>TSM: Set DSMI variables
        PostCheck->>TSM: Configure dsm.opt
        PostCheck->>TSM: Set password via dsmapipw
        TSM-->>PostCheck: Configuration complete
        
        PostCheck->>DB2: Recycle DB2 instance
        DB2-->>PostCheck: Instance restarted
        
        PostCheck->>SP: Register node
        SP-->>PostCheck: Node registered
        PostCheck-->>User: Installation complete
    end
```

### Backup Flow

```mermaid
sequenceDiagram
    participant User
    participant BackupPB as Backup Playbook
    participant Manage as Manage Role
    participant DB2 as DB2 Instance
    participant TSM as TSM API
    participant SP as SP Server
    
    User->>BackupPB: Execute backup
    BackupPB->>Manage: Invoke backup operation
    Manage->>Manage: Build BACKUP DATABASE command
    Manage->>Manage: Add compression options
    Manage->>Manage: Add encryption options
    Manage->>Manage: Add parallelism options
    
    Manage->>DB2: Execute BACKUP DATABASE
    DB2->>TSM: Transfer backup data
    TSM->>SP: Store backup
    SP-->>TSM: Backup stored
    TSM-->>DB2: Transfer complete
    DB2-->>Manage: Backup successful
    
    Manage->>Manage: Capture backup metadata
    Manage-->>User: Backup complete with details
```

### Restore Flow

```mermaid
sequenceDiagram
    participant User
    participant RestorePB as Restore Playbook
    participant Manage as Manage Role
    participant DB2 as DB2 Instance
    participant TSM as TSM API
    participant SP as SP Server
    
    User->>RestorePB: Execute restore
    RestorePB->>Manage: Invoke restore operation
    Manage->>Manage: Build RESTORE DATABASE command
    Manage->>Manage: Add timestamp/redirect options
    Manage->>Manage: Add tablespace options
    
    Manage->>DB2: Execute RESTORE DATABASE
    DB2->>TSM: Request backup data
    TSM->>SP: Retrieve backup
    SP-->>TSM: Backup data
    TSM-->>DB2: Transfer data
    DB2->>DB2: Restore database
    DB2-->>Manage: Restore successful
    
    Manage->>Manage: Capture restore metadata
    Manage-->>User: Restore complete with details
```

### Query Flow

```mermaid
sequenceDiagram
    participant User
    participant QueryPB as Query Playbook
    participant Manage as Manage Role
    participant db2adutl as db2adutl Utility
    participant TSM as TSM API
    participant SP as SP Server
    
    User->>QueryPB: Execute query
    QueryPB->>Manage: Invoke query operation
    Manage->>db2adutl: Execute query command
    db2adutl->>TSM: Query backup catalog
    TSM->>SP: Request backup list
    SP-->>TSM: Backup metadata
    TSM-->>db2adutl: Backup information
    db2adutl-->>Manage: Query results
    
    Manage->>Manage: Parse and format results
    Manage-->>User: Display backup list
```

### Delete Flow

```mermaid
sequenceDiagram
    participant User
    participant DeletePB as Delete Playbook
    participant Manage as Manage Role
    participant db2adutl as db2adutl Utility
    participant TSM as TSM API
    participant SP as SP Server
    
    User->>DeletePB: Execute delete
    DeletePB->>Manage: Invoke delete operation
    Manage->>db2adutl: Execute delete command
    db2adutl->>TSM: Delete backup request
    TSM->>SP: Mark backup for deletion
    SP-->>TSM: Deletion confirmed
    TSM-->>db2adutl: Delete successful
    db2adutl-->>Manage: Deletion results
    
    Manage->>Manage: Capture deletion metadata
    Manage-->>User: Delete complete with details
```

## Component Details

### 1. Playbook Layer

#### Installation Playbook

**File**: [`playbooks/dp_db2_install_playbook.yml`](../../playbooks/dp_db2_install_playbook.yml)

```yaml
Purpose: End-to-end DP for DB2 installation
Features:
  - BA Client installation
  - Pre-installation validation
  - DSMI configuration
  - Node registration
  - Post-installation validation
```

#### Backup Playbook

**File**: [`playbooks/dp_db2_backup_playbook.yml`](../../playbooks/dp_db2_backup_playbook.yml)

```yaml
Purpose: DB2 database backup operations
Features:
  - Full, incremental, delta backups
  - Online/offline backup support
  - Compression and encryption
  - Parallelism configuration
  - Tablespace-level backup
```

#### Restore Playbook

**File**: [`playbooks/dp_db2_restore_playbook.yml`](../../playbooks/dp_db2_restore_playbook.yml)

```yaml
Purpose: DB2 database restore operations
Features:
  - Complete database restore
  - Point-in-time recovery
  - Redirect restore
  - Tablespace restore
  - Log target configuration
```

#### Query Playbook

**File**: [`playbooks/dp_db2_query_playbook.yml`](../../playbooks/dp_db2_query_playbook.yml)

```yaml
Purpose: Query DB2 backup information
Features:
  - List available backups
  - Backup metadata retrieval
  - Timestamp information
  - Backup type identification
```

#### Delete Playbook

**File**: [`playbooks/dp_db2_delete_playbook.yml`](../../playbooks/dp_db2_delete_playbook.yml)

```yaml
Purpose: Delete DB2 backup data
Features:
  - Delete specific backups
  - Age-based deletion
  - Retention management
  - Deletion confirmation
```

### 2. Role Layer

**Path**: [`roles/`](../../roles/)

#### dp_db2_precheck Role

**Location**: [`roles/dp_db2_precheck/`](../../roles/dp_db2_precheck/)

##### Structure
```
roles/dp_db2_precheck/
├── README.md
├── defaults/main.yml
├── meta/main.yml
└── tasks/main.yml
```

##### Tasks
- Check DB2 processes are running
- Validate DB2 binary locations
- Determine 32-bit vs 64-bit architecture
- Verify DB2 instance ownership
- Validate environment variables

#### dp_db2_manage Role

**Location**: [`roles/dp_db2_manage/`](../../roles/dp_db2_manage/)

##### Structure
```
roles/dp_db2_manage/
├── README.md
├── defaults/main.yml
├── meta/main.yml
└── tasks/
    ├── main.yml
    ├── dp_db2_backup.yml
    ├── dp_db2_restore.yml
    ├── dp_db2_query.yml
    └── dp_db2_delete.yml
```

##### Default Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `db2_operation` | "" | Operation type (backup/restore/query/delete) |
| `db2_database` | "" | Database name |
| `db2_instance` | "" | DB2 instance name |
| `db2_user` | "" | DB2 username |
| `db2_backup_online` | true | Online backup flag |
| `db2_backup_compress` | false | Enable compression |
| `db2_backup_encrypt` | false | Enable encryption |
| `db2_backup_parallelism` | 1 | Number of parallel streams |
| `db2_restore_replace_existing` | false | Replace existing database |
| `db2_restore_taken_at` | "" | Backup timestamp for restore |

##### Tasks
- Dispatch to operation-specific task file
- Build DB2 command with options
- Execute DB2 backup/restore/query/delete
- Capture and return results

#### dp_db2_postcheck Role

**Location**: [`roles/dp_db2_postcheck/`](../../roles/dp_db2_postcheck/)

##### Structure
```
roles/dp_db2_postcheck/
├── README.md
├── defaults/main.yml
├── meta/main.yml
└── tasks/main.yml
```

##### Tasks
- Validate DSMI environment variables
- Configure dsm.opt file
- Set TSM password via dsmapipw
- Recycle DB2 instance
- Verify TSM API connectivity

### 3. Module Layer

While this solution primarily uses roles and shell commands, it integrates with:

**BA Client Module**: [`plugins/modules/sp_baclient_install.py`](../../plugins/modules/sp_baclient_install.py)
- Installs BA Client for TSM API

**Node Module**: [`plugins/modules/node.py`](../../plugins/modules/node.py)
- Registers DB2 node on SP Server

### 4. Utility Layer

**DSMI Configuration**:
- `DSMI_DIR`: TSM API installation directory
- `DSMI_CONFIG`: Path to dsm.opt configuration file
- `DSMI_LOG`: Path to TSM API log directory

**db2adutl Utility**:
- Query backup catalog
- Delete backup images
- Manage backup retention

## Execution Flow

### Complete Installation Workflow

```mermaid
flowchart TD
    Start([User Executes Install]) --> LoadVars[Load Variables]
    LoadVars --> PreCheck{Run Precheck}
    
    PreCheck --> CheckProc[Check DB2 Processes]
    CheckProc --> ProcOK{Processes<br/>Running?}
    ProcOK -->|No| FailProc[Fail: DB2 not running]
    ProcOK -->|Yes| CheckBin[Check DB2 Binaries]
    
    CheckBin --> BinOK{Binaries<br/>Found?}
    BinOK -->|No| FailBin[Fail: DB2 not installed]
    BinOK -->|Yes| CheckArch[Determine Architecture]
    
    CheckArch --> InstallBA[Install BA Client]
    InstallBA --> BASuccess{BA Install<br/>Success?}
    BASuccess -->|No| FailBA[Fail: BA installation error]
    BASuccess -->|Yes| PostCheck[Run Postcheck]
    
    PostCheck --> SetDSMI[Set DSMI Variables]
    SetDSMI --> ConfigOpt[Configure dsm.opt]
    ConfigOpt --> SetPass[Set TSM Password]
    SetPass --> RecycleDB2[Recycle DB2 Instance]
    RecycleDB2 --> RegisterNode[Register Node]
    
    RegisterNode --> RegSuccess{Registration<br/>Success?}
    RegSuccess -->|No| FailReg[Fail: Registration error]
    RegSuccess -->|Yes| Success[Installation Complete]
    
    FailProc --> End([End])
    FailBin --> End
    FailBA --> End
    FailReg --> End
    Success --> End
    
    style Start fill:#e1f5ff
    style End fill:#e1ffe1
    style FailProc fill:#ffe1e1
    style FailBin fill:#ffe1e1
    style FailBA fill:#ffe1e1
    style FailReg fill:#ffe1e1
    style Success fill:#e1ffe1
```

### Complete Backup Workflow

```mermaid
flowchart TD
    Start([User Executes Backup]) --> LoadVars[Load Variables]
    LoadVars --> ValidateDB{Database<br/>Specified?}
    ValidateDB -->|No| FailDB[Fail: Database required]
    ValidateDB -->|Yes| BuildCmd[Build BACKUP Command]
    
    BuildCmd --> AddType[Add Backup Type]
    AddType --> OnlineCheck{Online<br/>Backup?}
    OnlineCheck -->|Yes| AddOnline[Add ONLINE clause]
    OnlineCheck -->|No| AddOffline[Add OFFLINE clause]
    
    AddOnline --> CompressCheck{Compression<br/>Enabled?}
    AddOffline --> CompressCheck
    CompressCheck -->|Yes| AddCompress[Add COMPRESS clause]
    CompressCheck -->|No| EncryptCheck{Encryption<br/>Enabled?}
    AddCompress --> EncryptCheck
    
    EncryptCheck -->|Yes| AddEncrypt[Add ENCRYPT clause]
    EncryptCheck -->|No| ParallelCheck{Parallelism<br/>>1?}
    AddEncrypt --> ParallelCheck
    
    ParallelCheck -->|Yes| AddParallel[Add PARALLELISM clause]
    ParallelCheck -->|No| ExecBackup[Execute BACKUP]
    AddParallel --> ExecBackup
    
    ExecBackup --> BackupResult{Backup<br/>Success?}
    BackupResult -->|No| FailBackup[Fail: Backup error]
    BackupResult -->|Yes| CaptureInfo[Capture Backup Info]
    CaptureInfo --> Success[Backup Complete]
    
    FailDB --> End([End])
    FailBackup --> End
    Success --> End
    
    style Start fill:#e1f5ff
    style End fill:#e1ffe1
    style FailDB fill:#ffe1e1
    style FailBackup fill:#ffe1e1
    style Success fill:#e1ffe1
```

## Usage Examples

### Install Data Protection for DB2

```bash
# Set environment variables
export STORAGE_PROTECT_SERVERNAME="your_server_name"
export STORAGE_PROTECT_USERNAME="your_username"
export STORAGE_PROTECT_PASSWORD="your_password"

# Execute installation
ansible-playbook -i inventory.ini \
  ibm.storage_protect.dp_db2_install_playbook.yml \
  -e @vars/db2_install.yml
```

**vars/db2_install.yml**:
```yaml
target_hosts: "db2_servers"
db2_instance: "db2inst1"
db2_database: "SAMPLE"
ba_client_version: "8.1.27.0"
```

### Perform Full Online Backup

```bash
ansible-playbook -i inventory.ini \
  ibm.storage_protect.dp_db2_backup_playbook.yml \
  -e "target_hosts=db2_servers" \
  -e "db2_database=PRODDB" \
  -e "db2_instance=db2inst1" \
  -e "db2_backup_online=true" \
  -e "db2_backup_compress=true" \
  -e "db2_backup_parallelism=4"
```

### Restore Database to Point-in-Time

```bash
ansible-playbook -i inventory.ini \
  ibm.storage_protect.dp_db2_restore_playbook.yml \
  -e "target_hosts=db2_servers" \
  -e "db2_database=PRODDB" \
  -e "db2_restore_taken_at=20260330120000" \
  -e "db2_restore_replace_existing=true"
```

### Query Available Backups

```bash
ansible-playbook -i inventory.ini \
  ibm.storage_protect.dp_db2_query_playbook.yml \
  -e "target_hosts=db2_servers" \
  -e "db2_database=PRODDB"
```

### Delete Old Backups

```bash
ansible-playbook -i inventory.ini \
  ibm.storage_protect.dp_db2_delete_playbook.yml \
  -e "target_hosts=db2_servers" \
  -e "db2_database=PRODDB" \
  -e "db2_delete_older_than=30"
```

## Integration Points

### Storage Protect Server Integration

```mermaid
graph LR
    subgraph "DP DB2 Solution"
        DB2Backup[DB2 Backup]
        TSMAPIClient[TSM API Client]
    end
    
    subgraph "Storage Protect Server"
        NodeRegistry[Node Registry]
        BackupStorage[Backup Storage]
        PolicyMgmt[Policy Management]
    end
    
    DB2Backup --> TSMAPIClient
    TSMAPIClient -->|Register Node| NodeRegistry
    TSMAPIClient -->|Store Backup| BackupStorage
    NodeRegistry -->|Apply Policy| PolicyMgmt
    PolicyMgmt -->|Retention| BackupStorage
    
    style DB2Backup fill:#ffe1f5
    style TSMAPIClient fill:#f0e1ff
    style NodeRegistry fill:#e1ffe1
```

### BA Client Integration

```mermaid
graph TB
    subgraph "DP DB2 Components"
        DB2Instance[DB2 Instance]
        DSMIConfig[DSMI Configuration]
    end
    
    subgraph "BA Client"
        TSMAPILib[TSM API Library]
        dsmoptFile[dsm.opt]
        PasswordFile[TSM Password]
    end
    
    subgraph "SP Server"
        SPServer[Storage Protect Server]
    end
    
    DB2Instance --> DSMIConfig
    DSMIConfig -->|DSMI_DIR| TSMAPILib
    DSMIConfig -->|DSMI_CONFIG| dsmoptFile
    DSMIConfig -->|DSMI_LOG| PasswordFile
    TSMAPILib --> SPServer
    dsmoptFile --> SPServer
    
    style DB2Instance fill:#ffe1f5
    style TSMAPILib fill:#f0e1ff
    style SPServer fill:#e1ffe1
```

## Requirements

### Prerequisites
1. IBM DB2 Database installed and running
2. IBM Storage Protect Server installed and configured
3. Network connectivity between DB2 host and SP Server
4. Sufficient storage space for backups
5. Valid DB2 instance credentials
6. Valid Storage Protect admin credentials

### Environment Variables
```bash
STORAGE_PROTECT_SERVERNAME  # Server name (default: 'local')
STORAGE_PROTECT_USERNAME    # Admin username
STORAGE_PROTECT_PASSWORD    # Admin password
DSMI_DIR                    # TSM API installation directory
DSMI_CONFIG                 # Path to dsm.opt file
DSMI_LOG                    # Path to TSM API log directory
```

### Permissions
- Root or sudo access on DB2 host (become: true)
- DB2 instance owner permissions
- Storage Protect admin privileges for node registration
- File system permissions for DSMI configuration

### Platform Requirements

| Platform | DB2 Version | TSM API Version | Architecture |
|----------|-------------|-----------------|--------------|
| AIX | 10.5+ | 8.1.x | ppc64 |
| Linux | 10.5+ | 8.1.x | x86_64, s390x, ppc64le |
| Windows | 10.5+ | 8.1.x | x86_64 |

## Error Scenarios

### Common Errors and Resolutions

| Error | Cause | Resolution |
|-------|-------|------------|
| "DB2 instance not running" | DB2 processes not found | Start DB2 instance: `db2start` |
| "DB2 binaries not found" | DB2 not installed or PATH issue | Install DB2 or update PATH variable |
| "TSM API not found" | BA Client not installed | Install BA Client first |
| "DSMI variables not set" | Environment not configured | Run postcheck role to set DSMI variables |
| "Node not registered" | Node registration failed | Check SP Server connectivity and credentials |
| "Backup failed: insufficient space" | Storage full | Free up space or add storage |
| "Restore failed: backup not found" | Invalid timestamp or backup deleted | Query available backups first |
| "db2adutl command not found" | DB2 utilities not in PATH | Source DB2 profile: `. ~db2inst1/sqllib/db2profile` |

## Testing

**Test Files**: 
- [`tests/integration/targets/dp_db2/test_dp_db2_install.yml`](../../tests/integration/targets/dp_db2/test_dp_db2_install.yml)
- [`tests/integration/targets/dp_db2_manage/test_db2_operations.yml`](../../tests/integration/targets/dp_db2_manage/test_db2_operations.yml)

### Test Coverage
- Installation validation
- Backup operations (full, incremental, delta)
- Restore operations (complete, point-in-time)
- Query operations
- Delete operations
- Error handling validation
- Multi-platform testing (AIX, Linux, Windows)

## Security Considerations

1. **Credential Management**
   - DB2 passwords stored in Ansible Vault
   - TSM passwords set via dsmapipw (encrypted)
   - No logging of sensitive parameters (no_log: true)
   - Credentials passed via secure channels

2. **Encryption**
   - Support for backup encryption (db2_backup_encrypt)
   - SSL/TLS communication with SP Server
   - Encrypted password storage

3. **Access Control**
   - Requires DB2 instance owner privileges
   - Requires SP Server admin privileges
   - File permissions on DSMI configuration
   - Audit logging of all operations

4. **Network Security**
   - Secure communication between DB2 and SP Server
   - Firewall rules for TSM API ports
   - Network isolation for backup traffic

## Performance Considerations

- **Parallelism**: Configure `db2_backup_parallelism` for faster backups (default: 1)
- **Compression**: Enable `db2_backup_compress` to reduce backup size and network traffic
- **Buffer Sizes**: Tune DB2 backup buffer sizes for optimal performance
- **Network Bandwidth**: Ensure sufficient bandwidth for backup/restore operations
- **Storage Performance**: Use high-performance storage for backup staging
- **Idempotency**: All operations are idempotent and safe to re-run

## Future Enhancements

1. **Advanced Features**
   - Incremental forever backup strategy
   - Synthetic full backups
   - Backup validation and verification
   - Automated backup scheduling

2. **Monitoring Integration**
   - Backup success/failure notifications
   - Performance metrics collection
   - Capacity planning reports
   - SLA compliance tracking

3. **Multi-Database Support**
   - Parallel backup of multiple databases
   - Database group operations
   - Centralized backup management

4. **Cloud Integration**
   - Cloud-based backup storage
   - Hybrid cloud backup strategies
   - Cloud disaster recovery

## References

- [IBM Storage Protect Documentation](https://www.ibm.com/docs/en/storage-protect)
- [IBM DB2 Documentation](https://www.ibm.com/docs/en/db2)
- [DB2 Backup and Recovery Guide](https://www.ibm.com/docs/en/db2/11.5?topic=recovery-backing-up-databases)
- [TSM API Documentation](https://www.ibm.com/docs/en/storage-protect/8.1.27?topic=clients-api)
- [Ansible Module Development](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html)

## Related Components

- [`sp_server_install`](design-sp-server.md) - Storage Protect Server installation
- [`ba_client_install`](design-ba-client.md) - Backup-Archive client installation
- [`storage_agent_config`](design-storage-agent.md) - Storage Agent configuration
- [`oc_configure`](design-oc.md) - Operations Center configuration
- [Data Protection DB2 Guide](../guides/data-protection-db2-guide.md) - User guide

## Related Documentation

- [Playbook Analysis](../pb-analysis.md) - Section 5: Data Protection - DB2 Solution
- [Complete Technical Design](design-db2.md) - Detailed implementation specifications

---

**Document Version**: 2.0  
**Last Updated**: 2026-04-12  
**Author**: Reverse-engineered from codebase  
**Status**: Component design document aligned with OC design structure
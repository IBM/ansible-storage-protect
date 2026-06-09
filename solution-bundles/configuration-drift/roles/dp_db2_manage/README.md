# DB2 Backup, Restore, Query, Delete, and Extract with TSM via Ansible

This Ansible role automates **DB2 database operations** — backup, restore, query, delete, and extract — using **TSM (IBM Storage Protect)** as the backup medium.

---

## Overview

This role provides a unified interface for managing DB2 database backups and restores with TSM, including querying, deleting, and extracting backup images. It is designed for DB2 administrators who want to automate and standardize their backup and recovery workflows.

---

## Supported Operations

- **Backup**: Full, incremental, or delta backups using TSM
- **Restore**: Restore databases with optional rollforward
- **Query**: Query backups using `db2adutl`
- **Delete**: Delete backups using `db2adutl`
- **Extract**: Extract backup images from TSM

---

## Supported Platforms

- Linux (tested on RHEL)
- DB2 11.x and 12.x
- IBM Storage Protect (TSM) client installed and configured

---

## Key Variables

### Common Variables
| Variable              | Description                                           | Default   |
|-----------------------|------------------------------------------------------|-----------|
| db2_operation         | Operation to perform: backup, restore, query, delete | ""        |
| db2_database          | Name of the DB2 database to operate on               | ""        |
| db2_instance          | Name of the DB2 instance to use                      | ""        |
| db2_user              | DB2 user for authentication                          | ""        |
| db2_password          | DB2 password for authentication (optional)           | ""        |
| db2_chain             | Optional: chain number for logs                      | ""        |
| db2_partition         | Optional: dbpartitionnum value                       | ""        |
| db2_logstream         | Optional: logstream number                           | ""        |
| db2_options           | Optional: additional options for TSM                 | ""        |
| db2_compress          | Enable compression for backup                        | false     |
| db2_encrypt           | Enable encryption for backup                         | false     |
| db2_tsm_password      | TSM password                                         | ""        |
| db2_tsm_nodename      | TSM node name                                        | ""        |
| db2_tsm_owner         | Owner ID for TSM                                     | ""        |
| db2_without_prompting | Whether to disable prompting                         | false     |

### Backup-specific Variables
| Variable                        | Description                                      | Default   |
|---------------------------------|--------------------------------------------------|-----------|
| db2_backup_type                 | Backup type: INCREMENTAL, DELTA                  | ""        |
| db2_backup_online               | Perform online backup                            | false     |
| db2_backup_include_logs         | Include logs in backup                           | false     |
| db2_backup_exclude_logs         | Exclude logs in backup                           | false     |
| db2_backup_tablespace           | List of tablespaces to backup                    | []        |
| db2_backup_no_tablespace        | If true, NO TABLESPACE will be used              | false     |
| db2_backup_use_tsm              | Use TSM for backup                               | true      |
| db2_backup_open_sessions        | Number of open sessions for backup (0 = not set) | 0         |
| db2_backup_options              | Additional options string for backup             | ""        |
| db2_backup_buffers              | Number of buffers for backup                     | 0         |
| db2_backup_buffer_size          | Size of each buffer for backup                   | 0         |
| db2_backup_parallelism          | Parallelism value for backup                     | 0         |
| db2_backup_util_impact_priority | Utility impact priority: LOW, MEDIUM, HIGH       | ""        |
| db2_backup_without_prompting    | Suppress prompts during backup                   | false     |
| db2_backup_comprlib             | Compression library name                         | ""        |
| db2_backup_compropts            | Compression options string                       | ""        |
| db2_backup_encrlib              | Encryption library name                          | ""        |
| db2_backup_encropts             | Encryption options string                        | ""        |
| db2_backup_partition_on_type    | Partition ON (DBPARTITIONNUM or DBPARTITIONNUMS) | ""        |
| db2_backup_partition_on_all          | Use ALL keyword in partition ON clause      | false     |
| db2_backup_partition_on_range        | Partition ON clause range (e.g. "1 TO 4")   | ""        |
| db2_backup_partition_on_except       | Include EXCEPT clause in partition ON       | false     |
| db2_backup_partition_on_except_type  | EXCEPT (DBPARTITIONNUM or DBPARTITIONNUMS)  | ""        |
| db2_backup_partition_on_except_range | EXCEPT clause range (e.g. "2 TO 3")         | ""        |

### Restore-specific Variables
| Variable                            | Description                                  | Default   |
|-------------------------------------|----------------------------------------------|-----------|
| db2_restore_into                    | New database name for restore                | ""        |
| db2_restore_replace_existing        | Replace existing database during restore     | false     |
| db2_restore_without_rolling_forward | Skip rollforward after restore               | false     |
| db2_restore_online                  | Perform online restore                       | false     |
| db2_restore_tablespace_online       | Online restore for tablespace                | false     |
| db2_restore_history_file_online     | Online restore for history file              | false     |
| db2_restore_compression_lib_online  | Online restore with compression library      | false     |
| db2_restore_logs_online             | Online restore with logs                     | false     |
| db2_restore_incremental             | INCREMENTAL, AUTO, AUTOMATIC, ABORT          | ""        |
| db2_restore_use_tsm                 | Use TSM for restore                          | true      |
| db2_restore_open_sessions           | Number of open sessions for restore          | ""        |
| db2_restore_options                 | Additional options for restore               | ""        |
| db2_restore_taken_at                | Backup timestamp for restore (yyyymmddhhmmss)| ""        |
| db2_restore_to                      | Restore target path                          | ""        |
| db2_restore_dbpath                  | Restore database path                        | ""        |
| db2_restore_on_paths                | List of restore paths                        | []        |
| db2_restore_transport               | Use transport option for restore             | false     |
| db2_restore_stage_in                | Stage in option for restore                  | ""        |
| db2_restore_using_stogroup          | Use storage group for restore                | ""        |
| db2_restore_logtarget               | Logtarget option: DEFAULT, EXCLUDE, INCLUDE  | ""        |
| db2_restore_logtarget_force         | Add FORCE to logtarget                       | false     |
| db2_restore_newlogpath              | New log path for restore                     | ""        |
| db2_restore_buffers                 | Number of buffers for restore                | ""        |
| db2_restore_buffer_size             | Buffer size for restore                      | ""        |
| db2_restore_replace_history         | Replace history during restore               | false     |
| db2_restore_redirect                | Use redirect during restore                  | false     |
| db2_restore_generate_script         | Generate script during restore               | ""        |
| db2_restore_parallelism             | Parallelism for restore                      | ""        |
| db2_restore_comprlib                | Compression library for restore              | ""        |
| db2_restore_compropts               | Compression options for restore              | ""        |
| db2_restore_no_encrypt              | Do not encrypt during restore                | false     |
| db2_restore_encrypt                 | Enable encryption during restore             | false     |
| db2_restore_cipher                  | Cipher for encryption: AES, 3DES             | ""        |
| db2_restore_cipher_mode             | Cipher mode: CBC, etc.                       | ""        |
| db2_restore_key_length              | Key length for encryption: 128, 192, 256     | ""        |
| db2_restore_encrlib                 | Encryption library for restore               | ""        |
| db2_restore_encropts                | Encryption options for restore               | ""        |
| db2_restore_master_key_label        | Master key label for restore                 | ""        |
| db2_restore_continue                | Continue restore operation                   | false     |
| db2_restore_abort                   | Abort restore operation                      | false     |
| db2_restore_rebuild_all             | Restore rebuild option: "DATABASE" or "IMAGE"| ""        |
| db2_restore_rebuild_except          | Tablespace name to exclude from rebuild      | ""        |
| db2_restore_tablespace              | Specific tablespace to restore               | ""        |
| db2_restore_schema                  | Schema name for restore                      | ""        |

### Query-specific Variables
| Variable                     | Description                                            | Default   |
|------------------------------|--------------------------------------------------------|-----------|
| db2_query_type               | Query type: backup, log, tablespace, loadcopy          | ""        |
| db2_query_backup_level       | Backup level: full, incremental, delta, nonincremental | ""        |
| db2_query_show_inactive      | Show inactive backup images in query                   | false     |
| db2_query_logs_between_start | Start log sequence number for query                    | ""        |
| db2_query_logs_between_end   | End log sequence number for query                      | ""        |
| db2_query_verbose            | Enable verbose output for query                        | false     |
| db2_query_additional_options | Additional options for query                           | ""        |

### Delete-specific Variables
| Variable                     | Description                                      | Default        |
|------------------------------|--------------------------------------------------|----------------|
| db2_delete_type              | Type: FULL, INCREMENTAL, DELTA, TABLESPACE, etc. | ""             |
| db2_delete_tablespaces       | List of tablespaces to delete                    | []             |
| db2_delete_keep              | KEEP n backups for delete                        | ""             |
| db2_delete_older_than        | Delete backups older than this value             | ""             |
| db2_delete_taken_at          | Delete backups taken at this timestamp           | ""             |
| db2_delete_logs_between      | Delete logs between sequence numbers             | ""             |
| db2_delete_chain             | Delete chain number                              | ""             |
| db2_delete_options           | Additional options for delete command            | ""             |
| db2_delete_level             | Backup level: nonincremental, incremental, delta | nonincremental |
| db2_delete_filter_type       | Filter:  keep, older, older than, taken at       | older than     |
| db2_delete_filter_value      | Value for the above filter                       | 7 days         |
| db2_delete_logs_start        | Start log sequence number for delete             | ""             |
| db2_delete_logs_end          | End log sequence number for delete               | ""             |

---

## Environment Prerequisites

- DB2 instance environment profile must be sourced before running commands. This is handled internally, but ensure the DB2 environment is configured on the target node.
- TSM client must be installed and configured properly to communicate with your backup server.

---

## File Structure & Task Includes

| Task    | File                | Description                       |
|---------|---------------------|-----------------------------------|
| Backup  | dp_db2_backup.yml   | DB2 backup operation              |
| Restore | dp_db2_restore.yml  | DB2 restore operation             |
| Query   | dp_db2_query.yml    | Query backups using db2adutl      |
| Delete  | dp_db2_delete.yml   | Delete backups using db2adutl     |

The main playbook dispatches tasks based on the value of `db2_operation`.

---

## How it Works

1. Set the required variables in your playbook or inventory.
2. The role will include the appropriate task file based on `db2_operation`.
3. Each operation is performed using the correct DB2/TSM command, with output and errors shown for troubleshooting.

---

## Example Playbook

```yaml
- hosts: db2_servers
  vars:
    db2_operation: "backup"
    db2_database: "MYDB"
    db2_instance: "db2inst1"
    db2_user: "db2inst1"
    db2_password: "mypassword"
    db2_backup_type: "full"
    db2_backup_online: true
  roles:
    - dp_db2_manage
```

---

## Further Information
For the full list of variables and detailed descriptions, please refer to the `defaults/main.yml` file included in this role.

---

## License
MIT License

## Author
Karthik Kamepalli

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
| Variable         | Description                                           | Required? |
|------------------|-------------------------------------------------------|-----------|
| db2_operation    | Operation to perform (backup, restore, query, delete, extract) | Yes       |
| db2_database     | Name of the DB2 database                              | Yes       |
| db2_instance     | DB2 instance name                                     | Yes       |
| db2_user         | DB2 username for authentication                       | Optional  |
| db2_password     | Password for DB2 user                                 | Optional  |

### Backup-specific Variables (examples)
| Variable               | Description                                 | Default   |
|------------------------|---------------------------------------------|-----------|
| db2_backup_type        | Backup type: full, incremental, delta       | ""        |
| db2_backup_online      | Perform online backup (true/false)          | false     |
| db2_backup_include_logs| Include logs in backup                      | false     |
| db2_backup_tablespaces | List of tablespaces to backup (empty = all) | []        |

### Restore-specific Variables (examples)
| Variable                    | Description                          | Default   |
|-----------------------------|--------------------------------------|-----------|
| db2_restore_into            | New database name for restore        | ""        |
| db2_restore_replace_existing| Replace existing database            | false     |
| db2_restore_without_rollforward | Skip rollforward after restore   | false     |
| db2_restore_rollforward     | Perform rollforward after restore    | true      |

### Query-specific Variables (examples)
| Variable           | Description                               | Default   |
|--------------------|-------------------------------------------|-----------|
| db2_query_command  | db2adutl command (e.g., "LIST BACKUP")    | "QUERY"   |
| db2_query_database | Database name for db2adutl                | ""        |
| db2_query_verbose  | Enable verbose output                     | false     |

### Delete-specific Variables (examples)
| Variable             | Description                                                | Default   |
|----------------------|------------------------------------------------------------|-----------|
| db2_delete_type      | Type of delete: FULL, INCREMENTAL, DELTA, TABLESPACE, etc. | ""        |
| db2_delete_tablespaces | List of tablespaces to delete                            | []        |
| db2_delete_keep      | KEEP n backups                                             | ""        |

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

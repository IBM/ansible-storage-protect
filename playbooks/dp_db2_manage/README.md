# Playbooks: dp_db2_manage

This folder contains Ansible playbooks for managing DB2 database operations using the `dp_db2_manage` role and IBM Storage Protect (TSM).

## Playbook Overview

- **dp_db2_backup.yml**
  - Performs a DB2 database backup operation to IBM Storage Protect.
  - Supports full, incremental, and delta backups, with options for online/offline, compression, encryption, and parallelism.

- **dp_db2_restore.yml**
  - Restores a DB2 database from a backup stored in IBM Storage Protect.
  - Supports point-in-time and tablespace-level restore options.

- **dp_db2_query.yml**
  - Queries backup images and related metadata for a DB2 database in IBM Storage Protect.
  - Useful for listing available backups and their details.

- **dp_db2_delete.yml**
  - Deletes backup images for a DB2 database from IBM Storage Protect.
  - Useful for managing storage and retention policies.

## Usage
Each playbook is designed to be run independently, targeting the required DB2 operation. Refer to the role's README for variable details and prerequisites.

## Prerequisites
- DB2 and IBM Storage Protect client must be installed and configured on the target hosts.
- The `dp_db2_manage` role must be available in your Ansible roles path.

## See Also
- See the role's README for supported variables, environment setup, and advanced usage.

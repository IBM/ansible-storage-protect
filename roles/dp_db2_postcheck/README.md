# dp_db2_postcheck

## Overview
The `dp_db2_postcheck` Ansible role performs postchecks and configuration for DB2 integration with IBM Storage Protect. It ensures that the DB2 environment is properly configured and ready for use with IBM Storage Protect.

## Features
- Determines the DB2 bit level (`32` or `64`) using the `db2level` command.
- Validates and configures DSMI environment variables for DB2.
- Verifies the existence of required configuration files (`dsm.opt`, `dsm.sys`).
- Ensures proper permissions for DSMI log directories.
- Runs `dsmapipw` to set the password for IBM Storage Protect.
- Restarts the DB2 instance to apply changes.
- Provides detailed debug information for troubleshooting.

## Requirements
- **Ansible Version**: 2.15.0 or higher.
- **DB2 Instance**: Ensure that the DB2 instance is installed and running.
- **IBM Storage Protect Client**: Ensure that the IBM Storage Protect client is installed on the target host.

## Role Variables
The following variables can be configured in the `defaults/main.yml` file or passed as extra variables:

| Variable                  | Default Value | Description                                                                 |
|---------------------------|---------------|-----------------------------------------------------------------------------|
| `db2_instance_owner`      | `""`          | The user under which the DB2 instance runs. Must be overridden.            |
| `node_current_password`    | `""`          | The current password for the IBM Storage Protect API.                      |
| `node_new_password`        | `""`          | The new password to set for the IBM Storage Protect API.                   |
                                |

## Usage
### Example Playbook
```yaml
- name: Perform postchecks for DB2 integration with IBM Storage Protect
  hosts: db2_servers
  become: yes
  roles:
    - role: dp_db2_postcheck
      vars:
        db2_instance_owner: "db2inst1"
        node_current_password: "current_password"
        node_new_password: "new_password"
```

## Tasks Overview
The role performs the following tasks:

1. **Determine DB2 Bit Level**:
   - Runs the `db2level` command to determine if the DB2 instance is 32-bit or 64-bit.

2. **Validate DSMI Environment Variables**:
   - Checks if DSMI environment variables (`DSMI_DIR`, `DSMI_CONFIG`, `DSMI_LOG`) are set.
   - Configures default values if they are not set.

3. **Verify Configuration Files**:
   - Ensures that the `dsm.opt` and `dsm.sys` files exist in the appropriate directories.
   - Validates that the `servername` in `dsm.opt` matches the entry in `dsm.sys`.

4. **Run `dsmapipw` to Set Password**:
   - Uses the `dsmapipw` command to set the password for the IBM Storage Protect API.
   - Validates the output of the command to ensure no errors occurred.

5. **Restart the DB2 Instance**:
   - Stops and starts the DB2 instance to apply changes.

6. **Final Validation**:
   - Confirms that all checks passed and the DB2 instance is successfully configured with IBM Storage Protect.

### Example:
```yaml
- name: Perform postchecks with debug mode enabled
  hosts: db2_servers
  become: yes
  roles:
    - role: dp_db2_postcheck
      vars:
        db2_instance_owner: "db2inst1"
        debug_mode: true
```

## Notes
- Ensure that the `db2_instance_owner` user has the necessary permissions to run DB2 commands and access configuration files.
- Use Ansible Vault to securely store sensitive variables like `node_current_password` and `node_new_password`.

### Example:
Encrypt sensitive variables:
```bash
ansible-vault encrypt group_vars/db2_servers.yml
```

Run the playbook with the vault password:
```bash
ansible-playbook playbook.yml --ask-vault-pass
```
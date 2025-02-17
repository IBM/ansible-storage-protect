# ibm.storage_protect.sp_server_install

## Overview
This Ansible role automates the installation, upgrade, configuration, and uninstallation of IBM Storage Protect (SP) Server on remote hosts. It includes tasks for:
- Installing the SP Server.
- Upgrading the SP Server to a specified version.
- Configuring the SP Server.
- Uninstalling the SP Server and restoring the system to a clean state.

## Role Variables
The following variables can be configured in the `defaults/main.yml` file:

| Variable                     | Default Value                 | Description                                                                                                                           |
|------------------------------|-------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| `sp_server_state`            | `present`                     | Desired state of the SP Server (`present`, `upgrade`, `configure`, `absent`).                                                         |
| `sp_server_version`          | `8.1.23`                      | Version of the SP Server to install or upgrade to.                                                                                    |
| `install_location`           | `/opt/IBM/InstallationManager/eclipse` | Location where the SP Server will be installed.                                                                                       |
| `secure_port`                | `9443`                        | Secure port for SP Server.                                                                                                            |
| `ssl_password`               | `IBMSP@@123456789`            | Password for SSL encryption.                                                                                                          |
| `sp_server_install_dest`     | `/opt/sp_server_binary/`      | Destination directory for SP Server installation files.                                                                               |
| `sp_server_upgrade_dest`     | `/opt/sp_server_upgrade_binary` | Destination directory for upgrade binaries.                                                                                           |
| `repository_location`        | `{{ sp_server_temp_dest }}/repository` | Repository path for installation.                                                                                                     |
| `disk_device`                | `/dev/sdb`                    | Disk Device which will be mounted to the root directory of Storage Protect Server, which will contain all the log and db directories. |
| `root_dir`                   | `/tsmroot`                    | Root directory for SP Server.                                                                                                         |
| `sp_server_version`                | `8.1.23`                       | Version of SP Server to be installed.                                                                                                 |
| `sp_server_bin_repo`                | `""`                | Directory on control node which contains the binaries.                                                                                |
| `tsm_group`                | `tsmusers`       | Group of the user who owns SP Server instance.                                                                                        |
| `tsm_group_gid`                | `10001`        | Group Id                                                                                                                              |
| `tsm_user`                | `tsminst1`        | Specifies the name of the user who will own the SP Server Instance and also this value corresponds to the name of instance.           |
| `tsm_user_uid`                | `10001`        | User Id for `tsm_user`.                                                                                                               |
| `tsm_user_password`                | `password123`        | Password for `tsm_user`.                                                                                                              |
| `sp_server_db_directory`                | `tsmdb001`        | Specifies the name of the database directory for SP Server.                                                                           |


## Role Workflow
### When `sp_server_state` is `present`:
1. Validates system compatibility (architecture, disk space, etc.).
2. Checks if the specified version is available in the repository.
3. Determines the appropriate action based on the installed version:
   - If a higher version is available, it performs an upgrade.
   - If no version is installed, it proceeds with installation.
4. Installs the SP Server if the system meets the requirements.

### When `sp_server_state` is `upgrade`:
1. Checks the installed version and determines if an upgrade is necessary.
2. Performs the upgrade, ensuring existing configurations are retained.

### When `sp_server_state` is `configure`:
1. Executes configuration tasks for SP Server.

### When `sp_server_state` is `absent`:
1. Uninstalls the SP Server, and remove all associated packages and files.

## Key Tasks
### Installation
- Validates system compatibility.
- Transfer the required binaries on the target machines.
- Perform silent installation after executing the binaries.

### Upgrade
- Checks for the already installed version. If the specified version is greater than already existing version, performs upgrade using IBM Installation Manager.

### Uninstallation
- Stops SP Server processes.
- Deletes the instance of SP Server.
- Removes the instance directories and performs silent un-installtion.

## Example Playbooks
To install SP Server:
```bash
ansible-playbook -i inventory.ini playbooks/sp_server_install.yml --extra-vars '{"target_hosts": "group1", "sp_server_db_directory":"/path/to/repo/on/controlNode", "sp_server_state": "present", "sp_server_version": "8.1.23"}'
```

To upgrade SP Server:
```bash
ansible-playbook -i inventory.ini playbooks/sp_server_install.yml --extra-vars '{"target_hosts": "group1", "sp_server_db_directory":"/path/to/repo/on/controlNode", "sp_server_state": "upgrade", "sp_server_version": "8.1.24"}'
```

To configure SP Server:
```bash
ansible-playbook -i inventory.ini playbooks/sp_server_configure.yml --extra-vars '{"target_hosts": "group1", "sp_server_state": "configure"}'
```

To uninstall SP Server:
```bash
ansible-playbook -i inventory.ini playbooks/sp_server_uninstall.yml --extra-vars '{"target_hosts": "group1", "sp_server_state": "absent"}'
```

## Requirements
- **Operating System**: Linux (x86_64 architecture).
- **Disk Space**: Minimum 7500 MB free on the remote machine.
- The playbook should be executed with `become: true`.
- Ensure `ansible.posix.synchronize` module is installed for efficient file transfers:
```bash
ansible-galaxy collection install ansible.posix

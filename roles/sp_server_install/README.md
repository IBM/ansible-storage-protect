# ibm.storage_protect.sp_server_install

## Overview
This Ansible role automates the installation, upgrade, configuration, and uninstallation of IBM Storage Protect Server on remote hosts. It includes tasks for:
- Installing the SP Server.
- Upgrading the SP Server to a specified version.
- Configuring the SP Server.
- Uninstalling the SP Server and restoring the system to a clean state.

## Role Variables
The following variables can be configured in the `defaults/main.yml` file:

| Variable                     | Default Value                   | Description                                                                                                             |
|------------------------------|---------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| `sp_server_state`            | `present`                       | Desired state of the SP Server (`present`, `upgrade`, `absent`).                                               |
| `secure_port`                | `9443`                          | Secure port for SP Server.                                                                                              |
| `ssl_password`               | `""`                            | Password for SSL encryption.                                                                                            |
| `sp_server_install_dest`     | `/opt/sp_server_binary/`        | Destination directory for SP Server installation files.                                                                 |
| `sp_server_upgrade_dest`     | `/opt/sp_server_upgrade_binary` | Destination directory for upgrade binaries.                                                                             |
| `root_dir`                   | `/tsmroot`                      | Root directory for SP Server.                                                                                           |
| `sp_server_version`                | `""`                            | Version of SP Server to be installed.                                                                                   |
| `sp_server_bin_repo`                | `""`                            | Directory on control node which contains the binaries.                                                                  |
| `tsm_group`                | `tsmusers`                      | Group of the user who owns SP Server instance.                                                                          |
| `tsm_group_gid`                | `10001`                         | Group Id                                                                                                                |
| `tsm_user`                | `tsminst1`                      | Specifies the name of the user who will own the SP Server Instance and also this value corresponds to the name of instance. |
| `tsm_user_uid`                | `10001`                         | User Id for `tsm_user`.                                                                                                 |
| `tsm_user_password`                | `""`                            | Password for `tsm_user`.                                                                                                |
| `sp_server_db_directory`                | `tsmdb001`                      | Specifies the name of the database directory for SP Server.                                                             |
| `sp_server_active_log_size`                | `17000`                         | Specifies the active log size for SP Server                                                                             |

### Offerings dictionary can be used to install only required components. 
#### By default role install all the offerings.
```
offerings:
  server: true
  stagent: true
  devices: true
  oc: true
  ossm: true
```

## Role Workflow
### When `sp_server_state` is `present`:
1. Validates system compatibility (architecture, disk space, etc.).
2. Checks if the specified version is available in the repository on control node.
3. Determines the appropriate action based on the installed version:
   - If specified sp_server_version > already installed version, role performs upgrade of SP Server.
   - If no version is installed, it proceeds with installation.
4. Installs the SP Server if the system meets the requirements.
5. If Installation fails completely or for some components, the system is rolled-back to previous state and removes the components which were installed.
6. If Server is already installed and role is executed with state as `present`, then role will configure the server.

### When `sp_server_state` is `upgrade`:
1. Checks the installed version and determines if an upgrade is necessary.
2. Performs the upgrade, ensuring existing configurations are retained.

### When `sp_server_state` is `configure`:
1. Executes configuration tasks for SP Server.

### When `sp_server_state` is `absent`:
1. Stops the dsmserv processes.
2. Drops the db2 instance.
3. Uninstalls the SP Server, and remove's all related packages and instance directories.

## Example Playbooks
To install SP Server:
```bash
ansible-playbook -i inventory.ini playbooks/sp_server_install.yml --extra-vars '{"sp_server_bin_repo":"/path/to/repo/on/controlNode", "sp_server_state": "present", "sp_server_version": "8.1.23", "ssl_password": "YourPassword@123"}'
```

To upgrade SP Server:
```bash
ansible-playbook -i inventory.ini playbooks/sp_server_install.yml --extra-vars '{"sp_server_bin_repo":"/path/to/repo/on/controlNode", "sp_server_state": "upgrade", "sp_server_version": "8.1.24", "ssl_password": "YourPassword@123"}'
```

To configure SP Server:
```bash
ansible-playbook -i inventory.ini playbooks/sp_server_configure.yml
```

To uninstall SP Server:
```bash
ansible-playbook -i inventory.ini playbooks/sp_server_uninstall.yml --extra-vars '{"sp_server_state": "absent"}'
```

## Requirements
- **Operating System**: Linux (x86_64 architecture).
- **Disk Space**: Minimum 40000 MB free on the remote machine. Additional Memory will be required based on the value of `sp_server_active_log_size`.
- The playbook should be executed with `become: true`.
- Install the following collections from ansible galaxy on control node.
```bash
  ansible-galaxy collection install ansible.posix
  ansible-galaxy collection install community.general

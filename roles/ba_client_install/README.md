# ibm.storage_protect.ba_client_install

## Overview
This Ansible role manages the life cycle of BA Client on remote hosts. It includes tasks for:
- Installing the BA Client.
- Upgrading the BA Client to a specified version.
- Uninstalling the BA Client and restoring the system to a clean state.

## Role Variables
The following variables can be configured in the `defaults.yml` file:

| Variable                | Default Value             | Description                                                                                                                     |
|-------------------------|---------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `ba_client_state`       | `present`                 | Desired state of the BA Client (`present` or `absent`).                                                                         |
| `ba_client_version`     | `8.1.24.0`                | Version of the BA Client to install or upgrade to.                                                                              |
| `ba_client_tar_repo`    | `BA_CLIENT_TAR_REPO_PATH` | Set the environment variable which will point the directory containing `.tar` files for BA Client installation on control node. |
| `ba_client_extract_dest`| `/opt/baClient`           | Destination directory for extracted BA Client files.                                                                            |
| `ba_client_temp_dest`   | `/tmp/`                   | Temporary directory for transferring `.tar` files.                                                                              |
| `ba_client_start_daemon`   | `false`                   | Specify whether to start the daemon after the upgrade.                                                                          |

## Role Workflow
### General Workflow
- Before fresh installation, the system compatibility is validated. This includes checks for:
  - Architecture.
  - Disk space.

### When `ba_client_state` is `present`:
1. Validates whether the specified version is available in the local repository on the control node.
2. Determines the appropriate action based on the specified and installed versions:
   - If the specified version is greater than the installed version, the action is set to `upgrade`.
   - If the specified version is lower, the role execution is stopped.
   - If no version is installed, the action is set to `install`.
3. Collects system information for performing compatibility checks on remote VMs.
4. Executes the determined action:
   - Installs the BA Client if no version is installed and system is compatible.
   - Upgrades the BA Client if a newer version is specified.

### When `ba_client_state` is `absent`:
1. Uninstalls the BA Client.

### Additional Points:
- During an upgrade:
  - Configuration files (`opt` and `sys`) are backed up before the process.
  - After the upgrade, these configurations are restored.
- In case of an installation, upgrade, uninstall failure:
  - The system state is maintained to prevent inconsistencies.

## Key Tasks
### Installation
- Validates system compatibility (e.g., architecture, disk space).
- Transfers `.tar` files and extracts them on the remote host.
- Installs necessary packages in the correct dependency order.
- Rolls back to previous state if installation is failed.

### Upgrade
- Uninstalls the existing BA Client.
- Installs the new version.
- Restores configuration files after the upgrade.
- Rolls back to the previous version if the upgrade fails.

### Uninstallation
- Stops running BA Client processes.
- Backs up configuration files and installed RPMs.
- Removes the BA Client packages in dependency order.
- Rolls back to the previous version if the uninstall fails

## Example Playbooks
- The example playbooks are available in the playbooks directory of this collection.
- For installation of BA Client execute the 'ba_client_install.yml' playbook and pass the above mentioned variables as extra vars or define them in your inventory.
```bash
 anisble-playbook -i inventory.ini playbooks/ba_client/ba_client_install.yml --extra-vars '{"target_hosts": "group1", "ba_client_state": "present", "ba_client_version": "8.1.24.0", "ba_client_tar_repo": "/path/to/repo"}'
```
- For uninstallation of BA Client execute the 'ba_client_uninstall.yml' playbook.
```bash
 anisble-playbook -i inventory.ini playbooks/ba_client/ba_client_uninstall.yml --extra-vars '{"target_hosts": "group1"}'
```
- For upgrade of BA Client execute the 'ba_client_install.yml' playbook and make sure the greater version is passed as compared to already installed version.
```bash
 anisble-playbook -i inventory.ini playbooks/ba_client/ba_client_install.yml --extra-vars '{"target_hosts": "group1", "ba_client_state": "present", "ba_client_version": "8.1.25.0", "ba_client_tar_repo": "/path/to/repo"}'
```
- Note: The role also performs patching. The installation playbook is capable of applying patches—just pass the desired version, and the role will handle it. For example, if version 8.1.15.0 is already installed, passing 8.1.15.1 to the installation playbook will upgrade the BA Client to the patched version.
## Requirements
- **Operating System**: Linux with `x86_64` and `s390x` architecture.
- **Disk Space**: Minimum 1400 MB of free space on remote vm's.
- Make sure the playbook is executed with 'become' directive as true.
- Install the following collections from ansible galaxy on control node.
```bash
  ansible-galaxy collection install ansible.posix
  ansible-galaxy collection install community.general
```

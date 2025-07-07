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
- Example playbooks are available under the playbooks directory of [IBM/ansible-storage-protect](https://github.com/IBM/ansible-storage-protect/tree/main/playbooks/) github repo.
- The `target_hosts` variable allows you to dynamically specify the target hosts or host group at runtime.
- If `target_hosts` is not provided, the playbook defaults to using "all" hosts from your inventory.
Make sure the specified target_hosts exist in your inventory file (INI, YAML, or dynamic inventory).
- For installation of BA Client execute the 'ba_client_install_playbook.yml' included with the collection and pass the above mentioned variables as extra vars or create a seperate vars file in working directory.
- Execute the below command in working directory once ibm.storage_protect collection is installed.
```bash
 anisble-playbook -i inventory.ini ibm.storage_protect.ba_client_install_playbook.yml -e @your_vars_file.yml'
```
- For uninstallation of BA Client execute the 'ba_client_uninstall_playbook.yml' playbook.
```bash
 anisble-playbook -i inventory.ini ibm.storage_protect.ba_client_uninstall.yml'
```
- For upgrade of BA Client execute the 'ba_client_install_playbook.yml' playbook and make sure the greater version is passed as compared to already installed version.
```bash
 anisble-playbook -i inventory.ini ibm.storage_protect.ba_client_install.yml -e @your_vars_file.yml'
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

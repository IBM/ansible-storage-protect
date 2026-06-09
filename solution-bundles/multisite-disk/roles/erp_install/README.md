# ibm.storage_protect.erp_install

## Overview
This Ansible role manages the installation and configuration of SAP ERP for HANA on remote hosts. It includes tasks for:
- Installing the BA Client.
- Installing SAP ERP for hana.

## Role Variables
The following variables can be configured in the `configure.yml` file:

| Variable                | Default Value             | Description                                                                                                                     |
|-------------------------|---------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `sperp_language`        | `2`                       | Prefered language that is to be configured when SP ERP for HANA is installed                                                    |
| `hana_sid`              | `FR2`                     | Hana sid may vary depending upon the hana nodes configuration                                                                   |
| `hana_instance number`  | `00`                      | Instance number may vary depending upon the hana nodes configuration                                                            |
| `hana_db_role`          | `SYSTEM`                  | Database user with System Privileges, options: INIFILE ADMIN, CATALOG READ, SERVICE ADMIN and DATABASE ADMIN [SYSTEM]           |
| `ba_client_tar_repo`    | `BA_CLIENT_TAR_REPO_PATH` | Set the environment variable which will point the directory containing `.tar` files for BA Client installation on control node. |
| `erp_temp_dest`         | `/tmp/`                   | Temporary directory for transferring `.bin` files.                                                                              |
| `erp_bin_repo`          | `ERP_INSTALLER_REPO_PATH` | Set the environment variable which will point to the directory containing `.bin` file for erp installer

## Role Workflow
### General Workflow
- Before fresh installation, the system compatibility is validated. This includes checks for:
  - Architecture.
  - Disk space.
  - Utilities existence.

### Default behaviour:
1. Validates whether the specified version is available in the local repository on the control node.
2. Determines the appropriate action based whether SP ERP HANA is installed:
   - If the ERP is not installed, the action is set to `install`.
   - If the ERP is already installed, the playbook is stopped.
   - After ERP is installed, the action is set to `configure`. This is #WIP.
3. Collects system information for performing compatibility checks on remote VMs.
4. Executes the determined action:
   - Installs the BA Client (no versions should be installed previously) and system is compatible.

### Additional Points:
-This role currently supports BA client installation and does not support upgrading/Downgrading the client:
  - Configuration files w.r.t to supported architectures and utlities to verify are also available but are not recomended as the values are added as and and when tests for specific utilties/ architecture.

## Key Tasks
### Installation
- Validates system compatibility (e.g., architecture, disk space) twice, (as ba client and sp erp have different minimum requirements ).
- Transfers `.tar and .bin` files and extracts them on the remote host.
- Installs necessary packages in the correct dependency order.

## Example Playbooks
- The example playbooks are available in the playbooks directory of this collection.
- For installation of SP ERP for HANA execute the 'sperp_install_configure_hana.yml' playbook and pass the above mentioned variables as extra vars or define them in your inventory.
```bash
 anisble-playbook -i inventory.ini playbooks/ba_client/erp_install.yml --extra-vars '{"target_hosts": "group1", "ba_client_tar_repo": "/path/to/repo", "erp_bin_repo": "/path/to/repo"}'
```
- Having a node which does not have a ba client installed is essential for erp install to work, For uninstallation of BA Client execute the 'ba_client_uninstall.yml' playbook.
```bash
 anisble-playbook -i inventory.ini playbooks/ba_client/ba_client_uninstall.yml --extra-vars '{"target_hosts": "group1"}'
```

## Requirements
- **Operating System**: Linux with `ppc64le` architecture.
- **Disk Space**: Minimum 1400 MB of free space on remote vm's.
- make sure utilities like rsync, lsof are installed on target nodes.
- Make sure the playbook is executed with 'become' directive as true.
- Install the following collections from ansible galaxy on control node.


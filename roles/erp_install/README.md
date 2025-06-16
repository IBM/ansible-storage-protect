# ibm.storage_protect.erp_install

## Overview
This Ansible role manages the installation and configuration of SAP ERP for HANA on remote hosts. It includes tasks for:
- Installing the BA Client.
- Installing SAP ERP for hana.

## Role Variables
The following variables can be configured in the `configure.yml` file:

| Variable                | Default Value             | Description                                                                                                                     |
|-------------------------|---------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| `hana_sid`              | `00`                      | Hana sid may vary depending upon the hana nodes configuration                                                                   |
| `hana_instance number`  | `00`                      | Instance number may vary depending upon the hana nodes configuration                                                            |
| `hana_db_role`          | `SYSTEM`                  | Database user with System Privileges, options: INIFILE ADMIN, CATALOG READ, SERVICE ADMIN and DATABASE ADMIN [SYSTEM]           |
| `ba_client_tar_repo`    | `BA_CLIENT_TAR_REPO_PATH` | Set the environment variable which will point the directory containing `.tar` files for BA Client installation on control node. |
| `ba_client_extract_dest`| `/opt/baClient`           | Destination directory for extracted BA Client files.                                                                            |
| `ba_client_temp_dest`   | `/tmp/`                   | Temporary directory for transferring `.tar` files.                                                                              |

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
   - Installs the BA Client if no version is installed and system is compatible.

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
 anisble-playbook -i inventory.ini playbooks/ba_client/erp_install.yml --extra-vars '{"target_hosts": "group1", "ba_client_state": "present", "ba_client_version": "8.1.24.0", "ba_client_tar_repo": "/path/to/repo", "erp_tar_repo": "/path/to/repo"}'
```
- For uninstallation of BA Client execute the 'ba_client_uninstall.yml' playbook.
```bash
 anisble-playbook -i inventory.ini playbooks/ba_client/ba_client_uninstall.yml --extra-vars '{"target_hosts": "group1"}'
```
- For upgrade of BA Client execute the 'erp_install.yml' playbook and make sure the greater version is passed as compared to already installed version.
```bash
 anisble-playbook -i inventory.ini playbooks/ba_client/erp_install.yml --extra-vars '{"target_hosts": "group1", "ba_client_state": "present", "ba_client_version": "8.1.25.0", "ba_client_tar_repo": "/path/to/repo", "erp_tar_repo": "/path/to/repo"}'
```
- Note: The role also performs patching. The installation playbook is capable of applying patches—just pass the desired version, and the role will handle it. For example, if version 8.1.15.0 is already installed, passing 8.1.15.1 to the installation playbook will upgrade the BA Client to the patched version.
## Requirements
- **Operating System**: Linux with `x86_64` and `s390x` architecture.
- **Disk Space**: Minimum 1400 MB of free space on remote vm's.
- Make sure the playbook is executed with 'become' directive as true.
- Install the following collections from ansible galaxy on control node.

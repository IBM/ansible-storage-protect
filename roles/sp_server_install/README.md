# ibm.storage_protect.sp_server_install

## Overview
This Ansible role automates the installation, upgrade, configuration, and uninstallation of IBM Storage Protect Server on remote hosts. It includes tasks for:
- Installing the SP Server.
- Upgrading the SP Server to a specified version.
- Configuring the SP Server.
- Implements SP Server blueprint on Linux systems.
- Uninstalling the SP Server and restoring the system to a clean state.

## Role Variables
The following variables can be configured in the `defaults/main.yml` file:

| Variable                     | Default Value                   | Description                                                                                                                 |
|------------------------------|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| `sp_server_state`            | `present`                       | Desired state of the SP Server (`present`, `upgrade`, `absent`).                                                            |
| `secure_port`                | `9443`                          | Secure port for SP Server.                                                                                                  |
| `ssl_password`               | `""`                            | Password for SSL encryption. Include symbols, uppercase,lowercase and numbers in your password.                             |
| `sp_server_install_dest`     | `/opt/sp_server_binary/`        | Destination directory for SP Server installation files.                                                                     |
| `sp_server_upgrade_dest`     | `/opt/sp_server_upgrade_binary` | Destination directory for upgrade binaries.                                                                                 |
| `root_dir`                   | `/tsmroot`                      | Root directory for SP Server.                                                                                               |
| `sp_server_version`                | `""`                            | Version of SP Server to be installed.                                                                                       |
| `sp_server_bin_repo`                | `""`                            | Directory on control node which contains the binaries.                                                                      |
| `tsm_group`                | `tsmusers`                      | Group of the user who owns SP Server instance.                                                                              |
| `tsm_group_gid`                | `10001`                         | Group Id                                                                                                                    |
| `tsm_user`                | `tsminst1`                      | Specifies the name of the user who will own the SP Server Instance and also this value corresponds to the name of instance. |
| `tsm_user_uid`                | `10001`                         | User Id for `tsm_user`.                                                                                                     |
| `tsm_user_password`                | `""`                            | Password for `tsm_user`.                                                                                                    |
| `admin_name`                | `"tsmuser1"`                    | Initial system level administrator.                                                                                         |
| `admin_password`                | `"tsmuser1@@123456789"`                            | Password for Initial system level administrator.                                                                            |
| `sp_server_active_log_size`                | `17000`                         | Specifies the active log size for SP Server.                                                                                |
| `server_blueprint`                | `false`                         | Specifies whether to configure server according to blueprint configurations.                                                |

### Offerings dictionary can be used to install only required components. 
#### By default role install all the offerings. Override the below dictionary in your playbook to install only required components.
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
6. If Server is already installed and role is executed with state as `present`, then role will `configure` the server.
7. Two types of configuration can be achieved
   1. If `server_blueprint` is set to `true` and `server_size` is specified, role implements the blueprint. Refer the `Server Blueprint Implementation` section for detailed info.
   2. If `server_blueprint` is set to `false` (default value), it just configures the server and does not create the policy domains, storage pools, management classes, schedules related to client and db backup. Useful when just needed a server where clients can be registered for testing purpose.

### When `sp_server_state` is `upgrade`:
1. Checks the installed version and determines if an upgrade is necessary.
2. Performs the upgrade, ensuring existing configurations are retained.

### When `sp_server_state` is `absent`:
1. Stops the dsmserv processes.
2. Drops the db2 instance.
3. If `server_blueprint` is set to true, during cleanup role internally calls the `ibm.storage_protect.storage_prepare` role to remove the configuration. Set this value to true only if the server was configured  with `server_blueprint` directive as true.
4. Uninstalls the SP Server, and remove's all related packages and instance directories.


## SP Server Blueprint Specific Variables
| Variable                     | Default Value                | Description                                                                                                   |
|------------------------------|------------------------------|---------------------------------------------------------------------------------------------------------------|
| `dbbk_password`            | `YourDBkPassword@@123456789` | Specifies the password that is used to protect the database backups.                                          |
| `server_name`                | `Server1`                    | Set the server name for server 2 server communication.                                                        |
| `server_password`               | `IBMSPServer@@123456789`     | Specifies a password for the server. Include symbols uppercase,lowercase and numbers in your password.        |
| `server_size`               | `xsmall`                     | Specifies the size of server to be deployed.                                                                  |
| `maxcap`               | `100G`                       | Specifies the maximum size of any data storage files that are defined to a storage pool in this device class. |
| `dbbk_streams`               | `4`                          | Specifies the number of parallel data movement streams to use when you back up the database.                                                                                                              |
| `dbbk_compress`               | `YES`                        | Specifies whether volumes are compressed during database backup processing.                                                                  |


```yml
act_log_size:
  xsmall: 24576
  small: 131072
  medium: 131072
  large: 524032
```

```yml
# The MAXSESSIONS specifies the maximum number of simultaneous client sessions that can connect with the server.
max_sessions:
  xsmall: 75
  small: 250
  medium: 500
  large: 1000
```
## Server Blueprint Implementation:
1. To implement the server blueprint, set the `server_blueprint` directive to true.
2. Based on the value of `server_size`, role will configure the server with parameters as specified in the blueprint document.
3. Role also creates required policy domains, schedules, management classes and db backup related schedules. Refer the blueprint document for detailed information.
4. It is required to explicitly use `ibm.storage_protect.storage_prepare` role to configure the storage for required size before implementing the blueprint. It uses some facts which are set by `storage_prepare` role.See the documentation of `ibm.storage_protect.storage_prepare` role for detailed information.
5. As of now, role just creates the schedules for `IBM Spectrum Protect backup- archive client`.
6. Schedules related to other clients will be added in next releases.

## Example Playbooks
Example playbooks are available under the playbooks directory of [ibm-storage-protect](https://github.com/IBM/ansible-storage-protect/tree/main/playbooks/sp_server_install) github repo.

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

#### Example playbook for server blueprint implementation is available on the github repo of [IBM/ansible-storage-protect](https://github.com/IBM/ansible-storage-protect/tree/main/playbooks/sp_server_blueprint). 

## Requirements
- **Operating System**: Linux (x86_64 architecture).
- **Disk Space**: Minimum 40000 MB free on the remote machine. Additional Memory will be required based on the value of `sp_server_active_log_size`.
- The playbook should be executed with `become: true`.
- Install the following collections from ansible galaxy on control node.
```bash
  ansible-galaxy collection install ansible.posix
  ansible-galaxy collection install community.general

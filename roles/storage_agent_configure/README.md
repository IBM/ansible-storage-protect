# ibm.storage_protect.storage_agent_config
## Overview
This Ansible role configures the IBM Storage Protect Storage Agent on remote hosts.
## Role Variables
The following variables can be configured:

| Variable                    | Default Value |   | Description                                                                                                                                                                                                                                                                                    |
|-----------------------------|---------------|---|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `stg_agent_name`            | `''`          |   | Name of the Storage Agent defined on the server.                                                                                                                                                                                                                                               |
| `stg_agent_server_name`     | `''`          |   | Name of the server where the Storage Agent is defined.                                                                                                                                                                                                                                         |
| `stg_agent_password`        | `''`          |   | Password for the Storage Agent.                                                                                                                                                                                                                                                                |
| `stg_agent_hl_add`          | `''`          |   | High-level address where the client and storage agent are installed.                                                                                                                                                                                                                           |
| `lladdress`                 | `''`          |   | Port on which the server listens for LAN-Free communication.                                                                                                                                                                                                                                   |
| `server_tcp_port`           | `''`          |   | Port used for TCP/IP communication with the server.                                                                                                                                                                                                                                            |
| `server_hl_address`         | `''`          |   | High-level address of the Storage Protect server.                                                                                                                                                                                                                                              |
| `server_password`           | `''`          |   | Password for enabling server-to-server communication.                                                                                                                                                                                                                                          |
| `stg_agent_path_name`       | `''`          |   | Name assigned to the SCSI path on the server (e.g. `drv1`).                                                                                                                                                                                                                                    |
| `stg_agent_path_dest`       | `''`          |   | Destination type for the SCSI path (`drive` or `library`).                                                                                                                                                                                                                                     |
| `library`                   | `''`          |   | Name of the tape library defined on the server.                                                                                                                                                                                                                                                |
| `device`                    | `''`          |   | Device path on the Storage Agent host (e.g. `/dev/sg0`).                                                                                                                                                                                                                                       |
| `copygroup_domain`          | `''`          |   | Policy domain for the LAN-Free copy group.                                                                                                                                                                                                                                                     |
| `copygroup_policyset`       | `''`          |   | Policy set within the domain (e.g. `STANDARD`).                                                                                                                                                                                                                                                |
| `copygroup_mngclass`        | `''`          |   | Management class for LAN-Free backup.                                                                                                                                                                                                                                                          |
| `copygroup_destination`     | `''`          |   | Storage pool name for LAN-Free backups.                                                                                                                                                                                                                                                        |
| `validate_lan_free`         | `false`       |   | If `true`, runs the `VALIDATE LANFREE` command to verify configuration.                                                                                                                                                                                                                        |
| `node_name`                 | `''`          |   | Client node name registered for LAN-Free backup.                                                                                                                                                                                                                                               |
| `stg_pool`                  | `''`          |   | TSM server storage pool used for LAN-Free backups.                                                                                                                                                                                                                                             |
| `max_attempts`                  | 3             |   | Specifies the maximum number of times the module will retry the “validate lanfree” command.<br/>Storage Agent process can take several seconds to become fully available, each retry is spaced by the configured delay to ensure the agent has time to connect before the final validation attempt. |

## Note
1. All the variables are required while configuring the Storage Agent.
2. Only `node_name`,`stg_agent_name`,`validate_lan_free` are required for validation.

## Role Workflow
### Configuration
1. Define Storage agent on Server
2. Establish server to server communication by defining the servername, serverhladdress, serverlladdress and serverpassword on SP server using dsmadmc commands.
3. Configure SCSI paths for the storage agent on server
4. Configures the client and storage agent to communicate with SP server using 'setstorageserver' command.
4. Updates the `dsmsta.opt` and `dsm.sys` configuration files.
5. (Optional) Validate LAN-Free setup using `VALIDATE LANFREE`.

### Validation Mode
- If `validate_lan_free` is `true`, the role only runs a validation to check the LAN-Free configuration and does not make any configuration changes. Make sure while configuring the storage agent , `validate_lan_free` is `false`.

### Prerequisites on target nodes
1. BA client should be installed and configured to communicate with SP server. (Use ibm.storage_agent.ba_client_install)
2. Storage agent should be installed. (Use ibm.storage_agent.sp_server_install)
3. Refer the documentation of respective roles for detailed information. Sample playbooks are available in playbooks section/directory.
4. A lanfree capable storage pool should be created on the server, required for `stg_pool` directive of module.

## Example Playbook

For full, working examples of how to consume this role, see the **Playbooks** section:

[View Example Playbooks](https://galaxy.ansible.com/ui/repo/published/ibm/storage_protect/content/playbook/storage_agent_configure.yml/)

Below is a minimal inline example:
```yaml
---
- name: Storage agent config
  hosts: all
  become: yes
  environment:
    STORAGE_PROTECT_SERVERNAME: "server2"
    STORAGE_PROTECT_USERNAME: "tsmuser1"
    STORAGE_PROTECT_PASSWORD: "tsmuser1@@123456789"
  tasks:
    - name: Configure client
      ibm.storage_protect.storage_agent_config:
        stg_agent_name: "stgagent8"
        stg_agent_password: "STGAGENT@123456789"
        stg_agent_server_name: "server2"
        stg_agent_hl_add: "client_address"
        ... other parameters ...

    - name: Validate lanfree
      ibm.storage_protect.storage_agent_config:
        validate_lan_free: true
        node_name: "lanfreeclient"
        stg_agent_name: "stgagent8"
        max_attempts: 4

# Ansible Role: sp_server_facts

This Ansible role is designed to retrieve the facts of a Storage Protect Server (SP) by executing `dsmadmc` commands and gathering various server details. The role fetches data about the server's status, monitoring settings, storage pools, device classes, and other relevant information. The facts gathered are then displayed using Ansible's `debug` module.

## Requirements

- Ansible 2.9+ (to use the required features)
- A running Storage Protect Server (SP) that supports the `dsmadmc` commands.
- Access credentials for the Storage Protect Server (username, password).
- Inventory file containing the server details (`server_name`, `DSAMDMC Username`, `DSMADMC Password`).

## Role Variables

You can define the following variables in your **inventory file**:

- `ansible_host`: The IP address of the VM where the Storage Protect Server (SP) is installed
- `ansible_user`: The name of the root user for remote host.
- `ansible_password`: The password of the root user for remote host.
- `server_name`: The name or IP address of the Storage Protect Server (SP).
- `dsm_user`: The username for authenticating with the DSMADMC.
- `password`: The password for authenticating with the DSMADMC.

### Example Inventory File (`inventory.ini`):

```ini
[local]
servername ansible_host=host_ip ansible_connection=ssh ansible_user=root ansible_password=host_password server_name=server_name username=dsmadmc_username password=dsmadmc_password

```
## Playbook Examples

### Standard Role Usage

```yaml
---
- name: Get the Storage Protect Server Facts
  sp_server_facts:
    server_name: "{{ server_name }}"
    username: "{{ dsm_user }}"
    password: "{{ dsm_pass }}"
    q_status: true
    q_monitorsettings: true
    q_db: false
    q_dbspace: true
    q_log: false
    q_domain: true
    q_copygroup: true
    q_replrule: false
    q_devclass: true
    q_mgmtclass: true
    q_stgpool: true
  register: result

- name: Display output
  debug:
    var: result

```


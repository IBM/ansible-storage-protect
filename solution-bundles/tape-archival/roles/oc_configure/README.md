# ibm.storage_protect.oc_configure

## Overview
An Ansible role to configure, restart, or stop IBM Storage Protect Operations Center.

## Requirements
1. Client should be installed and registered with the server.

## Environment Variables
Before running the playbook, set the following environment variables in your terminal:
```bash
export STORAGE_PROTECT_SERVERNAME="your_server_name"
export STORAGE_PROTECT_USERNAME="your_username"
export STORAGE_PROTECT_PASSWORD="your_password"
```

## Role Variables

| Variable     | Default | Description                                          |
|--------------|---------|------------------------------------------------------|
| `admin_name` | ""      | OC admin username (Required, if action == configure) |
| `action`     | restart | Action to perform (configure, restart, stop)         |

## Example Playbook
- Example playbooks are available under the playbooks directory of [IBM/ansible-storage-protect](https://github.com/IBM/ansible-storage-protect/tree/main/playbooks/) github repo.
- The `target_hosts` variable allows you to dynamically specify the target hosts or host group at runtime.
- If `target_hosts` is not provided, the playbook defaults to using "all" hosts from your inventory.
Make sure the specified target_hosts exist in your inventory file (INI, YAML, or dynamic inventory).
- To configure oc, execute the `oc_configure_playbook.yml` included with the collection.
- Create a seperate vars file in working directory and provide the required variables.
- Execute the playbook using below command.
```bash
ansible-playbook -i inventory.ini ibm.storage_protect.oc_configure_playbook.yml -e @your_vars_file.yml
```
- To stop the OC, execute the playbook using below command.
```
ansible-playbook -i inventory.ini ibm.storage_protect.oc_configure_playbook.yml -e 'action=stop'
```
- To restart the OC, execute the playbook using below command.
```
ansible-playbook -i inventory.ini ibm.storage_protect.oc_configure_playbook.yml -e 'action=restart'
```

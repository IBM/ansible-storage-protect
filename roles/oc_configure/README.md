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

```yaml
---
- name: Configure OC
  hosts: localhost
  become: yes
  roles:
    - role: oc_configure
      vars:
        admin_name: tsmadmin
        action: configure

- name: Stop OC
  hosts: localhost
  become: yes
  roles:
    - role: oc_configure
      vars:
        action: stop

- name: Configure OC
  hosts: localhost
  become: yes
  roles:
    - role: oc_configure
      vars:
        action: restart
```

# Sample playbook is available in playbooks directory of ibm/storage_protect github repo
```bash
ansible-playbook playbooks/oc_configure/oc_configure.yml -e "target_hosts=host_group action=configure admin_name=tsmuser1"
```

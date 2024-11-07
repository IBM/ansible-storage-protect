# ibm.storage_protect

## Description

NOTE: This collection is under development

This collection provides a series of Ansible modules and plugins for interacting with the IBM Storage Protect product. For more information regarding this product, see [IBM Documentation](https://ibm.com/docs/en).


## Requirements

This collection requires the `dsmadmc` CLI to be installed on the target host.


## Installation

Before using this collection, you need to install it with the Ansible Galaxy command-line tool:

```
ansible-galaxy collection install ibm.storage_protect
```

You can also include it in a requirements.yml file and install it with ansible-galaxy collection install -r requirements.yml, using the format:


```yaml
collections:
  - name: ibm.storage_protect
```

Note that if you install any collections from Ansible Galaxy, they will not be upgraded automatically when you upgrade the Ansible package.
To upgrade the collection to the latest available version, run the following command:

```
ansible-galaxy collection install ibm.storage_protect --upgrade
```

You can also install a specific version of the collection, for example, if you need to downgrade when something is broken in the latest version (please report an issue in this repository). Use the following syntax to install version 1.0.0:

```
ansible-galaxy collection install ibm.storage_protect:==1.0.0
```

See [using Ansible collections](https://docs.ansible.com/ansible/devel/user_guide/collections_using.html) for more details.

## Use Cases

### Preparing the dsmadmc connection

The dsmadmc CLI requires a `dsm.sys` file to be created to be able to point at IBM Storage Protect instance. The `dsm_sysfile` module exists to prepare this file in readiness for runing modules if this file has not already been creaed. You can use the following example code:

```
- name: Create dsm.sys
  ibm.storage_protect.dsm_sysfile:
    server_name: "ibmsp01"
    tcp_server_address: "10.10.10.10"
```

### Managing resources in IBM Storage Protect

Most of the modules in this collection exist to add, update or remove resources on the IBM Storage Protect instance. An example is adding (registering) a node. The following task will do this:

```
- name: Register hosts
  ibm.storage_protect.node:
    node: ibmsp01
    policy_domain: STANDARD
    schedules:
      - my_sched
    node_password: P@ssword123456789
    session_security: strict
    node_password_expiry: 90
    can_archive_delete: true
    min_extent_size: 250
    state: present
    server_name: "{{ ibmsp_host }}"
    username: "{{ ibmsp_username }}"
    password: "{{ ibmsp_password }}"
```

## Testing

Tests should be defined in the `tests` repository of this collection. Here test playbooks should be created which can be run against an instance to ensure the modules are working correctly.


## License Information
Apache License, Version 2.0

See [LICENSE](LICENSE) to see the full text.
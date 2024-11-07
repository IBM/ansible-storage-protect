# ibm.storage_protect

## Description

NOTE: This collection is under development

This collection provides a series of Ansible modules and plugins to help automate the deployment and configuration of a Storage Protect landscape comprising of multiple Storage Protect servers and clients. It can be used to automate perform simple [data protection operations](https://www.ibm.com/docs/en/storage-protect/8.1.24?topic=overview-data-protection-services) such as backup / restore, archive / retrieve - of the data or workloads supported by the IBM Storage Protect product. You can also automate the overall data protection governance for the enterprise, using policy-based data management. For more information regarding this product, see [IBM Documentation](https://ibm.com/docs/en).


## Requirements

### Ansible version compatibility

This collection has been tested against following Ansible versions: >=2.15.0.

### Python

Collection supports 3.9+

### IBM Storage Protect

This collection supports IBM Storage Protect versions >= 8.1.23.
The Storage Protect Client (including dsmadmc CLI) must be pre-installed in the target client-node.
Refer to [IBM documentation](https://www.ibm.com/docs/en/storage-protect/8.1.24?topic=windows-install-unix-linux-backup-archive-clients) for more details

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

### Preparing Storage Protect client system-option file

- The client-system options file (dsm.sys) configures the Storage Protect client (and dsmadmc CLI) with the Storage Protect server details and the communication methods.
- Refer to https://www.ibm.com/docs/en/storage-protect/8.1.24?topic=overview-creating-modifying-client-system-options-file for more details.

You can use the following example code:

```
- name: Create dsm.sys
  ibm.storage_protect.dsm_sysfile:
    server_name: "ibmsp01"
    tcp_server_address: "10.10.10.10"
```

### Setting up the Storage Protect landscape

The modules in this collection are used to setup a Storage Protect landscape comprising of multiple Storage Protect server instance and multiple Storage Protect client nodes. Here is an example of adding or registering an existing client node, to an existing Storage Protect server instance.

The following task will do this:

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

The `tests` directory contains configuration for running sanity and integration tests using ansible-test.


## License Information
Apache License, Version 2.0

See [LICENSE](LICENSE) to see the full text.
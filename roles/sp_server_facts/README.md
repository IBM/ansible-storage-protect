# Ansible Role: sp_server_facts

This Ansible role is designed to retrieve the facts of a Storage Protect Server (SP) by using the `sp_server_facts` module. It gathers server information such as status, monitoring settings, storage pools, device classes, and other details. The facts collected are then displayed using Ansible's `debug` module.

## Requirements

- Ansible 2.9+ (to use the required features).
- The `sp_server_facts` module must be installed and accessible.
- Access to a running Storage Protect Server (SP) with appropriate credentials.

## Environment Variables

Before running the playbook, set the following environment variables in your terminal:

```bash
export STORAGE_PROTECT_SERVERNAME="your_server_name"
export STORAGE_PROTECT_USERNAME="your_username"
export STORAGE_PROTECT_PASSWORD="your_password"
```
## Role Variables

### Fact Collection Configuration

You can control which facts to collect using the `sp_server_facts_flags` variable. Set the corresponding keys to `true` or `false` to enable or disable specific fact collection:

| Key                | Description                            | Default  |
|--------------------|----------------------------------------|----------|
| `q_status`         | Collect server status information     | `false`  |
| `q_monitorsettings`| Collect monitor settings information  | `false`  |
| `q_db`             | Collect database information          | `false`  |
| `q_dbspace`        | Collect database space information    | `false`  |
| `q_log`            | Collect log information               | `false`  |
| `q_domain`         | Collect domain information            | `false`  |
| `q_copygroup`      | Collect copy group information        | `false`  |
| `q_replrule`       | Collect replication rule information  | `false`  |
| `q_devclass`       | Collect device class information      | `false`  |
| `q_mgmtclass`      | Collect management class information  | `false`  |
| `q_stgpool`        | Collect storage pool information      | `false`  |

### Example Playbooks
- Example playbooks are available under the playbooks directory of [IBM/ansible-storage-protect](https://github.com/IBM/ansible-storage-protect/tree/main/playbooks/) github repo.
- The `target_hosts` variable allows you to dynamically specify the target hosts or host group at runtime.
- If `target_hosts` is not provided, the playbook defaults to using "all" hosts from your inventory.
Make sure the specified target_hosts exist in your inventory file (INI, YAML, or dynamic inventory).
- To fetch the facts execute 'sp_server_facts_playbook' included with the collection.
- Create a vars file in working directory and execute below command.
```bash
 ansible-playbook -i inventory.ini ibm.storage_protect.sp_server_facts_playbook.yml -e @your_vars_file.yml
```
#### Example vars file
```bash
# vars.yml
sp_server_facts_flags:
  q_status: true
  q_monitorsettings: true
  q_db: true
  q_dbspace: true
  q_log: true
  q_domain: true
  q_copygroup: true
  q_replrule: true
  q_devclass: true
  q_mgmtclass: true
  q_stgpool: true
```

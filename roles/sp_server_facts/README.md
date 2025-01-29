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
- The example playbooks are available in the playbooks directory of this collection.
- To fetch the facts using 'sp_server_facts' module, execute the 'sp_server_facts' playbook from the playbooks directory and define variables mentioned above in your inventory or pass them as extra vars.
```bash
 ansible-playbook -i inventory.ini playbooks/sp_server_facts/sp_server_facts.yml --extra-vars 'target_hosts=group1 sp_server_facts_flags={"q_status": true}' 
```
- If the number of variables is large, create a separate vars file and pass the vars file as --extra-vars to the command.
```bash
# vars.yml
target_hosts: group1
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

```bash
ansible-playbook -i inventory.ini playbooks/sp_server_facts/sp_server_facts.yml --extra-vars "@vars.yml"
```

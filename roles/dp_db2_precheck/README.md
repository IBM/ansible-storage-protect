# dp_db2_precheck

This Ansible role performs prechecks for DB2 installation and configuration on remote hosts.

## Features
- Verifies if DB2 is installed by checking DB2 processes and binaries.
- Captures DB2 version and bit-level information using the `db2level` command.
- Provides recommendations based on the DB2 bit-level (32-bit or 64-bit).

## Variables

| Variable              | Default Value   | Required | Description                                              |
|-----------------------|-----------------|----------|----------------------------------------------------------|
| `db2_instance_owner`  | `db2inst1`      | Yes      | The user under which the DB2 instance runs.              |

## Usage

### Example Playbooks
- To perform DB2 prechecks, execute the playbook and define the required variables in your inventory or pass them as extra vars.

#### Example Command:
```bash
ansible-playbook -i inventory.ini playbooks/db2_precheck.yml --extra-vars 'db2_instance_owner=db2inst1'
```

#### Example Playbook:
```yaml
---
- name: Run DB2 Prechecks
  hosts: db2_servers
  become: true
  roles:
    - role: dp_db2_precheck
      vars:
        db2_instance_owner: "db2inst1"
```

- If the number of variables is large, create a separate vars file and pass the vars file as `--extra-vars` to the command.

#### Example Vars File (`vars.yml`):
```yaml
db2_instance_owner: "db2inst1"
```

#### Command Using Vars File:
```bash
ansible-playbook -i inventory.ini playbooks/db2_precheck.yml --extra-vars "@vars.yml"
```

## Tags
This role includes the following tags for selective execution:
- `db2_install_check`: Checks if DB2 is installed.
- `db2_version_check`: Captures DB2 version and bit-level information.
- `db2_recommendation`: Provides recommendations based on DB2 bit-level.

## License
This role is licensed under the MIT License.

## Author
Kartik Kamepalli
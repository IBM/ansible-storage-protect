# ibm.storage_protect.schedules

## Description
An Ansible Role to manage schedules in IBM Storage Protect, supporting creation, updates, and removal.

## Requirements
- Ansible 2.9+
- IBM Storage Protect server configured and accessible.

## Variables

| Variable Name                         | Default Value        | Required | Description                              |
|--------------------------------------|----------------------|----------|------------------------------------------|
| `storage_protect_state`              | `present`            | no       | Desired state of schedules.              |
| `storage_protect_server_name`        | `""`                | yes      | IBM Storage Protect Server URL.         |
| `storage_protect_username`           | `""`                | no       | Admin username.                          |
| `storage_protect_password`           | `""`                | no       | Admin password.                          |
| `storage_protect_request_timeout`    | `10`                | no       | Request timeout in seconds.             |
| `storage_protect_schedules`          | `see example below` | yes      | Data structure defining schedules.      |

### Secure Logging Variables

| Variable Name                        | Default Value | Required | Description                                           |
|--------------------------------------|----------------|----------|------------------------------------------------------|
| `storage_protect_schedules_secure_logging` | `False`        | no       | Enable secure logging for sensitive schedule data.   |

### Asynchronous Execution Variables

| Variable Name                         | Default Value | Required | Description                              |
|--------------------------------------|----------------|----------|------------------------------------------|
| `storage_protect_schedules_async_retries` | `30`         | no       | Number of retries for async tasks.      |
| `storage_protect_schedules_async_delay`   | `1`          | no       | Delay between async retries (seconds).  |

## Data Structure

### Schedule Variables

| Variable Name   | Required | Type   | Description                       |
|----------------|----------|--------|-----------------------------------|
| `policy_domain`| yes      | str    | Name of the policy domain.        |
| `name`         | yes      | str    | Name of the schedule.             |
| `description`  | no       | str    | Schedule description.             |
| `action`       | no       | str    | Action performed by the schedule. |
| `state`        | no       | str    | Desired schedule state.           |

### Example Data Structure

```yaml
storage_protect_schedules:
  - policy_domain: "DEFAULT"
    name: "Backup_Schedule"
    description: "Daily Backup"
    action: "backup"
    state: "present"
```

## Playbook Examples

### Basic Role Usage

```yaml
- name: Manage Storage Protect Schedules
  hosts: localhost
  vars_files:
    - vars/schedules.yml
  vars:
    storage_protect_server_name: "SPServer01"
    storage_protect_username: "admin"
    storage_protect_password: "SecurePass123"
  roles:
    - { role: ibm.storage_protect.schedule, when: storage_protect_schedules is defined }
```

## License Information
Apache License, Version 2.0

See [LICENSE](LICENSE) for the full license text.

## Author
[Subhajit Patra](https://github.com/yourusername)


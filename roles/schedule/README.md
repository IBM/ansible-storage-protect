# IBM Storage Protect Schedule Role

## Description
This Ansible role defines an IBM Storage Protect schedule using the custom module `ibm_storage_protect_schedule`.

## Requirements
- Ansible >= 2.9
- IBM Storage Protect CLI tool (`dsmadmc`) must be installed and configured.

## Role Variables

### Defaults (`defaults/main.yml`)
See `defaults/main.yml` for a complete list of supported variables.

### Example Playbook
```yaml
- name: "Define IBM Storage Protect Schedule"
  hosts: localhost
  roles:
    - role: ibm_storage_protect_schedule
      vars:
        domain_name: "BackupDomain"
        schedule_name: "MonthlyFullBackup"
        action: "Incremental"
        start_date: "2024-12-15"
        start_time: "01:00"
        duration: 5
        dur_units: "Hours"
        month: "December"
        day_of_week: "Sunday"
        expiration: "Never"
# ibm.storage_protect.dsm_opt

This Ansible role generates a `dsm.opt` configuration file for IBM Storage Protect clients.

## Features
- Dynamically generates the `dsm.opt` file
- Handles `present` and `absent` states for file creation and deletion.
- Automatic Value Mapping**: Reads an existing `dsm.opt` file and automatically maps the existing values.

## Variables

| Variable              | Default Value   | Required | Description             |
|-----------------------|-----------------|----------|-------------------------|
| `dsm_opt_servername`          | `""`           | No       | Server name defined in dsm.sys |
| `dsm_opt_nodename`            | `""`           | No       | Node name of the client |
| `dsm_opt_password`            | `""`           | No       | Specifies the password you use to log on to the IBM Storage Protect server.                       |
| `dsm_opt_domain`              | `""`             | No       | Directories or file systems to back up |
| `dsm_opt_optfile_path`        | `"/opt/tivoli/tsm/client/ba/bin/dsm.opt"` | No       | Path for the dsm.opt file |
| `dsm_opt_state`               | `"present"`    | No       | Ensure file is present or absent |

## Usage

### Example Playbooks
```yaml
- name: Configure dsm.opt parameters while maintaining the existing the parameters
  hosts: all
  roles:
    - role: dsm_opt
      vars:
        dsm_opt_parameters:
          dsm_opt_servername: "NewServer"
          dsm_opt_nodename: "NewClient"
          dsm_opt_domain: "C: D: E:\\UserData"
          dsm_opt_password: "mypassword"
          dsm_opt_password_access: "generate"
```

### Deleting dsm.opt file
```yaml
- name: Remove dsm.opt
  hosts: all
  roles:
    - role: dsm_optfile
      vars:
        dsm_opt_state: "absent"
```


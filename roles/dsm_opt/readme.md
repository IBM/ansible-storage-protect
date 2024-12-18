# ibm.storage_protect.dsm_opt

This Ansible role generates a `dsm.opt` configuration file for IBM Storage Protect clients using a Jinja2 template. It ensures the mandatory variable `servername` is defined while handling optional variables gracefully.

## Features
- Dynamically generates the `dsm.opt` file
- Validates `servername` as a mandatory field.
- Supports include/exclude patterns and optional parameters.
- Handles `present` and `absent` states for file creation and deletion.
- Automatic Value Mapping**: Reads an existing `dsm.opt` file and automatically maps the existing values. 

## Variables

| Variable              | Default Value     | Required | Description             |
|-----------------------|-------------------|----------|-------------------------|
| `dsm_opt_servername`          | `""`             | Yes      | Server name defined in dsm.sys |
| `dsm_opt_nodename`            | `""`             | No       | Node name of the client |
| `dsm_opt_password`            | `""`             | No       | Specifies the password you use to log on to the IBM Storage Protect server.                       |
| `dsm_opt_password_access`     | `""`             | No       | The passwordaccess option specifies whether you want to generate your password automatically or set as a user prompt. |
| `dsm_opt_domain`              | `[]`             | No       | Directories or file systems to back up |
| `dsm_opt_include_patterns`    | `[]`             | No       | Patterns to explicitly include in backups |
| `dsm_opt_exclude_patterns`    | `[]`             | No       | Patterns to explicitly exclude from backups |
| `dsm_opt_managedservices`     | `""`             | No       | Managed services       |
| `dsm_opt_schedlogname`        | `""`             | No       | Schedule log path      |
| `dsm_opt_errorlogname`        | `""`             | No       | Error log path         |
| `dsm_opt_compression`         | `""`             | No       | Enable or disable compression |
| `dsm_opt_resourceutilization` | `""`             | No       | Number of threads      |
| `dsm_opt_tcpbuffsize`         | `""`             | No       | TCP buffer size        |
| `dsm_opt_tcpwindowsize`       | `""`             | No       | TCP sliding window size |
| `dsm_opt_httpport`            | `""`             | No       | HTTP port for the client |
| `dsm_opt_txnbytelimit`        | `""`             | No       | Maximum bytes in a transaction |
| `dsm_opt_optfile_path`        | `"/opt/tivoli/tsm/client/ba/bin/dsm.opt"` | No | Path for the dsm.opt file |
| `dsm_opt_state`               | `"present"`      | No       | Ensure file is present or absent |

## Usage

### Example
```yaml
- name: Configure dsm.opt with additional settings
  hosts: all
  roles:
    - role: dsm_optfile_role
      vars:
        dsm_opt_servername: "IBM_SP02"
        dsm_opt_nodename: "CLIENT02"
        dsm_opt_domain:
          - "/custom"
          - "/data"
        dsm_opt_include_patterns:
          - "/custom/app/.../*"
        dsm_opt_exclude_patterns:
          - "/custom/tmp/.../*"
        dsm_opt_compression: "yes"

```

### Deleting dsm.opt file
```yaml
- name: Remove dsm.opt
  hosts: all
  roles:
    - role: dsm_optfile_role
      vars:
        dsm_opt_servername: "IBM_SP01"
        dsm_opt_state: "absent"
```


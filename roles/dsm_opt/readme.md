# dsm_opt

This Ansible role generates a `dsm.opt` configuration file for IBM Storage Protect clients using a Jinja2 template. It ensures the mandatory variable `servername` is defined while handling optional variables gracefully.

## Features
- Dynamically generates the `dsm.opt` file.
- Validates `servername` as a mandatory field.
- Supports include/exclude patterns and optional parameters.
- Handles `present` and `absent` states for file creation and deletion.

## Variables

| Variable             | Default Value     | Required | Description                                    |
|----------------------|-------------------|----------|------------------------------------------------|
| `servername`         | `""`             | Yes      | Server name defined in dsm.sys                |
| `nodename`           | `""`             | No       | Node name of the client                       |
| `password_access`    | `""`             | No       | Password management setting                   |
| `domain`             | `[]`             | No       | Directories or file systems to back up        |
| `include_patterns`   | `[]`             | No       | Patterns to explicitly include in backups     |
| `exclude_patterns`   | `[]`             | No       | Patterns to explicitly exclude from backups   |
| `managedservices`    | `""`             | No       | Managed services                              |
| `schedlogname`       | `""`             | No       | Schedule log path                             |
| `errorlogname`       | `""`             | No       | Error log path                                |
| `compression`        | `""`             | No       | Enable or disable compression                 |
| `resourceutilization`| `""`             | No       | Number of threads                             |
| `tcpbuffsize`        | `""`             | No       | TCP buffer size                               |
| `tcpwindowsize`      | `""`             | No       | TCP sliding window size                       |
| `httpport`           | `""`             | No       | HTTP port for the client                      |
| `txnbytelimit`       | `""`             | No       | Maximum bytes in a transaction                |
| `optfile_path`       | `"/opt/tivoli/tsm/client/ba/bin/dsm.opt"` | No | Path for the dsm.opt file |
| `state`              | `"present"`      | No       | Ensure file is present or absent              |

## Usage

### Example
```yaml
- name: Configure dsm.opt with additional settings
  hosts: all
  roles:
    - role: dsm_optfile_role
      vars:
        servername: "IBM_SP02"
        nodename: "CLIENT02"
        domain:
          - "/custom"
          - "/data"
        include_patterns:
          - "/custom/app/.../*"
        exclude_patterns:
          - "/custom/tmp/.../*"
        compression: "yes"

```

### Deleting dsm.opt file
```yaml
- name: Remove dsm.opt
  hosts: all
  roles:
    - role: dsm_optfile_role
      vars:
        servername: "IBM_SP01"
        state: "absent"
```


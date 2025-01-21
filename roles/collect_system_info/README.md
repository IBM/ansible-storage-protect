# ibm.storage_protect.system_info_collection

This Ansible role is designed to collect detailed system information such as memory usage, CPU architecture, operating system details, and Java version. It aggregates all the collected data into a structured format for easy access and display.

## Features

- Retrieves memory information using the `free -m` command.
- Collects CPU architecture details using the `lscpu` command.
- Gathers OS name and version using Ansible's `setup` module.
- Extracts disk space details from memory statistics.
- Checks for the installed Java version, or notes if Java is not installed.
- Aggregates all system information into a single variable for display or further use.

## Tasks Included

1. **Memory Information**
   - Retrieves memory stats (total, used, free, swap).
2. **CPU Architecture**
   - Extracts architecture details using `lscpu`.
3. **Operating System Details**
   - Fetches OS family and version using Ansible facts.
4. **Java Version**
   - Identifies the installed Java version or provides an error message if Java is absent.
5. **System Info Aggregation**
   - Combines all collected details into a unified `system_info` variable for easy reference.
   - Details can be accessed using `system_info.Architecture`, `system_info.['Java Version']`, `system_info['Filesystem Disk Space'][0]['Free Memory']`.

## Usage

1. Include this role in your playbook:
2. Since this role uses `set_fact` to define variables dynamically, variables are directly available for use in subsequent tasks.

```yaml
- hosts: all
  roles:
    - system_info_collection
```

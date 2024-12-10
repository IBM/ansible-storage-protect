# Ansible Role: BA Client Installation

This Ansible role automates the installation and configuration of the Storage Protect BA Client. It includes steps to verify system compatibility, transfer necessary files, and install required packages.

---

## Role Variables

The following variables are defined in `defaults.yml`:

| Variable         | Description                                                       | Default Value                        |
|------------------|-------------------------------------------------------------------|--------------------------------------|
| `tar_file_path`  | Path on the control node to the tar file, which is to be installed | `./8.1.24.0-TIV-TSMBAC-LinuxX86.tar` |
| `extract_dest`   | Destination to extract files                     | `/opt/baClient`                      |
| `temp_dest`      | Temporary storage for tar file                                    | `/tmp/`                              |

---

## Tasks Overview

The role performs the following steps:

1. **Compatibility Checks**:
   - Verifies system architecture compatibility.
   - Checks if Java is installed.
   - Confirms that sufficient disk space is available.

2. **File Transfer and Extraction**:
   - Transfers the tar file to the remote host.
   - Creates the extraction directory.
   - Extracts the tar file.

3. **Package Installation**:
   - Installs the GSKit cryptographic and SSL libraries.
   - Installs API and BA packages, if not already installed.

4. **Validation**:
   - Checks for the successful installation of the BA Client using `dsmc`.

---

## Requirements

- Supported on Linux x86 architecture.
- Requires a minimum of 1400 MB of free disk space.
- Java must be installed on the system.

---

## Usage

To use this role, include it in your playbook as follows:

```yaml
- name: Run system info collection and compatibility check
  hosts: all
  gather_facts: yes  # This should be set in the playbook, not inside the role
  roles:
    - collect_system_info
    - install_ba_client
```

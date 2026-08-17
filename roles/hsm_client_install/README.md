# IBM Storage Protect HSM Client Installation Role

## Overview

This Ansible role provides comprehensive management of IBM Storage Protect Hierarchical Storage Management (HSM) Client on Linux systems. It supports installation, upgrade, uninstallation, and configuration operations with automatic rollback capabilities.

## Features

- **Complete Lifecycle Management**: Install, upgrade, uninstall, and configure HSM Client
- **Idempotent Operations**: Safe to run multiple times without side effects
- **Automatic Rollback**: Rolls back changes if operations fail
- **Pre-flight Checks**: Validates system requirements before installation
- **GPFS Integration**: Checks GPFS status and HSM state
- **Configuration Management**: Manages dsm.opt and dsm.sys files
- **Facts Gathering**: Collects comprehensive HSM client information
- **Multi-version Support**: Handles version comparisons and upgrades

## Requirements

### System Requirements
- **Operating System**: Red Hat Enterprise Linux 7/8/9, SUSE Linux Enterprise Server, AIX 7.1+
- **Architecture**: x86_64, s390x, ppc64le (Linux), ppc64 (AIX)
- **Disk Space**: Minimum 1500 MB free space
- **Privileges**: Root access required
- **GPFS (CRITICAL)**: IBM Spectrum Scale (GPFS) must be installed and configured

### GPFS Prerequisite (MANDATORY)

⚠️ **HSM Client REQUIRES IBM Spectrum Scale (GPFS) to function.**

**Required GPFS Packages:**
- `gpfs.base` (>= 4.2.1-0) - Core GPFS functionality
- `gpfs.gpl` - GPL modules
- `gpfs.gskit` - Security toolkit
- `gpfs.msg.en_US` - Message catalog
- `gpfs.compression` (recommended) - Compression support
- `gpfs.license.std` - Standard license

**Verification Commands:**
```bash
# Linux
rpm -qa | grep -i '^gpfs\.'
mmgetstate -a

# AIX
lslpp -l | grep -i '^gpfs\.'
mmgetstate -a
```

**Why GPFS is Required:**
- File system hooks for automatic migration/recall
- Policy-based file management
- Stub file management
- Transparent data movement between storage tiers

**Bypass Option (Testing Only):**
```yaml
skip_gpfs_check: true  # HSM will NOT function without GPFS
```

### Software Requirements
- Ansible 2.9 or higher
- Python 3.6 or higher on target hosts
- IBM Storage Protect HSM Client installation package

## Role Variables

### Required Variables

```yaml
hsm_client_version: "8.1.25.0"          # HSM Client version to install
hsm_client_state: "present"             # State: present or absent
linux_package_source: "/path/to/package.tar"  # Path to installation package
```

### Optional Variables

```yaml
# Installation paths
hsm_install_path: "/opt/tivoli/tsm/client/hsm/bin"
hsm_temp_dir: "/opt/hsmClient"
ba_client_extract_dest: "/opt/baClient"

# Daemon control
hsm_client_start_daemon: true

# Server configuration
server_name: "TSM_SERVER"
server_address: "tsm.example.com"
server_port: "1500"
node_name: "{{ ansible_hostname }}"

# Advanced options
force_install: false
test_hsm_connection: false
```

## Dependencies

- `system_info` role (for gathering system facts)

## Example Playbooks

### Install HSM Client

```yaml
---
- name: Install HSM Client
  hosts: hsm_servers
  become: true
  
  vars:
    hsm_client_version: "8.1.25.0"
    hsm_client_state: "present"
    linux_package_source: "/tmp/8.1.25.0-TIV-TSMHSM-LinuxX86.tar"
    server_name: "TSM_PROD"
    server_address: "tsm-server.example.com"
    
  roles:
    - hsm_client_install
```

### Upgrade HSM Client

```yaml
---
- name: Upgrade HSM Client
  hosts: hsm_servers
  become: true
  
  vars:
    hsm_client_version: "8.1.26.0"
    hsm_client_state: "present"
    linux_package_source: "/tmp/8.1.26.0-TIV-TSMHSM-LinuxX86.tar"
    
  roles:
    - hsm_client_install
```

### Uninstall HSM Client

```yaml
---
- name: Uninstall HSM Client
  hosts: hsm_servers
  become: true
  
  vars:
    hsm_client_version: "8.1.25.0"
    hsm_client_state: "absent"
    linux_package_source: "/tmp/8.1.25.0-TIV-TSMHSM-LinuxX86.tar"
    
  roles:
    - hsm_client_install
```

### Configure HSM Client

```yaml
---
- name: Configure HSM Client
  hosts: hsm_servers
  become: true
  
  tasks:
    - name: Configure HSM Client
      ansible.builtin.include_role:
        name: hsm_client_install
        tasks_from: configure
      vars:
        server_name: "TSM_PROD"
        server_address: "tsm-server.example.com"
        server_port: "1500"
        node_name: "{{ ansible_hostname }}"
```

### Gather HSM Client Facts

```yaml
---
- name: Gather HSM Client Facts
  hosts: hsm_servers
  become: true
  
  tasks:
    - name: Gather HSM facts
      hsm_client_facts:
        q_version: true
        q_gpfs_status: true
        q_hsm_status: true
        q_filespace: true
        q_systeminfo: true
      register: hsm_facts
      
    - name: Display facts
      debug:
        var: hsm_facts
```

## Playbook Examples

The role includes several ready-to-use playbooks:

### Installation
```bash
ansible-playbook playbooks/hsm_client_install/playbooks/linux/hsm_client_install_playbook.yml \
  -i inventory.ini \
  -e "target_hosts=hsm_servers"
```

### Upgrade
```bash
ansible-playbook playbooks/hsm_client_install/playbooks/linux/hsm_client_upgrade_playbook.yml \
  -i inventory.ini \
  -e "target_hosts=hsm_servers"
```

### Uninstallation
```bash
ansible-playbook playbooks/hsm_client_install/playbooks/linux/hsm_client_uninstall_playbook.yml \
  -i inventory.ini \
  -e "target_hosts=hsm_servers"
```

### Configuration
```bash
ansible-playbook playbooks/hsm_client_install/playbooks/linux/hsm_client_config_playbook.yml \
  -i inventory.ini \
  -e "target_hosts=hsm_servers"
```

### Facts Gathering
```bash
ansible-playbook playbooks/hsm_client_install/playbooks/linux/hsm_client_facts_playbook.yml \
  -i inventory.ini \
  -e "target_hosts=hsm_servers"
```

## Task Flow

### Installation Flow (`state: present`)

1. **Local Repository Check** (`local_repo_check.yml`)
   - Validates package availability on control node
   - Checks version format and file existence

2. **Determine Action** (`determine_action.yml`)
   - Compares installed version with requested version
   - Sets action to: `install`, `upgrade`, or `none`

3. **System Info Gathering** (`system_info` role)
   - Collects system facts for compatibility checks
   - Validates architecture, disk space, and prerequisites

4. **Installation** (`hsm_client_install_linux.yml`)
   - Performs pre-checks (architecture, disk space, privileges)
   - Transfers and extracts packages
   - Installs packages in correct dependency order:
     - gskcrypt64
     - gskssl64
     - TIVsm-API64
     - TIVsm-APIcit
     - TIVsm-HSM
     - TIVsm-HSMcit
   - Configures HSM client
   - Starts daemon (if enabled)
   - Performs post-installation verification

5. **Upgrade** (`hsm_client_upgrade_linux.yml`)
   - Backs up configuration files
   - Backs up existing packages
   - Uninstalls current version
   - Installs new version
   - Restores configuration
   - Rolls back on failure

### Uninstallation Flow (`state: absent`)

1. **Pre-checks**
   - Verifies HSM Client is installed
   - Checks GPFS and HSM status

2. **Backup**
   - Backs up configuration files (dsm.opt, dsm.sys)
   - Backs up package files for potential rollback

3. **Uninstallation** (`hsm_client_uninstall_linux.yml`)
   - Stops HSM daemon
   - Deactivates HSM (if active)
   - Uninstalls packages in reverse dependency order
   - Cleans up directories
   - Rolls back on failure

## Package Installation Order

The role installs packages in the following order to satisfy dependencies:

1. **GSKit Libraries**
   - gskcrypt64 (Cryptographic library)
   - gskssl64 (SSL library)

2. **API Packages**
   - TIVsm-API64 (64-bit API)
   - TIVsm-APIcit (API Common Interface)

3. **HSM Packages**
   - TIVsm-HSM (HSM Client)
   - TIVsm-HSMcit (HSM Common Interface)

## Rollback Mechanism

The role implements automatic rollback for failed operations:

### Install Rollback
- Uninstalls all packages installed during failed attempt
- Restores system to pre-installation state

### Upgrade Rollback
- Restores backed-up configuration files
- Reinstalls previous version from backup
- Removes failed upgrade packages

### Uninstall Rollback
- Reinstalls packages that were successfully uninstalled
- Restores configuration files

## Configuration Files

### dsm.sys
Location: `/opt/tivoli/tsm/client/hsm/bin/dsm.sys`

Contains server connection settings:
```
SErvername  TSM_SERVER
    TCPServeraddress  tsm.example.com
    TCPPort           1500
    NODENAME          hostname
    PASSWORDACCESS    GENERATE
    MANAGEDSERVICES   WEBCLIENT SCHEDULE HSM
```

### dsm.opt
Location: `/opt/tivoli/tsm/client/hsm/bin/dsm.opt`

Contains client options:
```
SErvername  TSM_SERVER
NODENAME    hostname
ERRORLOGNAME  /opt/tivoli/tsm/client/hsm/bin/dsmerror.log
SCHEDLOGNAME  /opt/tivoli/tsm/client/hsm/bin/dsmsched.log
MANAGEDSERVICES WEBCLIENT SCHEDULE HSM
```

## HSM-Specific Features

### GPFS Integration
- Checks GPFS cluster status before operations
- Validates GPFS filesystem availability
- Ensures HSM can be safely activated/deactivated

### HSM State Management
- Deactivates HSM before uninstallation
- Reactivates HSM after successful installation
- Handles HSM failover scenarios

### Policy Management
- Supports HSM policy configuration
- Manages file migration thresholds
- Configures recall settings

## Troubleshooting

### Installation Fails

**Check system requirements:**
```bash
ansible-playbook playbooks/hsm_client_install/playbooks/linux/hsm_client_facts_playbook.yml
```

**Verify package integrity:**
```bash
tar -tzf /path/to/package.tar
```

**Check logs:**
```bash
tail -f /opt/tivoli/tsm/client/hsm/bin/dsmerror.log
```

### Upgrade Fails

**Check current version:**
```bash
rpm -q TIVsm-HSM
```

**Verify rollback:**
```bash
ls -la /opt/hsmClientPackagesBk/
```

### GPFS Issues

**Check GPFS status:**
```bash
mmgetstate -a
```

**Check HSM state:**
```bash
mmhsm state show
```

## Best Practices

1. **Always backup** configuration files before upgrades
2. **Test in non-production** environment first
3. **Verify GPFS status** before HSM operations
4. **Monitor disk space** during installation
5. **Keep package sources** for rollback scenarios
6. **Document custom configurations** in version control
7. **Use version control** for playbook variables
8. **Test rollback procedures** regularly

## Known Limitations

- Windows support not yet implemented
- AIX support not yet implemented
- Requires GPFS to be pre-installed and configured
- Cannot upgrade across major versions (e.g., 7.x to 8.x) without manual intervention

## Support

For issues and questions:
- Check the troubleshooting section
- Review logs in `/opt/tivoli/tsm/client/hsm/bin/`
- Consult IBM Storage Protect documentation

## License

IBM Storage Protect Ansible Collection
Copyright IBM Corporation 2024

## Author

IBM Storage Protect Team

## Version History

- **1.0.0** (2024): Initial release with full HSM client support
  - Installation, upgrade, uninstallation
  - Configuration management
  - Facts gathering
  - GPFS integration
  - Automatic rollback

---

Made with Bob
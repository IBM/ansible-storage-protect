# System Dependencies Check Role

## Overview

This Ansible role validates all required system dependencies before IBM Storage Protect installation. It provides comprehensive dependency checking with detailed remediation guidance and optional automatic installation of missing dependencies.

## Features

- ✅ **Comprehensive Validation**: Checks Python, Java, system packages, and /tmp configuration
- ✅ **Detailed Remediation Reports**: Provides step-by-step instructions for fixing issues
- ✅ **Optional Auto-Install**: Can automatically install missing dependencies (non-production use)
- ✅ **Cross-Platform Support**: Works on RHEL, Debian, Ubuntu, and AIX
- ✅ **Production-Safe**: Validation-only mode by default, no automatic changes

## Dependencies Validated

### Software Requirements
- **Python 3.9+**: Required for Ansible modules and IBM Storage Protect components
- **Java 8+**: Required for IBM Installation Manager and SP Server
- **lsof**: List open files utility
- **rsync**: File synchronization utility

### System Configuration
- **/tmp permissions**: Must be `1777` (rwxrwxrwt)
- **/tmp mount options**: Must NOT have `noexec` flag
- **/tmp disk space**: Minimum 2GB free space

## Role Variables

### Control Variables

```yaml
# Enable automatic installation of missing dependencies
# WARNING: Only use in non-production or controlled environments
# Default: false (validation only)
install_dependencies: false

# Fail playbook if dependencies are missing
# Default: true
fail_on_missing_dependencies: true

# Generate detailed remediation report
# Default: true
generate_remediation_report: true
```

### Requirement Variables

```yaml
# Python version requirement
required_python_version: "3.9"

# Java version requirement
required_java_version: "1.8"  # Java 8 or higher

# /tmp directory requirements
tmp_required_permissions: "1777"
tmp_required_space_mb: 2048  # 2GB minimum
```

## Usage

### Basic Usage (Validation Only)

```yaml
- name: Validate system dependencies
  hosts: all
  roles:
    - system_dependencies_check
```

This will:
1. Check all dependencies
2. Display validation summary
3. Generate remediation report if issues found
4. Fail playbook if dependencies are missing

### With Auto-Install (Non-Production)

```yaml
- name: Validate and install dependencies
  hosts: all
  vars:
    install_dependencies: true
  roles:
    - system_dependencies_check
```

Or via command line:

```bash
ansible-playbook playbook.yml -e "install_dependencies=true"
```

### Validation Only (No Failure)

```yaml
- name: Check dependencies without failing
  hosts: all
  vars:
    fail_on_missing_dependencies: false
  roles:
    - system_dependencies_check
```

## Example Output

### Successful Validation

```
============================================================
DEPENDENCY VALIDATION SUMMARY - hostname
============================================================

Python 3.9+:
  Status: ✓ INSTALLED
  Version: Python 3.9.16

Java:
  Status: ✓ INSTALLED
  Version: openjdk version "1.8.0_362"

System Packages:
  lsof: ✓ INSTALLED - List open files utility
  rsync: ✓ INSTALLED - File synchronization utility

/tmp Directory:
  Permissions: ✓ VALID (1777 / required: 1777)
  Mount Options: ✓ VALID
  Disk Space: ✓ SUFFICIENT (5120MB / required: 2048MB)

Overall Status: ✓ ALL DEPENDENCIES MET
============================================================
```

### Failed Validation with Remediation

```
============================================================
DEPENDENCY VALIDATION SUMMARY - hostname
============================================================

Python 3.9+:
  Status: ✗ MISSING
  Required: 3.9+

Java:
  Status: ✗ MISSING
  Required: 1.8+

System Packages:
  lsof: ✗ MISSING - List open files utility
  rsync: ✓ INSTALLED - File synchronization utility

/tmp Directory:
  Permissions: ✗ INVALID (755 / required: 1777)
  Mount Options: ✗ INVALID (noexec present)
  Disk Space: ✓ SUFFICIENT (3072MB / required: 2048MB)

Overall Status: ✗ MISSING DEPENDENCIES DETECTED
============================================================

============================================================
REMEDIATION REPORT - hostname
============================================================

The following dependencies are missing or misconfigured:

1. Python 3.9+
   Issue: Python 3.9 or higher is not installed
   Required for: Ansible modules and IBM Storage Protect components
   
   Installation command (RedHat):
   sudo yum install -y python39

2. Java 1.8+
   Issue: Java is not installed
   Required for: IBM Installation Manager and SP Server
   
   Installation command (RedHat):
   sudo yum install -y java-1.8.0-openjdk

3. lsof
   Issue: List open files utility is not installed
   Required for: IBM Storage Protect operations
   
   Installation command (RedHat):
   sudo yum install -y lsof

4. /tmp Directory Permissions
   Issue: Current permissions are 755, required: 1777
   Required for: Temporary file operations during installation
   
   Remediation command:
   sudo chmod 1777 /tmp
   
   Verify with:
   ls -ld /tmp
   # Should show: drwxrwxrwt

5. /tmp Mount Options
   Issue: noexec flag present
   Required for: IBM Installation Manager execution
   
   Temporary fix (until reboot):
   sudo mount -o remount,exec /tmp
   
   Permanent fix:
   1. Edit /etc/fstab
   2. Find the /tmp mount line
   3. Remove 'noexec' from mount options
   4. Save and remount: sudo mount -o remount /tmp
   
   Verify with:
   mount | grep /tmp
   # Should NOT show 'noexec'

============================================================
QUICK FIX - Install All Missing Dependencies
============================================================

To automatically install all missing dependencies, re-run with:

  ansible-playbook playbooks/petascale_install.yml \
    -i playbooks/inventory/petascale.ini \
    -e "install_dependencies=true"

⚠️  WARNING: Auto-installation should only be used in:
   - Non-production environments
   - Controlled test environments
   - With explicit customer approval

For production systems, manually install dependencies following
the remediation steps above.
============================================================
```

## Integration with Petascale Playbooks

This role is integrated into the petascale installation playbooks:

```yaml
# playbooks/petascale_install.yml
- name: Validate system dependencies
  hosts: all
  gather_facts: true
  roles:
    - system_dependencies_check
```

## Best Practices

### Production Environments

1. **Always use validation-only mode** (default)
2. **Manually install dependencies** following remediation report
3. **Verify installations** before proceeding with IBM Storage Protect installation
4. **Document any deviations** from standard configurations

### Non-Production Environments

1. **Use auto-install for convenience**: `-e "install_dependencies=true"`
2. **Review what was installed**: Check the auto-install completion message
3. **Re-run validation**: Confirm all dependencies are met
4. **Note manual interventions**: Some issues (noexec, disk space) require manual fixes

### Troubleshooting

#### Python 3.9 Not Found After Installation

```bash
# Verify Python 3.9 is in PATH
which python3.9

# If not found, create symlink
sudo ln -s /usr/bin/python3.9 /usr/local/bin/python3.9
```

#### Java Not Recognized

```bash
# Verify Java installation
java -version

# Set JAVA_HOME if needed
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk
```

#### /tmp Mount Options Persist After Reboot

```bash
# Verify /etc/fstab was updated
grep /tmp /etc/fstab

# Ensure 'noexec' is removed from options
```

## License

Apache-2.0

## Author

IBM Storage Protect Team
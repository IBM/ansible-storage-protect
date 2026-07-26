# SP Server Orchestration Playbooks

This directory contains playbooks for orchestrating IBM Storage Protect (SP) Server installation, configuration, and management across multiple platforms.

## Overview

The SP Server orchestration playbooks automate the deployment and configuration of Storage Protect servers on various platforms including Windows, Linux, AIX, and PPC64LE architectures.

## Playbooks

### 1. playbook.yml - Main Orchestration Playbook

The main orchestration playbook that handles SP Server installation, upgrade, and uninstallation across different platforms.

#### Supported Platforms

- **Windows (x64)**: `sp_server_windows` host group
- **Linux (x86_64) and AIX**: `sp_server_linux` and `sp_server_aix` host groups
- **PPC64LE (IBM Power)**: `sp_server_ppc64le` host group

#### Plays

**PLAY 1: Windows SP Server Orchestration**
- Target hosts: `sp_server_windows`
- Handles Windows-specific installation using PowerShell and Windows modules
- Uses `install.bat` for installation

**PLAY 2: Linux SP Server Orchestration**
- Target hosts: `sp_server_linux:sp_server_aix`
- Handles Linux and AIX installations using bash/shell scripts
- Uses `install.sh` for installation

**PLAY 3: PPC64LE SP Server Orchestration**
- Target hosts: `sp_server_ppc64le`
- Handles IBM Power architecture (ppc64le) installations
- Uses standard Linux installation flow with systemd service management
- Follows the same process as Linux x86_64 but targets Power architecture systems

#### Usage

```bash
# Install SP Server on all platforms
ansible-playbook playbooks/sp_server/playbook.yml -e "sp_mode=install"

# Install on specific platform
ansible-playbook playbooks/sp_server/playbook.yml -e "sp_mode=install" --limit sp_server_ppc64le

# Upgrade SP Server
ansible-playbook playbooks/sp_server/playbook.yml -e "sp_mode=upgrade"

# Uninstall SP Server
ansible-playbook playbooks/sp_server/playbook.yml -e "sp_mode=uninstall"
```

### 2. playbook_configure.yml - Configuration Playbook

Handles post-installation configuration of SP Server using Python implementation.

#### Supported Platforms

- Windows
- Linux (x86_64)
- AIX
- PPC64LE

#### Usage

```bash
ansible-playbook playbooks/sp_server/playbook_configure.yml
```

## Variables

Key variables are defined in `vars/sp_server.yml`:

| Variable | Description | Default |
|----------|-------------|---------|
| `sp_mode` | Operation mode: install, upgrade, uninstall | `install` |
| `sp_server_version` | SP Server version to install | `8.2.1.000` |
| `sp_pwd` | Server password | - |
| `sp_log_level` | Logging level | `DEBUG` |
| `sp_sync_scripts` | Sync scripts to target | `true` |
| `sp_server_install_dest_win` | Windows installation directory | `C:/temp/baserver` |
| `sp_server_install_dest_lin` | Linux/Unix installation directory | `/tmp/baserver` |

## Inventory Configuration

Define your hosts in the Ansible inventory with appropriate groups:

```ini
[sp_server_windows]
win-server-01 ansible_host=192.168.1.10

[sp_server_linux]
linux-server-01 ansible_host=192.168.1.20

[sp_server_aix]
aix-server-01 ansible_host=192.168.1.30

[sp_server_ppc64le]
power-server-01 ansible_host=192.168.1.40
power-server-02 ansible_host=192.168.1.41
```

## PPC64LE Platform Support

### Architecture Details

- **Platform**: IBM Power Systems (ppc64le architecture)
- **Operating System**: Linux distributions on Power (RHEL, SLES, Ubuntu)
- **Service Management**: systemd (same as Linux x86_64)
- **Installation Method**: Binary installation using `install.sh`

### Requirements

1. **Python 3.9+** on the target system
2. **Sufficient disk space** for SP Server installation
3. **Network connectivity** to the Ansible control node
4. **Root or sudo access** on target systems

### Binary Naming Convention

PPC64LE binaries follow the naming pattern:
```
<version>-<vendor>-<product>-Linuxppc64le.bin
```

Example: `8.2.1.000-IBM-SPOC-Linuxppc64le.bin`

### Installation Flow

1. **Pre-checks**: Validate system compatibility and requirements
2. **File Transfer**: Copy installation binaries and scripts to target
3. **Installation**: Execute `install.sh` with appropriate parameters
4. **Service Setup**: Configure systemd service for automatic startup
5. **Post-checks**: Verify installation success

### Differences from x86_64

- Uses architecture-specific binaries (Linuxppc64le.bin)
- Same installation process and service management as Linux x86_64
- No special handling required beyond architecture detection

## Module Files

The playbooks copy the following Python modules to target systems:

- `sp_server.py` - Main orchestration module
- `sp_server_configure.py` - Configuration module
- `sp_server_utils.py` - Utility functions
- `sp_server_constants.py` - Constants and definitions

## Logging

Logs are stored on target systems:

- **Linux/Unix**: `/var/log/sp_server/sp_server_configuration.log`
- **Windows**: `C:\var\log\sp_server\sp_server_configuration.log`

## Troubleshooting

### Common Issues

1. **Python version mismatch**: Ensure Python 3.9+ is installed on targets
2. **Permission errors**: Verify sudo/root access
3. **Binary not found**: Check artifact naming and placement
4. **Service start failures**: Review systemd logs with `journalctl -u <service-name>`

### Debug Mode

Enable debug logging:
```bash
ansible-playbook playbooks/sp_server/playbook.yml -e "sp_log_level=DEBUG" -vvv
```

## Related Documentation

- [IMPLEMENTATION_DIAGRAM.md](../../IMPLEMENTATION_DIAGRAM.md) - Architecture diagrams
- [CHANGES_SUMMARY.md](../../CHANGES_SUMMARY.md) - Platform support changes
- [PLATFORM_SUPPORT_PLAN.md](../../PLATFORM_SUPPORT_PLAN.md) - Platform support details
- [IMPLEMENTATION_SUMMARY.md](../../IMPLEMENTATION_SUMMARY.md) - Implementation overview

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the related documentation
3. Check the main repository README.md
4. Open an issue in the repository

## License

Apache License, Version 2.0
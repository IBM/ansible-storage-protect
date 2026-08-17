# Host Variables Directory

This directory contains per-host configuration files for the petascale installation playbook.

## Purpose

Each file in this directory corresponds to a specific host in your inventory and contains variables that are specific to that host. This allows you to customize settings for individual BA clients, SP servers, or other nodes.

## File Naming Convention

Files must be named exactly as the hostname appears in your inventory file:

```
Inventory hostname: ba-client-01
Host vars file:     ba-client-01.yml
```

## Example Files Provided

This directory includes example configuration files for different scenarios:

### Installation Examples
- **ba-client-01.yml** - Standard BA Client configuration with version 8.2.1.0
- **ba-client-02.yml** - Different version (8.1.24.0) with auto-start enabled
- **ba-client-03.yml** - Custom paths and pre-configured server connection
- **sp-server-01.yml** - SP Server installation configuration

### Upgrade Examples
- **sp-server-01-upgrade-example.yml** - SP Server upgrade configuration example
- **ba-client-01-upgrade-example.yml** - BA Client upgrade configuration example

These upgrade examples show how to configure hosts for upgrading to newer versions.

## Creating Your Own Host Variables

### Step 1: Copy an Example File

```bash
cp ba-client-01.yml my-actual-hostname.yml
```

### Step 2: Edit the File

```bash
vi my-actual-hostname.yml
```

### Step 3: Customize Variables

Edit the variables to match your requirements:

```yaml
---
# Host-specific variables for my-actual-hostname

ba_client_version: "8.2.1.0"
os_type: "LinuxX86"
ba_client_package_path: "/tmp/8.2.1.0-TIV-TSMBAC-LinuxX86.tar"
ba_client_start_daemon: false
```

## Common Variables for BA Clients

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ba_client_version` | Yes | BA Client version | `"8.2.1.0"` |
| `os_type` | Yes | OS type | `"LinuxX86"` or `"LinuxX86_64"` |
| `ba_client_package_path` | Yes | Package location on remote node | `"/tmp/8.2.1.0-TIV-TSMBAC-LinuxX86.tar"` |
| `ba_client_state` | No | Install, uninstall, or upgrade | `"present"` (default) |
| `ba_client_extract_dest` | No | Installation directory | `"/opt/baClient"` (default) |
| `ba_client_temp_dest` | No | Temp directory | `"/tmp/"` (default) |
| `ba_client_start_daemon` | No | Auto-start daemon | `false` (default) |

## Common Variables for SP Servers

### Package Location (Choose One Method)

**RECOMMENDED: Explicit Package Path**
```yaml
sp_server_package_path: "/tmp/8.2.2.000-IBM-SPSRV-LinuxX86_64.bin"
```
- Eliminates ambiguity when multiple packages exist
- Consistent with BA Client approach
- Clear error messages if file not found

**LEGACY: Pattern Matching**
```yaml
sp_server_version: "8.2.2.000"
sp_server_bin_repo: "/tmp"
```
- Searches for files matching `{{ sp_server_version }}*.bin`
- May match multiple files (uses first match)
- Kept for backward compatibility

### All SP Server Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `sp_server_package_path` | Recommended | Explicit path to binary file | `"/tmp/8.2.2.000-IBM-SPSRV-LinuxX86_64.bin"` |
| `sp_server_version` | Yes* | SP Server version | `"8.2.2.000"` |
| `sp_server_bin_repo` | Yes* | Package directory (legacy) | `"/tmp"` |
| `sp_server_state` | Yes | Install, uninstall, or upgrade | `"present"`, `"absent"`, or `"upgrade"` |
| `sp_server_action` | Yes | Action to perform | `"install"` or `"upgrade"` |
| `sp_server_install_dest` | No | Installation directory | `"/opt/sp_server_binary/"` (default) |
| `sp_server_upgrade_dest` | No | Upgrade staging directory | `"/opt/sp_server_upgrade_binary"` (default) |
| `server_name` | Yes | Server name | `"PETASCALE-SP01"` |

*Required only if `sp_server_package_path` is not defined

## Upgrade Configuration

To configure a host for upgrade, you need to:

1. **Set the target version** - Must be higher than currently installed version
2. **Set the state** - Use `"upgrade"` for SP Server, `"present"` for BA Client
3. **Set the action** - Use `"upgrade"` for SP Server (BA Client auto-detects)
4. **Ensure package is available** - New version package must be on remote node

### SP Server Upgrade Example

**Recommended (Explicit Path):**
```yaml
sp_server_version: "8.2.2.000"                                    # Target version (must be higher)
sp_server_state: "upgrade"                                        # State must be "upgrade"
sp_server_action: "upgrade"                                       # Action must be "upgrade"
sp_server_package_path: "/tmp/8.2.2.000-IBM-SPSRV-LinuxX86_64.bin"  # Exact package path
```

**Legacy (Pattern Matching):**
```yaml
sp_server_version: "8.2.2.000"      # Target version (must be higher)
sp_server_state: "upgrade"          # State must be "upgrade"
sp_server_action: "upgrade"         # Action must be "upgrade"
sp_server_bin_repo: "/tmp"          # Directory containing package
```

### BA Client Upgrade Example

```yaml
ba_client_version: "8.2.1.0"                                    # Target version (must be higher)
ba_client_state: "present"                                      # State is "present" (role auto-detects upgrade)
ba_client_package_path: "/tmp/8.2.1.0-TIV-TSMBAC-LinuxX86.tar" # Location of new version package
```

See the upgrade example files for complete configurations:
- `sp-server-01-upgrade-example.yml`
- `ba-client-01-upgrade-example.yml`

## Variable Precedence

Variables in this directory have the **HIGHEST PRIORITY** and will override:
- Group variables (`group_vars/ba_clients.yml`)
- Global variables (`group_vars/all.yml`)
- Playbook defaults

## Best Practices

1. **One file per host** - Create a separate file for each host that needs custom configuration
2. **Use meaningful names** - File name must match the inventory hostname exactly
3. **Document your changes** - Add comments to explain custom settings
4. **Version control** - Commit these files to git to track changes
5. **Test incrementally** - Test with one host before deploying to all

## Examples

### Example 1: Three BA Clients with Different Versions

```
host_vars/
├── ba-client-01.yml    # Version 8.2.1.0
├── ba-client-02.yml    # Version 8.1.24.0
└── ba-client-03.yml    # Version 8.2.1.0 with custom paths
```

### Example 2: Mixed Environment

```
host_vars/
├── ba-client-01.yml    # Custom configuration
├── ba-client-02.yml    # Custom configuration
├── ba-client-03.yml    # Uses group_vars defaults (no file needed)
└── sp-server-01.yml    # SP Server configuration
```

## Troubleshooting

### Issue: Variables Not Being Applied

**Problem:** Changes to host_vars file are not taking effect

**Solutions:**
1. Verify filename matches inventory hostname exactly (case-sensitive)
2. Check YAML syntax is valid: `yamllint ba-client-01.yml`
3. Verify the host is in the correct group in inventory
4. Check variable names are spelled correctly

### Issue: Which Variables Are Being Used?

**Problem:** Not sure which variables are being applied to a host

**Solution:** Use ansible-inventory to see all variables for a host:

```bash
ansible-inventory -i ../inventory/petascale.ini \
  --host ba-client-01 --yaml
```

## Additional Resources

- **Configuration Guide:** `../CONFIGURATION_GUIDE.md`
- **Main README:** `../PETASCALE_DEPLOYMENT_README.md`
- **Ansible Documentation:** https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html

## Need Help?

1. Review the example files in this directory
2. Check the Configuration Guide: `../CONFIGURATION_GUIDE.md`
3. Consult Ansible variable precedence documentation
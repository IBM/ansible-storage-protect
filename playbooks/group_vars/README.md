# Group Variables Directory

This directory contains group-level configuration files for the petascale installation playbook.

## Purpose

Files in this directory define variables that apply to groups of hosts. These variables are shared across all hosts in a group but can be overridden by individual host_vars files.

## Files in This Directory

- **all.yml** - Global variables that apply to ALL hosts
- **ba_clients.yml** - Variables specific to all BA Client hosts
- **sp_servers.yml** - Variables specific to all SP Server hosts (create as needed)

## Variable Precedence

Group variables have **MEDIUM PRIORITY**:

1. **host_vars/\<hostname\>.yml** (HIGHEST - overrides everything)
2. **group_vars/\<groupname\>.yml** (MEDIUM - this directory)
3. **group_vars/all.yml** (LOWER - global defaults)
4. Playbook defaults (LOWEST)

## File: all.yml

Contains global defaults for all hosts in your inventory.

**Use for:**
- Software versions used across all nodes
- Common connection settings
- Global Python interpreter paths
- Default package locations

**Example:**
```yaml
---
software_version: "8.2.1.0"
os_type: "LinuxX86"
package_location: "/tmp"
ansible_python_interpreter: /usr/bin/python3.9
```

## File: ba_clients.yml

Contains defaults for all hosts in the `[ba_clients]` group.

**Use for:**
- Default BA Client installation settings
- Common installation directories
- Shared daemon start preferences
- Default package paths (can use templates)

**Example:**
```yaml
---
ba_client_state: "present"
ba_client_extract_dest: "/opt/baClient"
ba_client_temp_dest: "/tmp/"
ba_client_start_daemon: false
```

## When to Use Group Variables vs Host Variables

### Use Group Variables When:
- Settings are the same for all hosts in a group
- You want to set defaults that can be overridden per host
- Managing common configuration across multiple nodes

### Use Host Variables When:
- Each host needs different settings
- Specific customization for individual nodes
- Different versions per host

## Example Scenarios

### Scenario 1: All BA Clients Use Same Version

**Configuration:**
```yaml
# group_vars/ba_clients.yml
---
ba_client_version: "8.2.1.0"
os_type: "LinuxX86"
ba_client_package_path: "/tmp/8.2.1.0-TIV-TSMBAC-LinuxX86.tar"
```

**Result:** All BA clients will use version 8.2.1.0

### Scenario 2: Most BA Clients Use Same Version, One Different

**Configuration:**
```yaml
# group_vars/ba_clients.yml (default for all)
---
ba_client_version: "8.2.1.0"
os_type: "LinuxX86"
ba_client_package_path: "/tmp/8.2.1.0-TIV-TSMBAC-LinuxX86.tar"
```

```yaml
# host_vars/ba-client-02.yml (override for one host)
---
ba_client_version: "8.1.24.0"
ba_client_package_path: "/tmp/8.1.24.0-TIV-TSMBAC-LinuxX86.tar"
```

**Result:** 
- ba-client-01, ba-client-03, etc. use 8.2.1.0 (from group_vars)
- ba-client-02 uses 8.1.24.0 (from host_vars override)

### Scenario 3: Each BA Client Uses Different Version

**Configuration:**
```yaml
# group_vars/ba_clients.yml (only common settings)
---
ba_client_state: "present"
ba_client_extract_dest: "/opt/baClient"
ba_client_start_daemon: false
```

```yaml
# host_vars/ba-client-01.yml
---
ba_client_version: "8.2.1.0"
ba_client_package_path: "/tmp/8.2.1.0-TIV-TSMBAC-LinuxX86.tar"
```

```yaml
# host_vars/ba-client-02.yml
---
ba_client_version: "8.1.24.0"
ba_client_package_path: "/tmp/8.1.24.0-TIV-TSMBAC-LinuxX86.tar"
```

**Result:** Each host uses its own version, but shares common settings

## Creating Additional Group Variables

You can create additional group_vars files for other groups in your inventory:

```bash
# For SP servers
vi group_vars/sp_servers.yml

# For storage agents
vi group_vars/storage_agents.yml

# For operations center
vi group_vars/operations_center.yml

# For environment-specific settings
vi group_vars/petascale_production.yml
```

## Best Practices

1. **Use all.yml for truly global settings**
   - Settings that apply to every host
   - Connection parameters
   - Python interpreter paths

2. **Use group-specific files for group defaults**
   - Settings common to a group
   - Can be overridden by host_vars

3. **Keep it DRY (Don't Repeat Yourself)**
   - Set common values in group_vars
   - Override only what's different in host_vars

4. **Document your variables**
   - Add comments explaining each variable
   - Include examples of valid values

5. **Use templates for dynamic values**
   ```yaml
   ba_client_package_path: "/tmp/{{ ba_client_version }}-TIV-TSMBAC-{{ os_type }}.tar"
   ```

## Troubleshooting

### Issue: Group Variables Not Applied

**Problem:** Variables in group_vars are not being used

**Solutions:**
1. Verify the group name matches your inventory exactly
2. Check the host is actually in that group
3. Ensure YAML syntax is valid: `yamllint ba_clients.yml`
4. Check if host_vars is overriding the value

### Issue: Which Variables Are Active?

**Problem:** Not sure which variables are being applied

**Solution:** Use ansible-inventory to see all variables:

```bash
# See all variables for a specific host
ansible-inventory -i ../inventory/petascale.ini \
  --host ba-client-01 --yaml

# See all variables for a group
ansible-inventory -i ../inventory/petascale.ini \
  --graph ba_clients --vars
```

### Issue: Variables Not Overriding as Expected

**Problem:** Host_vars not overriding group_vars

**Solution:** Check variable precedence:
1. Verify host_vars file exists and is named correctly
2. Ensure variable names match exactly (case-sensitive)
3. Check YAML indentation is correct

## Variable Naming Conventions

Follow these conventions for consistency:

- Use lowercase with underscores: `ba_client_version`
- Be descriptive: `ba_client_package_path` not `pkg_path`
- Group-specific prefix: `ba_client_*` for BA client variables
- Boolean values: `true` or `false` (lowercase)
- Strings: Always quote: `"8.2.1.0"`

## Additional Resources

- **Configuration Guide:** `../CONFIGURATION_GUIDE.md`
- **Host Variables README:** `../host_vars/README.md`
- **Main README:** `../PETASCALE_DEPLOYMENT_README.md`
- **Ansible Documentation:** https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html

## Need Help?

1. Review the example files in this directory
2. Check the Configuration Guide: `../CONFIGURATION_GUIDE.md`
3. Consult the host_vars README for per-host customization
4. Review Ansible variable precedence documentation
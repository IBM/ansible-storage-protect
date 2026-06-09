# BA Client Facts - Windows Execution Guide

This guide explains how to gather IBM Storage Protect BA Client facts on Windows machines.

## Overview

The `ba_client_facts` module can gather various information from BA Client installations on Windows, including:
- Client version information
- Session details (server, node, connection)
- Schedule information
- Filespace statistics
- Backup/Archive information
- Include/Exclude rules
- System information
- Client configuration options

## Prerequisites

1. **IBM Storage Protect BA Client** must be installed on the Windows machine
2. **Python 3.x** must be installed and accessible via PATH
3. **DSMC command** must be available in PATH or at a known location
4. **Valid credentials** for the BA Client (server name, node name, password)
5. **Ansible** installed on the control node (for running playbooks)

## Execution Methods

### Method 1: Using Ansible Playbook (Recommended)

Use the provided playbook to gather facts from Windows hosts:

```bash
ansible-playbook playbooks/ba_client_install/playbooks/windows/ba_client_facts_playbook.yml \
  -i inventory.ini \
  -e "ba_client_password=YourPassword"
```

**Inventory Example (inventory.ini):**
```ini
[windows]
windows-host-1 ansible_host=192.168.1.100
windows-host-2 ansible_host=192.168.1.101

[windows:vars]
ansible_connection=winrm
ansible_user=Administrator
ansible_password=AdminPassword
ansible_winrm_transport=ntlm
ansible_winrm_server_cert_validation=ignore
```

### Method 2: Direct Python Execution on Windows

If you need to run the module directly on a Windows machine:

#### Step 1: Copy Required Files

Copy these files to the Windows machine (e.g., `C:\temp\ansible-storage-protect\`):
- `plugins/modules/ba_client_facts.py`
- `plugins/module_utils/ba_client_facts.py`
- `plugins/module_utils/dsmc_adapter.py`

#### Step 2: Execute with Python

```cmd
python C:\temp\ansible-storage-protect\ba_client_facts.py ^
  --server-name TSM_SERVER ^
  --node-name CLIENT_NODE ^
  --password YourPassword ^
  --q-version ^
  --q-session ^
  --q-filespace
```

#### Available Query Flags:

| Flag | Description |
|------|-------------|
| `--q-version` | Gather BA Client version information |
| `--q-session` | Gather current session details |
| `--q-schedule` | Gather schedule information |
| `--q-filespace` | Gather filespace statistics |
| `--q-backup` | Gather backup information |
| `--q-archive` | Gather archive information |
| `--q-inclexcl` | Gather include/exclude rules |
| `--q-systeminfo` | Gather system information |
| `--q-options` | Gather client configuration options |

### Method 3: PowerShell Execution

```powershell
# Set variables
$ServerName = "TSM_SERVER"
$NodeName = "CLIENT_NODE"
$Password = "YourPassword"
$ModulePath = "C:\temp\ansible-storage-protect\ba_client_facts.py"

# Execute and capture output
$output = python $ModulePath `
  --server-name $ServerName `
  --node-name $NodeName `
  --password $Password `
  --q-version `
  --q-session `
  --q-filespace `
  --q-schedule

# Parse JSON output
$facts = $output | ConvertFrom-Json

# Display results
Write-Host "Client Version: $($facts.results.q_version.client_version)"
Write-Host "Server Name: $($facts.results.q_session.server_name)"
```

## Example Outputs

### Version Query Output:
```json
{
  "changed": false,
  "results": {
    "q_version": {
      "client_version": "8.1.25.0",
      "client_name": "IBM Storage Protect",
      "api_version": "8.1.25.0"
    }
  }
}
```

### Session Query Output:
```json
{
  "changed": false,
  "results": {
    "q_session": {
      "server_name": "TSM_SERVER",
      "server_address": "192.168.1.50",
      "server_port": "1500",
      "node_name": "CLIENT_NODE"
    }
  }
}
```

### Filespace Query Output:
```json
{
  "changed": false,
  "results": {
    "q_filespace": [
      {
        "filespace_name": "C:",
        "fsid": "1",
        "platform": "WinNT",
        "filespace_type": "NTFS",
        "capacity_mb": "102400",
        "pct_util": "45.2",
        "last_backup_start": "2024-01-15 10:30:00",
        "last_backup_completion": "2024-01-15 11:45:00"
      }
    ]
  }
}
```

## Troubleshooting

### Issue: "dsmc command not found"

**Solution:** Add DSMC to PATH or specify full path:
```cmd
set PATH=%PATH%;C:\Program Files\Tivoli\TSM\baclient
```

### Issue: "ANS1017E Session rejected: TCP/IP connection failure"

**Solution:** 
- Verify server name and address in dsm.opt
- Check network connectivity to SP server
- Verify firewall rules allow port 1500 (or configured port)

### Issue: "ANS1035S Options file 'C:\...\dsm.opt' could not be found"

**Solution:**
- Ensure BA Client is properly installed
- Verify dsm.opt exists in the BA Client bin directory
- Check file permissions

### Issue: Python import errors

**Solution:**
- Ensure all required files are copied to the same directory
- Check Python version (3.6+ required)
- Verify file paths in the command

## Advanced Usage

### Gathering All Facts:

```cmd
python ba_client_facts.py ^
  --server-name TSM_SERVER ^
  --node-name CLIENT_NODE ^
  --password YourPassword ^
  --q-version ^
  --q-session ^
  --q-schedule ^
  --q-filespace ^
  --q-backup ^
  --q-archive ^
  --q-inclexcl ^
  --q-systeminfo ^
  --q-options
```

### Saving Output to File:

```cmd
python ba_client_facts.py ^
  --server-name TSM_SERVER ^
  --node-name CLIENT_NODE ^
  --password YourPassword ^
  --q-version ^
  --q-session > ba_client_facts.json
```

### Using in Batch Scripts:

```batch
@echo off
setlocal

set SERVER_NAME=TSM_SERVER
set NODE_NAME=%COMPUTERNAME%
set PASSWORD=YourPassword
set MODULE_PATH=C:\temp\ansible-storage-protect\ba_client_facts.py

echo Gathering BA Client facts...
python %MODULE_PATH% ^
  --server-name %SERVER_NAME% ^
  --node-name %NODE_NAME% ^
  --password %PASSWORD% ^
  --q-version ^
  --q-session ^
  --q-filespace > facts_%NODE_NAME%.json

echo Facts saved to facts_%NODE_NAME%.json
endlocal
```

## Security Considerations

1. **Password Protection**: Never hardcode passwords in scripts. Use:
   - Environment variables
   - Secure credential storage (Windows Credential Manager)
   - Ansible Vault for playbooks

2. **File Permissions**: Restrict access to scripts containing credentials

3. **Logging**: Be careful not to log passwords in output files

## Integration with Monitoring Systems

The JSON output can be easily integrated with monitoring and reporting systems:

```powershell
# Example: Send facts to monitoring system
$facts = python ba_client_facts.py ... | ConvertFrom-Json
$version = $facts.results.q_version.client_version

if ([version]$version -lt [version]"8.1.0") {
    Send-Alert "BA Client version $version is outdated"
}
```

## Support

For issues or questions:
- Check the main README.md
- Review IBM Storage Protect documentation
- Contact your system administrator
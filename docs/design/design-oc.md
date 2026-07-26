# IBM Storage Protect Operations Center (OC) Configuration Design

## Overview

The Operations Center (OC) configuration component provides Ansible automation for managing IBM Storage Protect Operations Center. It enables administrators to configure, start, stop, and restart the Operations Center service through a unified Ansible interface.

## Architecture

### Component Overview

```mermaid
graph TB
    subgraph "Ansible Control Node"
        Playbook[oc_configure_playbook.yml]
        Role[oc_configure Role]
        Module[oc_configure Module]
    end
    
    subgraph "Module Utilities"
        DsmadmcAdapter[DsmadmcAdapter]
        AnsibleModule[AnsibleModule Base]
    end
    
    subgraph "Target Host"
        SystemCtl[systemctl]
        OCService[opscenter.service]
        Dsmadmc[dsmadmc CLI]
        SPServer[Storage Protect Server]
    end
    
    Playbook --> Role
    Role --> Module
    Module --> DsmadmcAdapter
    DsmadmcAdapter --> AnsibleModule
    Module --> SystemCtl
    SystemCtl --> OCService
    DsmadmcAdapter --> Dsmadmc
    Dsmadmc --> SPServer
    
    style Playbook fill:#e1f5ff
    style Role fill:#fff4e1
    style Module fill:#ffe1f5
    style DsmadmcAdapter fill:#f0e1ff
    style OCService fill:#e1ffe1
```

### Component Relationships

```mermaid
classDiagram
    class oc_configure_playbook {
        +target_hosts: string
        +become: true
        +roles: list
    }
    
    class oc_configure_role {
        +admin_name: string
        +action: string
        +defaults: dict
    }
    
    class oc_configure_module {
        +admin_name: string
        +action: string
        +configure()
        +restart()
        +stop()
        +check_service_status()
    }
    
    class DsmadmcAdapter {
        +server_name: string
        +username: string
        +password: string
        +run_command()
        +find_one()
        +perform_action()
    }
    
    class AnsibleModule {
        +params: dict
        +run_command()
        +exit_json()
        +fail_json()
    }
    
    oc_configure_playbook --> oc_configure_role
    oc_configure_role --> oc_configure_module
    oc_configure_module --> DsmadmcAdapter
    oc_configure_module --> AnsibleModule
    DsmadmcAdapter --|> AnsibleModule
```

## Data Flow

### Configuration Flow

```mermaid
sequenceDiagram
    participant User
    participant Playbook
    participant Role
    participant Module
    participant DsmadmcAdapter
    participant SystemCtl
    participant SPServer
    
    User->>Playbook: Execute with action=configure
    Playbook->>Role: Invoke oc_configure role
    Role->>Module: Call oc_configure module
    Module->>SystemCtl: Check opscenter.service status
    SystemCtl-->>Module: Service status
    
    alt Service not found
        Module-->>User: Fail: OC not installed
    else Service exists
        Module->>DsmadmcAdapter: Initialize adapter
        DsmadmcAdapter->>SPServer: update admin sessionsecurity=transitional
        SPServer-->>DsmadmcAdapter: Command result
        DsmadmcAdapter-->>Module: Return result
        
        alt Success
            Module-->>User: Configuration complete
        else Failure
            Module-->>User: Fail: Configuration error
        end
    end
```

### Service Control Flow

```mermaid
sequenceDiagram
    participant User
    participant Playbook
    participant Role
    participant Module
    participant SystemCtl
    participant OCService
    
    User->>Playbook: Execute with action=restart/stop
    Playbook->>Role: Invoke oc_configure role
    Role->>Module: Call oc_configure module
    Module->>SystemCtl: Check opscenter.service status
    SystemCtl-->>Module: Service status
    
    alt Service not found
        Module-->>User: Fail: OC not installed
    else Service exists
        Module->>SystemCtl: systemctl [action] opscenter.service
        SystemCtl->>OCService: Execute action
        OCService-->>SystemCtl: Action result
        SystemCtl-->>Module: Command result
        
        alt Success
            Module-->>User: Action completed (changed=true)
        else Failure
            Module-->>User: Fail: Action error
        end
    end
```

## Component Details

### 1. Playbook Layer

**File**: [`playbooks/oc_configure_playbook.yml`](../../playbooks/oc_configure_playbook.yml)

```yaml
Purpose: Entry point for OC operations
Features:
  - Dynamic host targeting via target_hosts variable
  - Privilege escalation (become: true)
  - Role-based execution
```

### 2. Role Layer

**Path**: [`roles/oc_configure/`](../../roles/oc_configure/)

#### Structure
```
roles/oc_configure/
├── README.md           # Role documentation
├── defaults/main.yml   # Default variables
├── meta/main.yml       # Role metadata
└── tasks/main.yml      # Main task file
```

#### Default Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `admin_name` | "" | OC admin username (required for configure action) |
| `action` | "configure" | Action to perform (configure/restart/stop) |

#### Tasks
- Invokes [`oc_configure`](../../plugins/modules/oc_configure.py) module with parameters

### 3. Module Layer

**File**: [`plugins/modules/oc_configure.py`](../../plugins/modules/oc_configure.py)

#### Module Parameters

| Parameter | Type | Required | Choices | Description |
|-----------|------|----------|---------|-------------|
| `admin_name` | string | Conditional* | - | Admin user of the hub server |
| `action` | string | Yes | configure, restart, stop | Action to perform |

*Required when action is 'configure'

#### Module Operations

##### Configure Action
1. Validates `admin_name` is provided
2. Checks if `opscenter.service` exists via systemctl
3. Uses [`DsmadmcAdapter`](../../plugins/module_utils/dsmadmc_adapter.py) to execute:
   ```
   update admin {admin_name} sessionsecurity=transitional
   ```
4. Returns success message with OC access URL

##### Restart/Stop Actions
1. Checks if `opscenter.service` exists via systemctl
2. Executes: `systemctl [action] opscenter.service`
3. Returns result with changed status

#### Error Handling
- Service not found: Fails with "OC is not installed or service is not registered"
- Configuration failure: Returns dsmadmc command output
- Service control failure: Returns systemctl error details

### 4. Utility Layer

**File**: [`plugins/module_utils/dsmadmc_adapter.py`](../../plugins/module_utils/dsmadmc_adapter.py)

#### DsmadmcAdapter Class

Extends `AnsibleModule` to provide Storage Protect CLI integration.

##### Authentication Parameters
| Parameter | Environment Variable | Description |
|-----------|---------------------|-------------|
| `server_name` | `STORAGE_PROTECT_SERVERNAME` | Server name (default: 'local') |
| `username` | `STORAGE_PROTECT_USERNAME` | Admin username |
| `password` | `STORAGE_PROTECT_PASSWORD` | Admin password |
| `request_timeout` | `STORAGE_PROTECT_REQUEST_TIMEOUT` | Timeout in seconds (default: 10) |

##### Key Methods

###### `run_command(command, auto_exit=True, dataonly=True, exit_on_fail=True)`
- Constructs and executes dsmadmc commands
- Format: `dsmadmc -servername={server} -id={user} -pass={pass} [-dataonly=yes] {command}`
- Handles return codes:
  - 0: Success
  - 10: No changes needed (idempotent)
  - Other: Error

###### `find_one(object_type, name, fail_on_not_found=False)`
- Queries for specific Storage Protect objects
- Returns existence status and object details

###### `perform_action(action, object_type, object_identifier, options='', exists=False, existing=None, auto_exit=True)`
- Performs CRUD operations on Storage Protect objects
- Implements idempotency checking
- Handles object lifecycle management

## Execution Flow

### Complete Workflow

```mermaid
flowchart TD
    Start([User Executes Playbook]) --> LoadVars[Load Variables]
    LoadVars --> TargetHosts{Target Hosts<br/>Specified?}
    TargetHosts -->|No| UseAll[Use 'all' hosts]
    TargetHosts -->|Yes| UseSpecified[Use specified hosts]
    UseAll --> InvokeRole[Invoke oc_configure Role]
    UseSpecified --> InvokeRole
    
    InvokeRole --> LoadDefaults[Load Default Variables]
    LoadDefaults --> CallModule[Call oc_configure Module]
    
    CallModule --> CheckAction{Action Type?}
    
    CheckAction -->|configure| ValidateAdmin{admin_name<br/>provided?}
    ValidateAdmin -->|No| FailAdmin[Fail: admin_name required]
    ValidateAdmin -->|Yes| CheckService1[Check opscenter.service]
    
    CheckAction -->|restart/stop| CheckService2[Check opscenter.service]
    
    CheckService1 --> ServiceExists1{Service<br/>Exists?}
    CheckService2 --> ServiceExists2{Service<br/>Exists?}
    
    ServiceExists1 -->|No| FailService1[Fail: OC not installed]
    ServiceExists2 -->|No| FailService2[Fail: OC not installed]
    
    ServiceExists1 -->|Yes| InitAdapter[Initialize DsmadmcAdapter]
    InitAdapter --> UpdateAdmin[Update admin sessionsecurity]
    UpdateAdmin --> ConfigResult{Success?}
    ConfigResult -->|Yes| SuccessConfig[Return: Configuration complete]
    ConfigResult -->|No| FailConfig[Fail: Configuration error]
    
    ServiceExists2 -->|Yes| SystemCtl[Execute systemctl action]
    SystemCtl --> ServiceResult{Success?}
    ServiceResult -->|Yes| SuccessService[Return: Action completed]
    ServiceResult -->|No| FailService[Fail: Service action error]
    
    SuccessConfig --> End([End])
    SuccessService --> End
    FailAdmin --> End
    FailService1 --> End
    FailService2 --> End
    FailConfig --> End
    FailService --> End
    
    style Start fill:#e1f5ff
    style End fill:#e1ffe1
    style FailAdmin fill:#ffe1e1
    style FailService1 fill:#ffe1e1
    style FailService2 fill:#ffe1e1
    style FailConfig fill:#ffe1e1
    style FailService fill:#ffe1e1
    style SuccessConfig fill:#e1ffe1
    style SuccessService fill:#e1ffe1
```

## Usage Examples

### Configure Operations Center

```bash
# Set environment variables
export STORAGE_PROTECT_SERVERNAME="your_server_name"
export STORAGE_PROTECT_USERNAME="your_username"
export STORAGE_PROTECT_PASSWORD="your_password"

# Execute configuration
ansible-playbook -i inventory.ini \
  ibm.storage_protect.oc_configure_playbook.yml \
  -e @vars.yml
```

**vars.yml**:
```yaml
admin_name: "tsmuser1"
action: "configure"
target_hosts: "oc_servers"
```

### Stop Operations Center

```bash
ansible-playbook -i inventory.ini \
  ibm.storage_protect.oc_configure_playbook.yml \
  -e 'action=stop'
```

### Restart Operations Center

```bash
ansible-playbook -i inventory.ini \
  ibm.storage_protect.oc_configure_playbook.yml \
  -e 'action=restart'
```

## Integration Points

### Storage Protect Server Integration

```mermaid
graph LR
    subgraph "OC Configuration"
        OCModule[oc_configure Module]
        DsmadmcAdapter[DsmadmcAdapter]
    end
    
    subgraph "Storage Protect Server"
        AdminDB[(Admin Database)]
        SessionMgr[Session Manager]
        OCApp[OC Application]
    end
    
    OCModule --> DsmadmcAdapter
    DsmadmcAdapter -->|update admin| AdminDB
    AdminDB -->|sessionsecurity=transitional| SessionMgr
    SessionMgr -->|Enable OC Access| OCApp
    
    style OCModule fill:#ffe1f5
    style DsmadmcAdapter fill:#f0e1ff
    style AdminDB fill:#e1ffe1
```

### System Service Integration

```mermaid
graph TB
    subgraph "Ansible Module"
        OCModule[oc_configure Module]
    end
    
    subgraph "System Layer"
        SystemCtl[systemctl]
        SystemD[systemd]
    end
    
    subgraph "OC Service"
        OCService[opscenter.service]
        OCProcess[OC Process]
        WebServer[Web Server]
    end
    
    OCModule -->|systemctl commands| SystemCtl
    SystemCtl --> SystemD
    SystemD --> OCService
    OCService --> OCProcess
    OCProcess --> WebServer
    
    style OCModule fill:#ffe1f5
    style SystemCtl fill:#fff4e1
    style OCService fill:#e1ffe1
```

## Requirements

### Prerequisites
1. IBM Storage Protect Operations Center must be installed
2. `opscenter.service` must be registered with systemd
3. Storage Protect client must be installed and registered with the server
4. Valid admin credentials with appropriate permissions

### Environment Variables
```bash
STORAGE_PROTECT_SERVERNAME  # Server name (default: 'local')
STORAGE_PROTECT_USERNAME    # Admin username
STORAGE_PROTECT_PASSWORD    # Admin password
STORAGE_PROTECT_REQUEST_TIMEOUT  # Optional timeout in seconds
```

### Permissions
- Root or sudo access on target hosts (become: true)
- Storage Protect admin privileges for configuration actions
- systemctl permissions for service management

## Error Scenarios

### Common Errors and Resolutions

| Error | Cause | Resolution |
|-------|-------|------------|
| "OC is not installed or service is not registered" | opscenter.service not found | Install OC or register service with systemd |
| "'admin_name' is required when action is 'configure'" | Missing admin_name parameter | Provide admin_name in variables |
| "Failed to configure the OC" | dsmadmc command failed | Check admin credentials and permissions |
| "Failed to restart/stop the OC" | systemctl command failed | Check service status and system logs |

## Testing

**Test File**: [`tests/integration/targets/oc_configure/test_oc_configure.yml`](../../tests/integration/targets/oc_configure/test_oc_configure.yml)

### Test Coverage
- Service status verification
- Configuration action execution
- Service control actions (restart/stop)
- Error handling validation

## Security Considerations

1. **Credential Management**
   - Passwords stored in environment variables
   - No logging of sensitive parameters (no_log: true)
   - Credentials passed via secure channels

2. **Session Security**
   - Sets `sessionsecurity=transitional` for OC access
   - Enables secure communication between OC and Storage Protect server

3. **Access Control**
   - Requires admin-level privileges
   - Service operations require root/sudo access
   - OC accessible via HTTPS

## Performance Considerations

- **Idempotency**: Module checks current state before making changes
- **Timeout Handling**: Configurable request timeout (default: 10 seconds)
- **Service Management**: Uses systemctl for efficient service control
- **Command Execution**: Direct subprocess calls for minimal overhead

## Future Enhancements

1. **Configuration Options**
   - Support for additional OC configuration parameters
   - Custom port and hostname configuration
   - SSL/TLS certificate management

2. **Monitoring Integration**
   - Health check capabilities
   - Status reporting
   - Log aggregation

3. **Multi-Server Support**
   - Hub server configuration
   - Spoke server management
   - Distributed OC deployment

## References

- [IBM Storage Protect Operations Center Documentation](https://www.ibm.com/docs/en/storage-protect)
- [Ansible Module Development](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html)
- [systemd Service Management](https://www.freedesktop.org/software/systemd/man/systemctl.html)

## Related Components

- [`sp_server_install`](design-sp-server.md) - Storage Protect Server installation
- [`ba_client_install`](design-ba-client.md) - Backup-Archive client installation
- [`dsmadmc_adapter`](../../plugins/module_utils/dsmadmc_adapter.py) - CLI adapter utility

---

**Document Version**: 1.0  
**Last Updated**: 2026-03-26  
**Author**: Reverse-engineered from codebase
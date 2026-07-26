# IBM Storage Protect Storage Agent Configuration Design

## Overview

The Storage Agent configuration component provides Ansible automation for configuring IBM Storage Protect Storage Agents to enable LAN-Free backup operations. A Storage Agent acts as a data mover that allows client nodes to back up data directly to tape or other storage devices without sending the data through the Storage Protect server, significantly reducing network traffic and improving backup performance.

## Storage Agent Concept

### What is a Storage Agent?

According to [IBM Documentation](https://www.ibm.com/docs/en/tsmfsan/7.1.1?topic=storage-agent-overview), a Storage Agent is a licensed program that moves data between a client node and local storage devices (such as tape drives or libraries) on behalf of the Storage Protect server. This enables **LAN-Free data movement**, where backup and restore operations bypass the LAN and communicate directly with storage devices through SCSI or Fibre Channel connections.

### Key Benefits

1. **Reduced Network Load**: Data flows directly from client to storage device
2. **Improved Performance**: Eliminates server bottleneck for data transfer
3. **Scalability**: Distributes data movement across multiple storage agents
4. **Efficient Resource Utilization**: Offloads data movement from the server

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Ansible Control Node"
        Playbook[storage_agent_configure_playbook.yml]
        Role[storage_agent_configure Role]
        Module[storage_agent_config Module]
    end
    
    subgraph "Module Utilities"
        SPUtils[StorageProtectUtils]
        DsmadmcAdapter[DsmadmcAdapter]
        AnsibleModule[AnsibleModule Base]
    end
    
    subgraph "Target Host - Storage Agent Node"
        BAClient[BA Client]
        StgAgent[Storage Agent Process]
        DsmstaOpt[dsmsta.opt]
        DsmSys[dsm.sys]
        TapeDevice[Tape Device/Library]
    end
    
    subgraph "Storage Protect Server"
        SPServer[SP Server]
        ServerDB[(Server Database)]
        PolicyEngine[Policy Engine]
        StoragePool[Storage Pool]
    end
    
    Playbook --> Role
    Role --> Module
    Module --> SPUtils
    Module --> DsmadmcAdapter
    SPUtils --> AnsibleModule
    DsmadmcAdapter --> AnsibleModule
    
    Module --> BAClient
    Module --> StgAgent
    Module --> DsmstaOpt
    Module --> DsmSys
    
    DsmadmcAdapter --> SPServer
    SPServer --> ServerDB
    SPServer --> PolicyEngine
    StgAgent --> TapeDevice
    TapeDevice --> StoragePool
    
    style Playbook fill:#e1f5ff
    style Role fill:#fff4e1
    style Module fill:#ffe1f5
    style StgAgent fill:#e1ffe1
    style TapeDevice fill:#ffe1e1
```

### LAN-Free Data Flow

```mermaid
graph LR
    subgraph "Client Node"
        ClientApp[Client Application]
        BAClient[BA Client]
    end
    
    subgraph "Storage Agent Node"
        StgAgent[Storage Agent]
        TapeLib[Tape Library]
    end
    
    subgraph "Storage Protect Server"
        SPServer[SP Server]
        MetaDB[(Metadata DB)]
    end
    
    ClientApp -->|1. Backup Request| BAClient
    BAClient -->|2. Control Info| SPServer
    SPServer -->|3. LAN-Free Path| BAClient
    BAClient -.->|4. Data Stream| StgAgent
    StgAgent -->|5. Write Data| TapeLib
    StgAgent -->|6. Completion| SPServer
    SPServer -->|7. Update Metadata| MetaDB
    
    style ClientApp fill:#e1f5ff
    style StgAgent fill:#e1ffe1
    style TapeLib fill:#ffe1e1
    style SPServer fill:#fff4e1
```

### Component Relationships

```mermaid
classDiagram
    class storage_agent_configure_playbook {
        +target_hosts: string
        +become: true
        +environment: dict
        +roles: list
        +vars: dict
    }
    
    class storage_agent_configure_role {
        +stg_agent_name: string
        +stg_agent_password: string
        +validate_lan_free: bool
        +defaults: dict
        +tasks: list
    }
    
    class storage_agent_config_module {
        +stg_agent_name: string
        +stg_agent_password: string
        +server_parameters: dict
        +path_parameters: dict
        +copygroup_parameters: dict
        +configure()
        +validate_lanfree()
        +setup_server_communication()
        +configure_files()
    }
    
    class StorageProtectUtils {
        +module: AnsibleModule
        +server_component_check()
        +rpm_package_check()
    }
    
    class DsmadmcAdapter {
        +server_name: string
        +username: string
        +password: string
        +run_command()
        +find_one()
        +perform_action()
    }
    
    storage_agent_configure_playbook --> storage_agent_configure_role
    storage_agent_configure_role --> storage_agent_config_module
    storage_agent_config_module --> StorageProtectUtils
    storage_agent_config_module --> DsmadmcAdapter
    StorageProtectUtils --> AnsibleModule
    DsmadmcAdapter --> AnsibleModule
```

## Data Flow

### Configuration Flow

```mermaid
sequenceDiagram
    participant User
    participant Playbook
    participant Role
    participant Module
    participant SPUtils
    participant DsmadmcAdapter
    participant SPServer
    participant Files
    participant StgAgent
    
    User->>Playbook: Execute with configuration vars
    Playbook->>Role: Invoke storage_agent_configure
    Role->>Module: Call storage_agent_config module
    
    Module->>SPUtils: Check Storage Agent installation
    SPUtils-->>Module: Installation verified
    
    Module->>SPUtils: Check BA Client installation
    SPUtils-->>Module: BA Client verified
    
    Module->>Module: Kill existing dsmsta process
    Module->>Module: Copy dsmsta.opt.smp to dsmsta.opt
    
    Module->>DsmadmcAdapter: Initialize adapter
    
    Note over Module,SPServer: Server Configuration Phase
    Module->>DsmadmcAdapter: DEFINE SERVER (storage agent)
    DsmadmcAdapter->>SPServer: Execute define server command
    SPServer-->>DsmadmcAdapter: Server defined
    
    Module->>DsmadmcAdapter: DEFINE PATH (SCSI path)
    DsmadmcAdapter->>SPServer: Execute define path command
    SPServer-->>DsmadmcAdapter: Path defined
    
    Module->>DsmadmcAdapter: DEFINE COPYGROUP (LAN-Free policy)
    DsmadmcAdapter->>SPServer: Execute define copygroup command
    SPServer-->>DsmadmcAdapter: Copygroup defined
    
    Module->>DsmadmcAdapter: ACTIVATE POLICYSET
    DsmadmcAdapter->>SPServer: Execute activate policyset command
    SPServer-->>DsmadmcAdapter: Policyset activated
    
    Note over Module,SPServer: Server-to-Server Communication
    Module->>DsmadmcAdapter: SET SERVERNAME
    Module->>DsmadmcAdapter: SET SERVERHLADDRESS
    Module->>DsmadmcAdapter: SET SERVERPASSWORD
    Module->>DsmadmcAdapter: SET SERVERLLADDRESS
    DsmadmcAdapter->>SPServer: Configure server communication
    SPServer-->>DsmadmcAdapter: Communication configured
    
    Note over Module,Files: Local Configuration Phase
    Module->>Module: Execute setstorageserver command
    Module->>Files: Update dsmsta.opt
    Files-->>Module: dsmsta.opt updated
    
    Module->>Files: Update dsm.sys (client config)
    Files-->>Module: dsm.sys updated
    
    Module-->>User: Configuration Complete
```

### Validation Flow

```mermaid
sequenceDiagram
    participant User
    participant Playbook
    participant Role
    participant Module
    participant StgAgent
    participant DsmadmcAdapter
    participant SPServer
    
    User->>Playbook: Execute with validate_lan_free=true
    Playbook->>Role: Invoke storage_agent_configure
    Role->>Module: Call storage_agent_config (validation mode)
    
    Module->>Module: Validate parameters (node_name, stg_agent_name)
    
    Module->>StgAgent: Start storage agent process (nohup dsmsta)
    StgAgent-->>Module: Agent started
    
    loop Retry max_attempts times
        Module->>DsmadmcAdapter: VALIDATE LANFREE node agent
        DsmadmcAdapter->>SPServer: Execute validate lanfree command
        SPServer->>SPServer: Check LAN-Free path
        SPServer->>SPServer: Verify storage agent connection
        SPServer->>SPServer: Test data path
        SPServer-->>DsmadmcAdapter: Validation result
        DsmadmcAdapter-->>Module: Return result
    end
    
    Module-->>User: Validation Complete with results
```

### Complete Workflow

```mermaid
flowchart TD
    Start([User Executes Playbook]) --> LoadVars[Load Variables & Environment]
    LoadVars --> CheckMode{validate_lan_free?}
    
    CheckMode -->|false - Configure| CheckInstall[Check Installations]
    CheckMode -->|true - Validate| ValidateParams{Parameters Valid?}
    
    CheckInstall --> CheckStgAgent[Check Storage Agent via IMCL]
    CheckStgAgent --> StgAgentOK{Installed?}
    StgAgentOK -->|No| FailStgAgent[Fail: Storage Agent not installed]
    StgAgentOK -->|Yes| CheckBAClient[Check BA Client via RPM]
    
    CheckBAClient --> BAClientOK{Installed?}
    BAClientOK -->|No| FailBAClient[Fail: BA Client not installed]
    BAClientOK -->|Yes| KillProcess[Kill existing dsmsta process]
    
    KillProcess --> CopyOpt[Copy dsmsta.opt.smp to dsmsta.opt]
    CopyOpt --> InitAdapter[Initialize DsmadmcAdapter]
    
    InitAdapter --> DefineServer[DEFINE SERVER on SP Server]
    DefineServer --> DefinePath[DEFINE PATH for SCSI device]
    DefinePath --> DefineCopygroup[DEFINE COPYGROUP for LAN-Free]
    DefineCopygroup --> ActivatePolicy[ACTIVATE POLICYSET]
    
    ActivatePolicy --> SetupComm[Setup Server-to-Server Communication]
    SetupComm --> SetServerName[SET SERVERNAME]
    SetServerName --> SetHLAddr[SET SERVERHLADDRESS]
    SetHLAddr --> SetPassword[SET SERVERPASSWORD]
    SetPassword --> SetLLAddr[SET SERVERLLADDRESS]
    
    SetLLAddr --> RunSetStorage[Execute setstorageserver command]
    RunSetStorage --> SetStorageOK{Success?}
    SetStorageOK -->|No| FailSetStorage[Fail: setstorageserver failed]
    SetStorageOK -->|Yes| UpdateDsmstaOpt[Update dsmsta.opt file]
    
    UpdateDsmstaOpt --> UpdateDsmSys[Update dsm.sys file]
    UpdateDsmSys --> ConfigComplete[Configuration Complete]
    
    ValidateParams -->|No| FailValidateParams[Fail: Missing parameters]
    ValidateParams -->|Yes| StartAgent[Start Storage Agent Process]
    
    StartAgent --> AgentStarted{Started?}
    AgentStarted -->|No| FailAgentStart[Fail: Cannot start agent]
    AgentStarted -->|Yes| RetryLoop[Retry Loop: max_attempts]
    
    RetryLoop --> ValidateLanFree[Execute VALIDATE LANFREE command]
    ValidateLanFree --> MoreAttempts{More attempts?}
    MoreAttempts -->|Yes| ValidateLanFree
    MoreAttempts -->|No| ValidationComplete[Validation Complete]
    
    ConfigComplete --> End([End])
    ValidationComplete --> End
    FailStgAgent --> End
    FailBAClient --> End
    FailSetStorage --> End
    FailValidateParams --> End
    FailAgentStart --> End
    
    style Start fill:#e1f5ff
    style End fill:#e1ffe1
    style FailStgAgent fill:#ffe1e1
    style FailBAClient fill:#ffe1e1
    style FailSetStorage fill:#ffe1e1
    style FailValidateParams fill:#ffe1e1
    style FailAgentStart fill:#ffe1e1
    style ConfigComplete fill:#e1ffe1
    style ValidationComplete fill:#e1ffe1
```

## Component Details

### 1. Playbook Layer

**File**: [`playbooks/storage_agent_configure_playbook.yml`](../../playbooks/storage_agent_configure_playbook.yml)

```yaml
Purpose: Entry point for Storage Agent configuration and validation
Features:
  - Two-phase execution: Configuration and Validation
  - Dynamic host targeting via target_hosts variable
  - Environment variable support for credentials
  - Comprehensive variable configuration
```

### 2. Role Layer

**Path**: [`roles/storage_agent_configure/`](../../roles/storage_agent_configure/)

#### Structure
```
roles/storage_agent_configure/
├── README.md                           # Role documentation
├── defaults/main.yml                   # Default variables
├── meta/main.yml                       # Role metadata
└── tasks/
    ├── main.yml                        # Main task dispatcher
    ├── storage_agent_configure.yml     # Configuration tasks
    └── lanfree_client_validation.yml   # Validation tasks
```

#### Default Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `stg_agent_name` | "" | Storage Agent name on server |
| `stg_agent_password` | "" | Storage Agent password |
| `stg_agent_server_name` | "" | Server name where agent is defined |
| `stg_agent_hl_add` | "" | High-level address of agent host |
| `lladdress` | "1502" | Low-level address (LAN-Free port) |
| `server_tcp_port` | "1500" | Server TCP/IP port |
| `server_hl_address` | "" | Server high-level address |
| `server_password` | "" | Server-to-server password |
| `stg_agent_path_name` | "" | SCSI path name (e.g., "drv1") |
| `stg_agent_path_dest` | "drive" | Path destination type (drive/library) |
| `library` | "" | Tape library name |
| `device` | "" | Device path (e.g., "/dev/sg1") |
| `copygroup_domain` | "" | Policy domain for LAN-Free |
| `copygroup_policyset` | "" | Policy set name |
| `copygroup_mngclass` | "" | Management class |
| `copygroup_destination` | "" | Storage pool destination |
| `validate_lan_free` | false | Enable validation mode |
| `node_name` | "" | Client node name for validation |
| `stg_pool` | "" | Storage pool name |
| `max_attempts` | 3 | Validation retry attempts |

### 3. Module Layer

**File**: [`plugins/modules/storage_agent_config.py`](../../plugins/modules/storage_agent_config.py)

#### Module Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `stg_agent_name` | string | Yes | - | Storage Agent name |
| `stg_agent_password` | string | Conditional* | - | Storage Agent password |
| `stg_agent_server_name` | string | Conditional* | - | Server name |
| `stg_agent_hl_add` | string | Conditional* | - | Agent high-level address |
| `lladdress` | string | Conditional* | - | LAN-Free port |
| `server_tcp_port` | string | Conditional* | - | Server TCP port |
| `server_hl_address` | string | Conditional* | - | Server address |
| `server_password` | string | Conditional* | - | Server password |
| `stg_agent_path_name` | string | Conditional* | - | SCSI path name |
| `stg_agent_path_dest` | string | Conditional* | "drive" | Path destination type |
| `library` | string | Conditional* | - | Library name |
| `device` | string | Conditional* | - | Device path |
| `copygroup_domain` | string | Conditional* | - | Policy domain |
| `copygroup_policyset` | string | Conditional* | - | Policy set |
| `copygroup_mngclass` | string | Conditional* | - | Management class |
| `copygroup_destination` | string | Conditional* | - | Storage pool |
| `stg_pool` | string | Conditional* | - | Storage pool name |
| `validate_lan_free` | bool | No | false | Enable validation mode |
| `node_name` | string | Conditional** | - | Client node name |
| `max_attempts` | int | No | 3 | Validation retry count |
| `client_options_file_path` | string | No | /opt/tivoli/tsm/client/ba/bin/dsm.sys | Client config path |
| `stg_agent_options_file_path` | string | No | /opt/tivoli/tsm/StorageAgent/bin/dsmsta.opt | Agent config path |
| `stg_agent_bin_dir` | string | No | /opt/tivoli/tsm/StorageAgent/bin | Agent binary directory |
| `start_stg_agent` | bool | No | true | Start agent after config |
| `imcl_path` | string | No | /opt/IBM/InstallationManager/eclipse/tools/imcl | IMCL path |

*Required when `validate_lan_free` is false  
**Required when `validate_lan_free` is true

#### Module Operations

##### Configuration Mode (`validate_lan_free=false`)

**Phase 1: Prerequisites Check**
1. Verify Storage Agent installation via IMCL
2. Verify BA Client installation via RPM
3. Kill any existing dsmsta process
4. Copy `dsmsta.opt.smp` to `dsmsta.opt`

**Phase 2: Server Configuration**
```python
# Define Storage Agent as a server on SP Server
DEFINE SERVER {stg_agent_name} 
  SERVERPASSWORD={stg_agent_password} 
  HLADDRESS={stg_agent_hl_add} 
  LLADDRESS={lladdress} 
  SSL=YES

# Define SCSI path for storage device
DEFINE PATH {stg_agent_name} {stg_agent_path_name} 
  SRCTYPE=SERVER 
  DESTTYPE={stg_agent_path_dest} 
  LIBRARY={library} 
  DEVICE={device}

# Define LAN-Free copy group
DEFINE COPYGROUP {copygroup_domain} {copygroup_policyset} 
  {copygroup_mngclass} 
  TYPE=BACKUP 
  DESTINATION={stg_pool}

# Activate policy set
ACTIVATE POLICYSET {copygroup_domain} {copygroup_policyset}
```

**Phase 3: Server-to-Server Communication**
```python
SET SERVERNAME {stg_agent_server_name}
SET SERVERHLADDRESS {server_hl_address}
SET SERVERPASSWORD {server_password}
SET SERVERLLADDRESS {lladdress}
```

**Phase 4: Local Configuration**
```bash
# Configure storage agent
./dsmsta setstorageserver 
  myname={stg_agent_name} 
  mypassword={stg_agent_password} 
  myhladdress={stg_agent_hl_add} 
  servername={stg_agent_server_name} 
  serverpassword={server_password} 
  hladdress={server_hl_address} 
  lladdress={server_tcp_port} 
  ssl=yes
```

**Phase 5: File Updates**

`dsmsta.opt`:
```
Servername {stg_agent_server_name}
COMMmethod TCPip
TCPPort {server_tcp_port}
SSLTCPPort {server_tcp_port}
SSLTCPadminPort {lladdress}
DEVCONFIG devconfig.txt
```

`dsm.sys`:
```
Servername {stg_agent_server_name}
LANfreeCOMMmethod tcpip
enablelanfree yes
lanfreetcpserveraddress {server_hl_address}
lanfreetcpport {lladdress}
TCPServeraddress {server_hl_address}
```

##### Validation Mode (`validate_lan_free=true`)

1. Validate required parameters (`node_name`, `stg_agent_name`)
2. Start storage agent process: `nohup dsmsta > dsmsta.log 2>&1 &`
3. Retry validation up to `max_attempts` times:
   ```
   VALIDATE LANFREE {node_name} {stg_agent_name}
   ```
4. Return validation results

### 4. Utility Layer

#### StorageProtectUtils

**File**: [`plugins/module_utils/sp_utils.py`](../../plugins/module_utils/sp_utils.py)

##### Methods

###### `server_component_check(imcl_path, package_prefix)`
- Verifies Storage Agent installation via IBM Installation Manager
- Executes: `{imcl_path} listinstalledpackages`
- Searches for package prefix: `com.tivoli.dsm.stagent_`
- Fails if component not found

###### `rpm_package_check(package_name)`
- Verifies BA Client installation via RPM
- Executes: `rpm -q {package_name}`
- Checks for package: `TIVsm-BA`
- Fails if package not installed

#### DsmadmcAdapter

**File**: [`plugins/module_utils/dsmadmc_adapter.py`](../../plugins/module_utils/dsmadmc_adapter.py)

Provides Storage Protect CLI integration for executing administrative commands. See [OC Design](design-oc.md#dsmadmcadapter-class) for detailed documentation.

## LAN-Free Architecture

### Traditional vs LAN-Free Backup

```mermaid
graph TB
    subgraph "Traditional Backup (LAN-Based)"
        Client1[Client Node]
        Server1[SP Server]
        Storage1[Storage Pool]
        
        Client1 -->|Data over LAN| Server1
        Server1 -->|Write| Storage1
    end
    
    subgraph "LAN-Free Backup"
        Client2[Client Node]
        Server2[SP Server]
        StgAgent2[Storage Agent]
        Storage2[Storage Pool]
        
        Client2 -.->|Metadata only| Server2
        Client2 -->|Data via SCSI/FC| StgAgent2
        StgAgent2 -->|Direct Write| Storage2
        Server2 -.->|Control| StgAgent2
    end
    
    style Client1 fill:#ffe1e1
    style Server1 fill:#fff4e1
    style Client2 fill:#e1ffe1
    style StgAgent2 fill:#e1ffe1
```

### Storage Agent Communication Paths

```mermaid
graph TB
    subgraph "Client Node"
        BAClient[BA Client<br/>dsm.sys configured]
    end
    
    subgraph "Storage Agent Node"
        StgAgent[Storage Agent<br/>dsmsta process]
        DsmstaOpt[dsmsta.opt]
        TapeDevice[Tape Device<br/>/dev/sg1]
    end
    
    subgraph "Storage Protect Server"
        SPServer[SP Server]
        ServerDB[(Server Database)]
        PolicyDB[(Policy Database)]
    end
    
    BAClient -->|1. Control Channel<br/>TCP Port 1500| SPServer
    SPServer -->|2. LAN-Free Path Info| BAClient
    BAClient -->|3. Data Channel<br/>TCP Port 1502| StgAgent
    StgAgent -->|4. SCSI/FC| TapeDevice
    StgAgent -->|5. Status Updates<br/>TCP Port 1500| SPServer
    SPServer -->|6. Metadata| ServerDB
    SPServer -->|7. Policy Info| PolicyDB
    DsmstaOpt -.->|Configuration| StgAgent
    
    style BAClient fill:#e1f5ff
    style StgAgent fill:#e1ffe1
    style TapeDevice fill:#ffe1e1
    style SPServer fill:#fff4e1
```

## Configuration Files

### dsmsta.opt (Storage Agent Options)

```ini
# Server connection parameters
Servername SERVER2
COMMmethod TCPip
TCPPort 1500
SSLTCPPort 1500
SSLTCPadminPort 1502
DEVCONFIG devconfig.txt
```

**Purpose**: Configures how the storage agent connects to the Storage Protect server.

### dsm.sys (Client System Options)

```ini
# LAN-Free configuration for BA Client
Servername SERVER2
LANfreeCOMMmethod tcpip
enablelanfree yes
lanfreetcpserveraddress 9.47.89.61
lanfreetcpport 1502
TCPServeraddress 9.47.89.61
```

**Purpose**: Enables LAN-Free backup for the BA Client and specifies storage agent connection details.

## Usage Examples

### Complete Configuration

```bash
# Set environment variables
export STORAGE_PROTECT_SERVERNAME="server2"
export STORAGE_PROTECT_USERNAME="tsmuser1"
export STORAGE_PROTECT_PASSWORD="tsmuser1@@123456789"

# Execute configuration playbook
ansible-playbook -i inventory.ini \
  ibm.storage_protect.storage_agent_configure_playbook.yml \
  -e @storage_agent_vars.yml
```

**storage_agent_vars.yml**:
```yaml
target_hosts: "storage_agent_nodes"
stg_agent_name: "stgagent16"
stg_agent_password: "STGAGENT@123456789"
stg_agent_server_name: "server2"
stg_agent_hl_add: "9.11.69.158"
lladdress: "1502"
server_tcp_port: "1500"
server_hl_address: "9.47.89.61"
server_password: "ServerPassword@@12345"
stg_agent_path_name: "drv1"
stg_agent_path_dest: "drive"
library: "MSLG3LIB"
device: "/dev/sg1"
copygroup_domain: "lanfreedomain"
copygroup_policyset: "standard"
copygroup_mngclass: "LANFREEMGMT"
copygroup_destination: "LANFREEPOOL"
stg_pool: "LANFREEPOOL"
node_name: "lanfreeclient"
validate_lan_free: false
```

### LAN-Free Validation

```bash
ansible-playbook -i inventory.ini \
  ibm.storage_protect.storage_agent_configure_playbook.yml \
  -e "validate_lan_free=true" \
  -e "node_name=lanfreeclient" \
  -e "stg_agent_name=stgagent16" \
  -e "max_attempts=3"
```

## Integration Points

### Storage Protect Server Integration

```mermaid
graph TB
    subgraph "Configuration Module"
        Module[storage_agent_config]
        DsmadmcAdapter[DsmadmcAdapter]
    end
    
    subgraph "Storage Protect Server"
        ServerDef[Server Definition]
        PathDef[Path Definition]
        PolicyDef[Policy Definition]
        ServerComm[Server Communication]
    end
    
    subgraph "Server Database"
        ServerDB[(Server Objects)]
        PathDB[(Path Objects)]
        PolicyDB[(Policy Objects)]
    end
    
    Module --> DsmadmcAdapter
    DsmadmcAdapter -->|DEFINE SERVER| ServerDef
    DsmadmcAdapter -->|DEFINE PATH| PathDef
    DsmadmcAdapter -->|DEFINE COPYGROUP| PolicyDef
    DsmadmcAdapter -->|SET SERVER*| ServerComm
    
    ServerDef --> ServerDB
    PathDef --> PathDB
    PolicyDef --> PolicyDB
    
    style Module fill:#ffe1f5
    style DsmadmcAdapter fill:#f0e1ff
    style ServerDB fill:#e1ffe1
```

### File System Integration

```mermaid
graph LR
    subgraph "Module Operations"
        Module[storage_agent_config]
        SetStorage[setstorageserver command]
    end
    
    subgraph "Configuration Files"
        DsmstaOpt[dsmsta.opt]
        DsmSys[dsm.sys]
        DsmstaOptSmp[dsmsta.opt.smp]
    end
    
    subgraph "Processes"
        DsmstaProc[dsmsta process]
        BAClientProc[BA Client process]
    end
    
    Module -->|Copy| DsmstaOptSmp
    DsmstaOptSmp -.->|Template| DsmstaOpt
    Module -->|Execute| SetStorage
    SetStorage -->|Updates| DsmstaOpt
    Module -->|Write| DsmstaOpt
    Module -->|Write| DsmSys
    DsmstaOpt -.->|Config| DsmstaProc
    DsmSys -.->|Config| BAClientProc
    
    style Module fill:#ffe1f5
    style DsmstaOpt fill:#fff4e1
    style DsmSys fill:#fff4e1
```

## Prerequisites

### System Requirements

1. **Storage Agent Installation**
   - IBM Storage Protect Storage Agent must be installed
   - Verified via IBM Installation Manager (IMCL)
   - Package prefix: `com.tivoli.dsm.stagent_`

2. **BA Client Installation**
   - IBM Storage Protect Backup-Archive Client must be installed
   - Verified via RPM: `TIVsm-BA`
   - Client must be registered with Storage Protect server

3. **Storage Hardware**
   - SCSI or Fibre Channel tape library
   - Tape drives accessible from storage agent node
   - Device paths configured (e.g., `/dev/sg1`, `/dev/st0`)

4. **Network Configuration**
   - TCP/IP connectivity between client, storage agent, and server
   - Port 1500: Server communication
   - Port 1502: LAN-Free data transfer
   - Firewall rules configured appropriately

5. **Storage Protect Server**
   - LAN-Free capable storage pool created
   - Policy domain and management class defined
   - Server-to-server communication enabled

### Environment Variables

```bash
STORAGE_PROTECT_SERVERNAME  # Server name for dsmadmc
STORAGE_PROTECT_USERNAME    # Admin username
STORAGE_PROTECT_PASSWORD    # Admin password
```

### Permissions

- Root or sudo access on target hosts (become: true)
- Storage Protect admin privileges for server configuration
- File system write permissions for configuration files
- Device access permissions for tape devices

## Error Scenarios

### Common Errors and Resolutions

| Error | Cause | Resolution |
|-------|-------|------------|
| "Server component with prefix 'com.tivoli.dsm.stagent_' not found" | Storage Agent not installed | Install Storage Agent using sp_server_install role |
| "BA client package 'TIVsm-BA' is not installed" | BA Client not installed | Install BA Client using ba_client_install role |
| "Failed to copy dsmsta.opt.smp file" | Missing template file | Verify Storage Agent installation integrity |
| "setstorageserver command failed" | Invalid parameters or connectivity | Check network connectivity and parameter values |
| "Failed to update dsmsta.opt" | Permission denied | Verify write permissions on /opt/tivoli/tsm/StorageAgent/bin/ |
| "Failed to update dsm.sys" | Permission denied | Verify write permissions on /opt/tivoli/tsm/client/ba/bin/ |
| "For LAN-Free validation, both stg_agent_name and node_name must be provided" | Missing validation parameters | Provide both parameters when validate_lan_free=true |
| "Failed to start storage agent" | Process startup failure | Check dsmsta.log for errors, verify configuration |
| "VALIDATE LANFREE failed" | Path not configured or agent not running | Verify storage agent is running and paths are defined |

## Validation Process

### VALIDATE LANFREE Command

The `VALIDATE LANFREE` command verifies that:

1. **Client Node Configuration**
   - Node is registered with the server
   - Node is assigned to LAN-Free policy domain
   - Client has enablelanfree=yes in dsm.sys

2. **Storage Agent Configuration**
   - Storage agent is defined on server
   - Storage agent process is running
   - Communication paths are established

3. **SCSI Path Configuration**
   - Path is defined between storage agent and device
   - Device is accessible and operational
   - Library configuration is correct

4. **Policy Configuration**
   - Copy group is defined with LAN-Free destination
   - Policy set is activated
   - Storage pool is LAN-Free capable

### Validation Output

```
ANR2017I Administrator ADMIN issued command: VALIDATE LANFREE lanfreeclient stgagent16
ANR2280I LAN-free data transfer is enabled for node LANFREECLIENT.
ANR2281I Storage agent STGAGENT16 is available for LAN-free data transfer.
ANR2282I Path STGAGENT16 DRV1 is available for LAN-free data transfer.
ANR2283I LAN-free validation completed successfully.
```

## Performance Considerations

1. **Network Bandwidth**
   - LAN-Free reduces network traffic on primary LAN
   - Data flows directly between client and storage agent
   - Control traffic still uses primary network

2. **Storage Agent Capacity**
   - Multiple clients can share a storage agent
   - Agent capacity depends on tape drive speed
   - Consider multiple agents for high-volume environments

3. **Retry Mechanism**
   - Validation retries (`max_attempts`) allow agent startup time
   - Default 3 attempts with delays between retries
   - Adjust based on environment and agent startup time

4. **Concurrent Operations**
   - Multiple LAN-Free backups can run simultaneously
   - Limited by number of tape drives and paths
   - Configure sufficient paths for concurrent operations

## Security Considerations

1. **Password Management**
   - Storage agent password stored in configuration
   - Server-to-server password for authentication
   - Use Ansible Vault for sensitive variables

2. **SSL/TLS Communication**
   - SSL enabled for server-to-agent communication
   - Certificate validation recommended
   - Secure ports: 1500 (SSL), 1502 (SSL admin)

3. **Access Control**
   - Device permissions restrict tape access
   - File permissions protect configuration files
   - Admin privileges required for configuration

4. **Network Security**
   - Firewall rules for LAN-Free ports
   - Separate network segments recommended
   - Monitor for unauthorized access

## Troubleshooting

### Diagnostic Commands

```bash
# Check storage agent process
ps aux | grep dsmsta

# View storage agent log
tail -f /opt/tivoli/tsm/StorageAgent/bin/dsmsta.log

# Test storage agent connectivity
dsmadmc -id=admin -pa=password "q server stgagent16"

# Check SCSI paths
dsmadmc -id=admin -pa=password "q path * * srctype=server"

# Verify LAN-Free policy
dsmadmc -id=admin -pa=password "q copygroup lanfreedomain standard *"

# Test device access
ls -l /dev/sg1
```

### Log Files

| Log File | Location | Purpose |
|----------|----------|---------|
| dsmsta.log | /opt/tivoli/tsm/StorageAgent/bin/ | Storage agent operations |
| dsmsched.log | /var/log/tsm/ | Client scheduler log |
| dsmerror.log | /var/log/tsm/ | Client error log |
| actlog.log | SP Server | Server activity log |

## Future Enhancements

1. **Multi-Path Support**
   - Configure multiple SCSI paths per agent
   - Load balancing across paths
   - Failover capabilities

2. **Dynamic Path Discovery**
   - Automatic device detection
   - Path optimization
   - Health monitoring

3. **Advanced Validation**
   - Performance testing
   - Throughput measurement
   - Path quality assessment

4. **Configuration Templates**
   - Pre-defined configurations for common scenarios
   - Best practice templates
   - Environment-specific profiles

## References

- [IBM Storage Protect Storage Agent Overview](https://www.ibm.com/docs/en/tsmfsan/7.1.1?topic=storage-agent-overview)
- [Configuring LAN-Free Data Movement](https://www.ibm.com/docs/en/storage-protect/8.1.x?topic=data-configuring-lan-free-movement)
- [Storage Agent Installation](https://www.ibm.com/docs/en/storage-protect/8.1.x?topic=agent-installing-storage)
- [VALIDATE LANFREE Command](https://www.ibm.com/docs/en/storage-protect/8.1.x?topic=commands-validate-lanfree)

## Related Components

- [`sp_server_install`](design-sp-server.md) - Storage Protect Server installation
- [`ba_client_install`](design-ba-client.md) - Backup-Archive client installation
- [`dsmadmc_adapter`](../../plugins/module_utils/dsmadmc_adapter.py) - CLI adapter utility
- [`sp_utils`](../../plugins/module_utils/sp_utils.py) - Common utilities

---

**Document Version**: 1.0  
**Last Updated**: 2026-03-26  
**Author**: Reverse-engineered from codebase with IBM documentation reference
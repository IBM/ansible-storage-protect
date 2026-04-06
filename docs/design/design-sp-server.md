# IBM Storage Protect Server - Ansible Automation Design Document

## Introduction

This document captures the design of the Ansible modules for deploying, configuring, and managing IBM Storage Protect (SP) Server.

**Product Reference**: [IBM Storage Protect 8.1.27 Documentation](https://www.ibm.com/docs/en/storage-protect/8.1.27?topic=servers)

This design is based on IBM Storage Protect Product documentation version 8.1.27.

## Document Scope

This document describes:
- Python modules for SP Server
- Python module utilities for SP Server
- Ansible tasks and roles for SP Server
- Ansible playbooks for SP Server
- Component architecture and relationships
- Data flow and interaction patterns

### Supported Platforms

Based on IBM Storage Protect 8.1.27 product documentation and collection requirements:

**Operating Systems**:
- **Linux**: RHEL 7.x, 8.x, 9.x, SLES 12, 15, Ubuntu 18.04, 20.04, 22.04
- **AIX**: AIX 7.1, 7.2, 7.3
- **Windows**: Windows Server 2016, 2019, 2022

**Architectures**:
- **x86_64** (Intel/AMD 64-bit)
- **s390x** (IBM Z Systems)
- **ppc64le** (IBM Power Systems - Little Endian)

**IBM Storage Protect Versions**:
- Version 8.1.23 and higher
- Tested with version 8.1.27

**Ansible Requirements**:
- Ansible Core >= 2.15.0
- Python >= 3.9 on control node and managed nodes

### Lifecycle and Management Functions

- Server facts gathering
- Install and configure
- Upgrade
- Uninstall
- Certificate management
- Storage Pools management
- Policy management
- Node management
- Schedule management
- Storage Protect Resiliency

### Out of Scope

This design document does not cover:
- Storage Agent (separate component)
- BA Client (separate component)
- Operation Center (separate component)

---

## Architecture Overview

### High-Level Component Architecture

```mermaid
graph TB
    subgraph "Control Node"
        PB[Playbooks]
        ROLES[Ansible Roles]
        PB --> ROLES
    end
    
    subgraph "Ansible Collection: ibm.storage_protect"
        subgraph "Modules Layer"
            SPM[sp_server.py]
            SPCM[sp_server_configure.py]
            SPFM[sp_server_facts.py]
            NM[node.py]
            SM[schedule.py]
            OCM[oc_configure.py]
        end
        
        subgraph "Module Utils Layer"
            SPU[sp_server_utils.py]
            SPC[sp_server_constants.py]
            SPFU[sp_server_facts.py]
            DSMA[dsmadmc_adapter.py]
        end
        
        subgraph "Roles"
            SPI[sp_server_install]
            SPF[sp_server_facts]
            NODES[nodes]
            SCHED[schedules]
            OC[oc_configure]
        end
        
        ROLES --> SPI
        ROLES --> SPF
        ROLES --> NODES
        ROLES --> SCHED
        
        SPI --> SPM
        SPI --> SPCM
        SPF --> SPFM
        NODES --> NM
        SCHED --> SM
        OC --> OCM
        
        SPM --> SPU
        SPM --> SPC
        SPCM --> SPU
        SPFM --> SPFU
        SPFM --> DSMA
        NM --> DSMA
        SM --> DSMA
        OCM --> DSMA
        
        SPFU --> DSMA
    end
    
    subgraph "Target Hosts"
        subgraph "SP Server Components"
            SPSERVER[SP Server Instance]
            DB2[DB2 Database]
            DSMSERV[dsmserv Process]
        end
        
        subgraph "System Resources"
            FS[File System]
            STORAGE[Storage Pools]
            LOGS[Active/Archive Logs]
        end
        
        CLI[dsmadmc CLI]
        IMCL[IBM Installation Manager]
    end
    
    SPM -.->|Install/Upgrade/Uninstall| IMCL
    SPCM -.->|Configure| DSMSERV
    SPFM -.->|Query| CLI
    NM -.->|Manage Nodes| CLI
    SM -.->|Manage Schedules| CLI
    
    CLI --> SPSERVER
    IMCL --> SPSERVER
    DSMSERV --> DB2
    DSMSERV --> STORAGE
    DSMSERV --> LOGS
    SPSERVER --> FS
    
    style SPM fill:#e1f5ff
    style SPCM fill:#e1f5ff
    style SPFM fill:#e1f5ff
    style SPU fill:#fff4e1
    style DSMA fill:#fff4e1
```

---

## Component Details

### 1. Python Modules

#### 1.1 sp_server.py (Installation Orchestrator)

**Purpose**: Main orchestration module for SP Server lifecycle management (install/upgrade/uninstall)

**Key Classes**:
- [`BA_SERVER_SETUP`](plugins/modules/sp_server.py:195): Main orchestration class

**Key Methods**:
- [`run(mode)`](plugins/modules/sp_server.py:207): Entry point for lifecycle operations
- [`_install()`](plugins/modules/sp_server.py:222): Fresh installation workflow
- [`_upgrade()`](plugins/modules/sp_server.py:261): Upgrade workflow
- [`_uninstall()`](plugins/modules/sp_server.py:312): Uninstallation workflow
- [`_deploy()`](plugins/modules/sp_server.py:352): Binary deployment and installation
- [`_undeploy()`](plugins/modules/sp_server.py:480): Uninstallation execution

**Responsibilities**:
- Artifact discovery and validation
- Binary extraction and preparation
- Response XML generation
- IBM Installation Manager interaction
- Version comparison and upgrade logic
- Rollback on failure

#### 1.2 sp_server_configure.py

**Purpose**: Server configuration management after installation

**Key Classes**:
- [`SPServerConfiguration`](plugins/modules/sp_server_configure.py:23): Configuration orchestrator

**Key Methods**:
- [`prepare_storage()`](plugins/modules/sp_server_configure.py:147): Storage preparation
- [`_ensure_directories()`](plugins/modules/sp_server_configure.py:99): Directory creation
- [`_run_cmd()`](plugins/modules/sp_server_configure.py:63): Command execution wrapper

**Responsibilities**:
- User and group creation
- Directory structure setup
- DB2 instance creation
- Database formatting
- Server options configuration
- Administrative user setup

#### 1.3 sp_server_facts.py

**Purpose**: Gather server facts and status information

**Key Functions**:
- [`main()`](plugins/modules/sp_server_facts.py:99): Module entry point

**Supported Queries**:
- Server status
- Monitor settings
- Database information
- Database space
- Log information
- Domain information
- Copy groups
- Replication rules
- Device classes
- Management classes
- Storage pools

#### 1.4 node.py

**Purpose**: Client node registration and management

**Capabilities**:
- Register new client nodes
- Update node configuration
- Deregister nodes
- Associate schedules with nodes
- Set node policies and options

#### 1.5 schedule.py

**Purpose**: Schedule management for backup operations

**Capabilities**:
- Define backup schedules
- Configure schedule timing
- Set schedule actions (incremental, selective, archive, etc.)
- Manage schedule lifecycle

---

### 2. Module Utilities

#### 2.1 sp_server_utils.py

**Purpose**: Reusable utility functions for SP Server operations

**Key Function Categories**:

**OS Helpers**:
- [`os_oskey()`](plugins/module_utils/sp_server_utils.py:75): OS detection and normalization
- [`get_os_info()`](plugins/module_utils/sp_server_utils.py:122): Detailed OS information
- [`get_system_info()`](plugins/module_utils/sp_server_utils.py:186): System resource information

**File System Helpers**:
- `fs_exists()`: Check file/directory existence
- `fs_ensure_dir()`: Create directories
- `fs_remove_tree()`: Remove directory trees
- `fs_require_free_mb()`: Check available disk space

**Execution Helpers**:
- `exec_run()`: Execute shell commands
- `extract_binary_package()`: Extract installation binaries

**Version Helpers**:
- `version_parse()`: Parse version strings
- `version_is_newer()`: Compare versions

**BA Server Helpers**:
- `ba_install_dir()`: Determine installation directory
- `ba_is_installed()`: Check installation status
- `find_installer()`: Locate installation artifacts

**XML Helpers**:
- [`AgentInputXMLBuilder`](plugins/module_utils/sp_server_utils.py:381): Generate installation response XML
- `update_xml_value()`: Update XML configuration
- `update_package_offering()`: Update package offerings in XML

#### 2.2 sp_server_constants.py

**Purpose**: Constants and metadata for SP Server components

**Key Data Structures**:
- [`offerings_metadata`](plugins/module_utils/sp_server_constants.py:31): Component metadata
  - `server`: SP Server core
  - `stagent`: Storage Agent
  - `devices`: Device drivers
  - `oc`: Operations Center
  - `ossm`: Open Systems Storage Manager
  - `license`: License component

- [`preferences`](plugins/module_utils/sp_server_constants.py:70): Installation Manager preferences

#### 2.3 sp_server_facts.py (Module Utils)

**Purpose**: Parse and transform dsmadmc output

**Key Classes**:
- [`DsmadmcAdapterExtended`](plugins/module_utils/sp_server_facts.py:5): Extended adapter with comma-delimited support
- [`DSMParser`](plugins/module_utils/sp_server_facts.py:35): Output parser
- [`SpServerResponseMapper`](plugins/module_utils/sp_server_facts.py:298): Response transformation

**Parser Methods**:
- [`parse_q_status()`](plugins/module_utils/sp_server_facts.py:41): Parse status output
- [`parse_q_db()`](plugins/module_utils/sp_server_facts.py:95): Parse database info
- [`parse_q_stgpool()`](plugins/module_utils/sp_server_facts.py:273): Parse storage pool info
- Additional parsers for various query types

#### 2.4 dsmadmc_adapter.py

**Purpose**: Base adapter for dsmadmc CLI interaction

**Key Classes**:
- [`DsmadmcAdapter`](plugins/module_utils/dsmadmc_adapter.py:9): Base adapter class

**Key Methods**:
- [`run_command()`](plugins/module_utils/dsmadmc_adapter.py:46): Execute dsmadmc commands
- [`find_one()`](plugins/module_utils/dsmadmc_adapter.py:71): Query single object
- [`perform_action()`](plugins/module_utils/dsmadmc_adapter.py:80): Perform CRUD operations

**Authentication**:
- Server name (env: `STORAGE_PROTECT_SERVERNAME`)
- Username (env: `STORAGE_PROTECT_USERNAME`)
- Password (env: `STORAGE_PROTECT_PASSWORD`)

---

### 3. Ansible Roles

#### 3.1 sp_server_install

**Purpose**: Complete SP Server installation, upgrade, and uninstallation

**Main Tasks**: [`main.yml`](roles/sp_server_install/tasks/main.yml)

**Task Files**:
- [`sp_server_prechecks_linux.yml`](roles/sp_server_install/tasks/sp_server_prechecks_linux.yml): Pre-installation validation
- [`sp_server_install_linux.yml`](roles/sp_server_install/tasks/sp_server_install_linux.yml): Installation execution
- [`sp_server_configuration_linux.yml`](roles/sp_server_install/tasks/sp_server_configuration_linux.yml): Post-install configuration
- [`sp_server_postchecks_linux.yml`](roles/sp_server_install/tasks/sp_server_postchecks_linux.yml): Installation verification
- [`sp_server_uninstall_linux.yml`](roles/sp_server_install/tasks/sp_server_uninstall_linux.yml): Uninstallation

**Key Variables**:
- `sp_server_state`: present/absent/upgrade
- `sp_server_version`: Target version
- `sp_server_bin_repo`: Binary repository path
- `ssl_password`: SSL password for server
- `tsm_user`: Instance user
- `tsm_group`: Instance group

#### 3.2 sp_server_facts

**Purpose**: Gather SP Server facts

**Main Tasks**: [`main.yml`](roles/sp_server_facts/tasks/main.yml)

**Usage**: Collects server information using [`sp_server_facts`](plugins/modules/sp_server_facts.py) module

#### 3.3 nodes

**Purpose**: Manage client nodes

**Main Tasks**: [`main.yml`](roles/nodes/tasks/main.yml)

**Capabilities**: Register, update, and deregister client nodes

#### 3.4 schedules

**Purpose**: Manage backup schedules

**Main Tasks**: [`main.yml`](roles/schedules/tasks/main.yml)

**Capabilities**: Create and manage backup schedules

---

## Data Flow Diagrams

### Installation Workflow

```mermaid
sequenceDiagram
    participant User
    participant Playbook
    participant Role as sp_server_install
    participant Module as sp_server.py
    participant Utils as sp_server_utils.py
    participant IMCL as IBM Installation Manager
    participant Target as Target Host
    
    User->>Playbook: ansible-playbook sp_server_install_playbook.yml
    Playbook->>Role: Execute role with vars
    
    Role->>Role: sp_server_prechecks_linux.yml
    Role->>Target: Check binary exists
    Role->>Target: Verify architecture compatibility
    Role->>Target: Check disk space (>7500MB)
    
    alt Prechecks Pass
        Role->>Module: Call sp_server module (mode=install)
        Module->>Utils: ba_is_installed()
        Utils-->>Module: Installation status
        
        alt Not Installed
            Module->>Utils: find_installer()
            Utils-->>Module: Installer path
            
            Module->>Utils: extract_binary_package()
            Utils->>Target: Extract to temp directory
            
            Module->>Utils: AgentInputXMLBuilder.generate()
            Utils-->>Module: response.xml
            
            Module->>Target: Execute install.sh with response.xml
            Target->>IMCL: Silent installation
            IMCL->>Target: Install packages
            IMCL-->>Module: Installation result
            
            Module->>Role: Installation complete
            Role->>Role: sp_server_postchecks_linux.yml
            Role->>Target: Verify installation
            
            Role->>Role: sp_server_configuration_linux.yml
            Role->>Target: Create user/group
            Role->>Target: Setup directories
            Role->>Target: Create DB2 instance
            Role->>Target: Format database
            Role->>Target: Create admin user
            
            Role-->>User: Installation successful
        else Already Installed
            Module->>Module: Switch to upgrade path
        end
    else Prechecks Fail
        Role-->>User: Prechecks failed
    end
```

### Configuration Workflow

```mermaid
sequenceDiagram
    participant Role as sp_server_install
    participant Target as Target Host
    participant DB2
    participant DSMSERV as dsmserv
    
    Role->>Target: Create TSM user and group
    Target-->>Role: User/group created
    
    Role->>Target: Create directory structure
    Note over Target: /tsminst1/TSMdbspace01-04<br/>/tsminst1/TSMalog<br/>/tsminst1/TSMarchlog
    Target-->>Role: Directories created
    
    Role->>Target: Create DB2 instance
    Target->>DB2: db2icrt -a server -u tsminst1
    DB2-->>Target: Instance created
    
    Role->>Target: Update DB2 configuration
    Target->>DB2: db2 update dbm cfg using dftdbpath
    DB2-->>Target: Config updated
    
    Role->>Target: Copy and configure dsmserv.opt
    Note over Target: Set tcpport, activelogsize,<br/>maxsessions, etc.
    Target-->>Role: Options configured
    
    Role->>Target: Format database
    Target->>DSMSERV: dsmserv format dbdir=...
    DSMSERV->>DB2: Create database
    DB2-->>DSMSERV: Database formatted
    DSMSERV-->>Target: Format complete
    
    Role->>Target: Create admin user macro
    Target-->>Role: Macro created
    
    Role->>Target: Execute admin user macro
    Target->>DSMSERV: dsmserv runfile setup.mac
    DSMSERV-->>Target: Admin user created
    
    alt Blueprint Mode
        Role->>Target: Generate configuration macros
        Note over Target: basics.mac, policy.mac,<br/>schedules.mac, cntrpool.mac
        Role->>Target: Execute configuration macros
        Target->>DSMSERV: dsmserv runfile *.mac
        DSMSERV-->>Target: Configuration applied
    end
    
    Role->>Target: Configure DSMI environment
    Target-->>Role: Environment configured
    
    Role-->>Role: Configuration complete
```

### Facts Gathering Workflow

```mermaid
sequenceDiagram
    participant User
    participant Module as sp_server_facts.py
    participant Adapter as DsmadmcAdapterExtended
    participant Parser as DSMParser
    participant Mapper as SpServerResponseMapper
    participant CLI as dsmadmc
    participant Server as SP Server
    
    User->>Module: Execute with query flags
    Note over User: q_status=true<br/>q_db=true<br/>q_stgpool=true
    
    loop For each enabled query
        Module->>Adapter: run_command('q status')
        Adapter->>CLI: dsmadmc -commadelimited q status
        CLI->>Server: Query server
        Server-->>CLI: Comma-delimited output
        CLI-->>Adapter: Raw output
        
        Adapter-->>Module: Return code and output
        
        Module->>Parser: parse_q_status(output)
        Parser->>Parser: Split by comma
        Parser->>Parser: Map to labels
        Parser-->>Module: Structured dict
    end
    
    Module->>Mapper: map_to_developer_friendly(results)
    Mapper->>Mapper: Transform keys to snake_case
    Mapper-->>Module: Developer-friendly format
    
    Module-->>User: Return facts
```

### Node Management Workflow

```mermaid
sequenceDiagram
    participant User
    participant Module as node.py
    participant Adapter as DsmadmcAdapter
    participant CLI as dsmadmc
    participant Server as SP Server
    
    User->>Module: Register node with params
    Note over User: name, password,<br/>policy_domain, schedules
    
    Module->>Adapter: find_one('node', name)
    Adapter->>CLI: dsmadmc q node <name>
    CLI->>Server: Query node
    Server-->>CLI: Node info or not found
    CLI-->>Adapter: Result
    Adapter-->>Module: exists=true/false
    
    alt Node does not exist
        Module->>Adapter: perform_action('register', 'node', ...)
        Adapter->>CLI: dsmadmc register node <name> <password> domain=<domain>
        CLI->>Server: Register node
        Server->>Server: Create node entry
        Server-->>CLI: Success
        CLI-->>Adapter: rc=0
        
        loop For each schedule
            Module->>Adapter: run_command('define association ...')
            Adapter->>CLI: dsmadmc define association
            CLI->>Server: Associate schedule
            Server-->>CLI: Success
        end
        
        Adapter-->>Module: Node registered
    else Node exists
        Module->>Adapter: perform_action('update', 'node', ...)
        Adapter->>CLI: dsmadmc update node <name> ...
        CLI->>Server: Update node
        Server-->>CLI: Success
        Adapter-->>Module: Node updated
    end
    
    Module-->>User: Result (changed=true/false)
```

### Upgrade Workflow

```mermaid
sequenceDiagram
    participant User
    participant Role as sp_server_install
    participant Module as sp_server.py
    participant Utils as sp_server_utils.py
    participant IMCL as IBM Installation Manager
    participant Target as Target Host
    
    User->>Role: Execute with state=upgrade
    
    Role->>Role: sp_server_prechecks_linux.yml
    Role->>Target: Check installed version
    Role->>Role: Compare versions
    
    alt New version > Installed version
        Role->>Module: Call sp_server (mode=upgrade)
        
        Module->>Utils: ba_is_installed()
        Utils-->>Module: Current version info
        
        Module->>Utils: find_installer(new_version)
        Utils-->>Module: New installer path
        
        Module->>Utils: version_is_newer()
        Utils-->>Module: Comparison result
        
        alt Upgrade needed
            Module->>Module: _uninstall()
            Module->>IMCL: imcl uninstall
            IMCL->>Target: Remove packages
            IMCL-->>Module: Uninstall complete
            
            Module->>Utils: fs_remove_tree()
            Utils->>Target: Clean directories
            
            Module->>Utils: fs_ensure_dir()
            Utils->>Target: Recreate directories
            
            Module->>Module: _deploy(new_version)
            Module->>Target: Extract new binary
            Module->>Utils: AgentInputXMLBuilder.generate()
            Module->>IMCL: install.sh with response.xml
            IMCL->>Target: Install new version
            IMCL-->>Module: Installation complete
            
            Module-->>Role: Upgrade successful
            Role->>Role: sp_server_postchecks_linux.yml
            Role-->>User: Upgrade complete
        else Already up to date
            Module-->>User: No upgrade needed
        end
    else Version check fails
        Role-->>User: Upgrade not required
    end
```

---

## Component Interaction Matrix

| Component | Interacts With | Purpose |
|-----------|---------------|---------|
| **sp_server.py** | sp_server_utils.py | Utility functions for installation |
| | sp_server_constants.py | Component metadata |
| | IBM Installation Manager | Binary installation/uninstallation |
| | File System | Binary extraction, directory management |
| **sp_server_configure.py** | sp_server_utils.py | Configuration utilities |
| | dsmserv | Database formatting, configuration |
| | DB2 | Instance creation, database setup |
| **sp_server_facts.py** | dsmadmc_adapter.py | CLI command execution |
| | sp_server_facts.py (utils) | Output parsing |
| | dsmadmc CLI | Server queries |
| **node.py** | dsmadmc_adapter.py | Node operations |
| | dsmadmc CLI | Node registration/management |
| **schedule.py** | dsmadmc_adapter.py | Schedule operations |
| | dsmadmc CLI | Schedule definition |
| **dsmadmc_adapter.py** | subprocess | Command execution |
| | AnsibleModule | Ansible integration |
| **sp_server_utils.py** | OS APIs | System information |
| | File System | File operations |
| | subprocess | Command execution |
| | XML libraries | Response file generation |

---

## Installation Package Structure

### 1. Binary Package Extraction

```mermaid
graph LR
    BIN[Binary Package<br/>8.1.27-IBM-SPOC-LinuxX64.bin]
    EXTRACT[Extracted Directory]
    INPUT[input/]
    INSTALL[install.sh]
    REPO[repository/]
    
    BIN -->|Execute| EXTRACT
    EXTRACT --> INPUT
    EXTRACT --> INSTALL
    EXTRACT --> REPO
    
    style BIN fill:#e1f5ff
    style EXTRACT fill:#fff4e1
```

### 2. Response File Generation

```mermaid
graph TB
    SAMPLE[install_response_sample.xml<br/>Template File]
    BUILDER[AgentInputXMLBuilder]
    VARS[ansible-vars.json<br/>Configuration]
    RESPONSE[response.xml<br/>Generated File]
    
    SAMPLE --> BUILDER
    VARS --> BUILDER
    BUILDER --> RESPONSE
    
    subgraph "Response XML Contents"
        PROFILE[Profile: IBM Storage Protect]
        OFFERINGS[Offerings: server, gskit, etc.]
        PREFS[Preferences: Timeouts, SSL]
        REPOS[Repositories: Local paths]
        DATA[Data: Passwords, Licenses]
    end
    
    RESPONSE --> PROFILE
    RESPONSE --> OFFERINGS
    RESPONSE --> PREFS
    RESPONSE --> REPOS
    RESPONSE --> DATA
    
    style RESPONSE fill:#e1ffe1
    style BUILDER fill:#fff4e1
```

### 3. Installation Manager Workflow

```mermaid
graph TB
    INSTALL[install.sh]
    RESPONSE[response.xml]
    IMCL[IBM Installation Manager<br/>/opt/IBM/InstallationManager]
    
    INSTALL -->|Calls with -s -input| IMCL
    RESPONSE -->|Configuration| IMCL
    
    subgraph "Package Installation"
        PKG1[com.tivoli.dsm.server<br/>SP Server Core]
        PKG2[com.tivoli.dsm.gskit<br/>Security Toolkit]
        PKG3[com.tivoli.dsm.clientapi<br/>Client API]
        PKG4[com.ibm.java.jre<br/>Java Runtime]
    end
    
    IMCL --> PKG1
    IMCL --> PKG2
    IMCL --> PKG3
    IMCL --> PKG4
    
    style IMCL fill:#e1f5ff
    style PKG1 fill:#fff4e1
```

### 4. Installed Directory Structure

```mermaid
graph TB
    subgraph "System Directories"
        OPT[/opt/tivoli/tsm/]
        USR[/usr/local/ibm/]
        INST[/tsminst1/]
    end
    
    subgraph "Server Installation - /opt/tivoli/tsm/"
        SRVBIN[server/bin/<br/>• dsmserv<br/>• dsmadmc<br/>• dsmc]
        SRVBKAPI[server/bin/dbbkapi/<br/>• DB2 Backup API<br/>• dsm.sys]
        DB2DIR[db2/<br/>• DB2 Engine<br/>• Libraries]
        DB2INSTDIR[db2/instance/<br/>• db2icrt<br/>• db2ilist]
    end
    
    subgraph "Security - /usr/local/ibm/"
        GSKIT[gsk8_64/<br/>• GSKit Libraries<br/>• SSL/TLS Support<br/>• gsk8capicmd_64]
    end
    
    subgraph "Instance Directory - /tsminst1/"
        HOME[Home Directory<br/>• .profile<br/>• sqllib/]
        DBSPACE[Database Spaces<br/>• TSMdbspace01/<br/>• TSMdbspace02/<br/>• TSMdbspace03/<br/>• TSMdbspace04/]
        ALOG[Active Logs<br/>• TSMalog/]
        ARCHLOG[Archive Logs<br/>• TSMarchlog/]
        CONF[Configuration<br/>• dsmserv.opt<br/>• devconf.dat<br/>• volhist.out<br/>• tsmdbmgr.opt]
    end
    
    OPT --> SRVBIN
    OPT --> SRVBKAPI
    OPT --> DB2DIR
    OPT --> DB2INSTDIR
    
    USR --> GSKIT
    
    INST --> HOME
    INST --> DBSPACE
    INST --> ALOG
    INST --> ARCHLOG
    INST --> CONF
    
    style OPT fill:#e1f5ff
    style USR fill:#fff4e1
    style INST fill:#e1ffe1
```

### 5. Package Metadata

| Package ID | Version | Features | Installation Path |
|------------|---------|----------|-------------------|
| **com.tivoli.dsm.server** | 8.1.27+ | server.main, gskit, clientapi, jre | /opt/tivoli/tsm/server |
| **com.tivoli.dsm.gskit** | 8.0.55+ | Security libraries | /usr/local/ibm/gsk8_64 |
| **com.tivoli.dsm.clientapi** | 8.1.27+ | Client API libraries | /opt/tivoli/tsm/server/bin/dbbkapi |
| **com.ibm.java.jre** | 8.0+ | Java Runtime Environment | /opt/tivoli/tsm/java |

---

## Database and Storage Architecture

```mermaid
graph TB
    subgraph "SP Server Instance"
        DSMSERV[dsmserv Process]
        DSMOPT[dsmserv.opt]
        DSMSERV --> DSMOPT
    end
    
    subgraph "DB2 Instance"
        DB2INST[DB2 Instance<br/>tsminst1]
        DB2PROF[db2profile]
        DB2CFG[DBM Configuration]
        
        DB2INST --> DB2PROF
        DB2INST --> DB2CFG
    end
    
    subgraph "Database Storage"
        DBSPACE1[TSMdbspace01]
        DBSPACE2[TSMdbspace02]
        DBSPACE3[TSMdbspace03]
        DBSPACE4[TSMdbspace04]
        
        DB2INST --> DBSPACE1
        DB2INST --> DBSPACE2
        DB2INST --> DBSPACE3
        DB2INST --> DBSPACE4
    end
    
    subgraph "Transaction Logs"
        ALOG[Active Log<br/>TSMalog/]
        ARCHLOG[Archive Log<br/>TSMarchlog/]
        
        DSMSERV --> ALOG
        DSMSERV --> ARCHLOG
    end
    
    subgraph "Storage Pools"
        DEVCLASS[Device Classes]
        STGPOOL[Storage Pools]
        VOLUMES[Volumes]
        
        DEVCLASS --> STGPOOL
        STGPOOL --> VOLUMES
    end
    
    subgraph "Configuration Files"
        DEVCONF[devconf.dat]
        VOLHIST[volhist.out]
        DSMSYS[dsm.sys]
        TSMDBOPT[tsmdbmgr.opt]
    end
    
    DSMSERV --> DB2INST
    DSMSERV --> DEVCLASS
    DSMSERV --> DEVCONF
    DSMSERV --> VOLHIST
    
    style DSMSERV fill:#e1f5ff
    style DB2INST fill:#fff4e1
    style STGPOOL fill:#e1ffe1
```

---

## Error Handling and Rollback

### Installation Failure Rollback

```mermaid
flowchart TD
    START[Installation Started] --> EXTRACT[Extract Binary]
    EXTRACT --> |Success| GENXML[Generate response.xml]
    EXTRACT --> |Failure| CLEANUP1[Clean temp directory]
    
    GENXML --> |Success| INSTALL[Execute install.sh]
    GENXML --> |Failure| CLEANUP1
    
    INSTALL --> |Success| VERIFY[Verify Installation]
    INSTALL --> |Failure| ROLLBACK[Rollback Process]
    
    VERIFY --> |Success| CONFIG[Configure Server]
    VERIFY --> |Failure| ROLLBACK
    
    CONFIG --> |Success| END[Installation Complete]
    CONFIG --> |Failure| ROLLBACK
    
    ROLLBACK --> CHECKPKG[Check Installed Packages]
    CHECKPKG --> UNINSTALL[Uninstall Packages via imcl]
    UNINSTALL --> CLEANUP2[Remove Directories]
    CLEANUP2 --> FAIL[Installation Failed]
    
    CLEANUP1 --> FAIL
    
    style START fill:#e1f5ff
    style END fill:#e1ffe1
    style FAIL fill:#ffe1e1
    style ROLLBACK fill:#fff4e1
```

### Upgrade Failure Handling

```mermaid
flowchart TD
    START[Upgrade Started] --> CHECKVER[Check Current Version]
    CHECKVER --> |Valid| FINDNEW[Find New Installer]
    CHECKVER --> |Invalid| FAIL[Upgrade Failed]
    
    FINDNEW --> |Found| COMPARE[Compare Versions]
    FINDNEW --> |Not Found| FAIL
    
    COMPARE --> |Newer| UNINSTOLD[Uninstall Old Version]
    COMPARE --> |Same/Older| SKIP[Skip Upgrade]
    
    UNINSTOLD --> |Success| CLEANDIR[Clean Directories]
    UNINSTOLD --> |Failure| FAIL
    
    CLEANDIR --> |Success| INSTALLNEW[Install New Version]
    CLEANDIR --> |Failure| FAIL
    
    INSTALLNEW --> |Success| VERIFYNEW[Verify New Installation]
    INSTALLNEW --> |Failure| ROLLBACK[Attempt Rollback]
    
    VERIFYNEW --> |Success| END[Upgrade Complete]
    VERIFYNEW --> |Failure| ROLLBACK
    
    ROLLBACK --> FINDOLD[Find Previous Artifact]
    FINDOLD --> |Found| REINSTOLD[Reinstall Old Version]
    FINDOLD --> |Not Found| FAIL
    
    REINSTOLD --> |Success| WARN[Rollback Successful]
    REINSTOLD --> |Failure| FAIL
    
    SKIP --> END
    WARN --> FAIL
    
    style START fill:#e1f5ff
    style END fill:#e1ffe1
    style FAIL fill:#ffe1e1
    style ROLLBACK fill:#fff4e1
```

---

## Security Considerations

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Ansible
    participant Module
    participant Adapter as dsmadmc_adapter
    participant CLI as dsmadmc
    participant Server as SP Server
    
    User->>Ansible: Provide credentials
    Note over User: STORAGE_PROTECT_USERNAME<br/>STORAGE_PROTECT_PASSWORD<br/>STORAGE_PROTECT_SERVERNAME
    
    Ansible->>Module: Execute with env vars
    Module->>Adapter: Initialize with credentials
    Note over Adapter: password marked as no_log=True
    
    Adapter->>CLI: dsmadmc -id=<user> -pass=<pass>
    Note over CLI: Password not logged
    
    CLI->>Server: Authenticate
    Server->>Server: Validate credentials
    Server-->>CLI: Authentication result
    
    alt Authentication Success
        CLI-->>Adapter: Session established
        Adapter->>CLI: Execute commands
        CLI->>Server: Perform operations
        Server-->>CLI: Results
        CLI-->>Adapter: Command output
        Adapter-->>Module: Results
        Module-->>User: Success
    else Authentication Failure
        CLI-->>Adapter: Auth failed
        Adapter-->>Module: Error
        Module-->>User: Authentication failed
    end
```

### Password Management

- **Installation Password**: Required for SSL configuration during installation
  - Provided via `--serverpassword` CLI argument or `SP_BA_SERVER_PASSWORD` environment variable
  - Used in response.xml for SSL password configuration
  - Marked as `no_log: true` in Ansible tasks

- **Admin User Password**: Created during configuration
  - Set in setup.mac file
  - Used for administrative operations

- **Node Passwords**: Managed through node registration
  - Minimum 15 characters (configurable)
  - Expiration period configurable (0-9999 days)

---

## Performance Considerations

### Server Sizing

The collection supports different server sizes with pre-configured parameters:

| Size | Active Log Size | Max Sessions | Use Case |
|------|----------------|--------------|----------|
| **xsmall** | 2048 MB | 25 | Development/Testing |
| **small** | 4096 MB | 50 | Small deployments |
| **medium** | 8192 MB | 100 | Medium deployments |
| **large** | 16384 MB | 200 | Large deployments |

### Resource Requirements

**Minimum Requirements**:
- Disk Space: 7500 MB free
- Supported Architectures: x86_64, s390x, ppc64le
- Memory: Varies by server size
- Network: TCP/IP connectivity

**Database Configuration**:
- Multiple database spaces (TSMdbspace01-04)
- Separate active and archive log directories
- Configurable log sizes based on server size

---

## Testing Strategy

### Test Coverage

```mermaid
graph LR
    subgraph "Integration Tests"
        INSTALL[test_sp_server_install.yml]
        FACTS[test_sp_server_facts.yml]
        NODE[test_sp_client.yml]
        SCHED[test_sp_schedule.yml]
    end
    
    subgraph "Test Scenarios"
        FRESH[Fresh Installation]
        CONFIG[Configuration]
        UPGRADE[Upgrade]
        UNINSTALL[Uninstallation]
        QUERY[Facts Gathering]
        NODEMGMT[Node Management]
        SCHEDMGMT[Schedule Management]
    end
    
    INSTALL --> FRESH
    INSTALL --> CONFIG
    INSTALL --> UPGRADE
    INSTALL --> UNINSTALL
    
    FACTS --> QUERY
    NODE --> NODEMGMT
    SCHED --> SCHEDMGMT
    
    style INSTALL fill:#e1f5ff
    style FACTS fill:#fff4e1
```

### Test Execution Flow

1. **Fresh Installation Test**
   - Verify binary availability
   - Execute installation
   - Verify installed components
   - Validate configuration

2. **Configuration Test**
   - Test on already installed server
   - Verify configuration application
   - Check database formatting
   - Validate admin user creation

3. **Upgrade Test**
   - Install base version
   - Upgrade to newer version
   - Verify version change
   - Validate functionality

4. **Uninstallation Test**
   - Uninstall server
   - Verify component removal
   - Check cleanup

5. **Facts Gathering Test**
   - Query various server facts
   - Validate output format
   - Check data accuracy

---

## Future Enhancements

### Planned Features

1. **High Availability Support**
   - Replication configuration
   - Failover automation
   - Load balancing

2. **Advanced Monitoring**
   - Performance metrics collection
   - Alert configuration
   - Dashboard integration

3. **Backup Automation**
   - Database backup scheduling
   - Configuration backup
   - Disaster recovery procedures

4. **Cloud Integration**
   - Cloud storage pool support
   - Container deployment
   - Kubernetes operators

5. **Enhanced Security**
   - Certificate automation
   - Key management integration
   - Audit logging

---

## Appendix

### A. File Locations

**Installation Directories**:
- Server binaries: `/opt/tivoli/tsm/server/bin`
- DB2 instance: `/opt/tivoli/tsm/db2`
- GSKit: `/usr/local/ibm/gsk8_64`
- Instance home: `/home/tsminst1`

**Configuration Files**:
- Server options: `/tsminst1/dsmserv.opt`
- Device configuration: `/tsminst1/devconf.dat`
- Volume history: `/tsminst1/volhist.out`
- DSM system file: `/opt/tivoli/tsm/server/bin/dbbkapi/dsm.sys`
- DSMI options: `/tsminst1/tsmdbmgr.opt`

**Database and Logs**:
- Database spaces: `/tsminst1/TSMdbspace01-04`
- Active logs: `/tsminst1/TSMalog`
- Archive logs: `/tsminst1/TSMarchlog`

### B. Environment Variables

**Required for Installation**:
- `SP_BA_SERVER_PASSWORD`: Server SSL password

**Required for Operations**:
- `STORAGE_PROTECT_SERVERNAME`: Server name (default: local)
- `STORAGE_PROTECT_USERNAME`: Admin username
- `STORAGE_PROTECT_PASSWORD`: Admin password

**DB2 Environment**:
- `DB2INSTANCE`: Instance name (e.g., tsminst1)
- `DSMI_CONFIG`: Path to tsmdbmgr.opt
- `DSMI_DIR`: Path to dbbkapi directory
- `DSMI_LOG`: Log directory path

### C. Command Reference

**Installation Manager Commands**:
```bash
# List installed packages
/opt/IBM/InstallationManager/eclipse/tools/imcl listInstalledPackages

# Install with response file
./install.sh -s -input response.xml -acceptLicense

# Uninstall packages
/opt/IBM/InstallationManager/eclipse/tools/imcl uninstall <package_id>
```

**DB2 Commands**:
```bash
# Create instance
/opt/tivoli/tsm/db2/instance/db2icrt -a server -u tsminst1 tsminst1

# Update DBM configuration
db2 update dbm cfg using dftdbpath /tsminst1

# Set registry variable
db2set DB2NOEXITLIST=ON
```

**Server Commands**:
```bash
# Format database
dsmserv format dbdir=/tsminst1/TSMdbspace01,... activelogsize=2048 \
  activelogdirectory=/tsminst1/TSMalog \
  archlogdirectory=/tsminst1/TSMarchlog

# Run macro file
dsmserv runfile setup.mac

# Query server
dsmadmc -id=admin -pass=password q status
```

### D. Troubleshooting Guide

**Common Issues**:

1. **Installation Fails**
   - Check disk space (>7500 MB required)
   - Verify binary file exists and is executable
   - Check architecture compatibility
   - Review installation logs

2. **Configuration Fails**
   - Verify user/group creation
   - Check directory permissions
   - Ensure DB2 instance created successfully
   - Review dsmserv.opt settings

3. **Facts Gathering Fails**
   - Verify dsmadmc is in PATH
   - Check authentication credentials
   - Ensure server is running
   - Verify network connectivity

4. **Upgrade Issues**
   - Confirm version comparison logic
   - Check for running processes
   - Verify backup before upgrade
   - Review rollback procedures

---

## Implementation Gaps and Analysis

### Current Implementation Status

Based on the codebase analysis, the following components are implemented:

✅ **Fully Implemented**:
- SP Server installation (Linux)
- SP Server upgrade (Linux)
- SP Server uninstallation (Linux)
- SP Server configuration (Linux)
- SP Server facts gathering
- Node management (register, update, deregister)
- Schedule management (define, update, delete)
- Storage pool queries
- Policy domain queries
- dsmadmc CLI adapter

### Identified Gaps

#### 1. Platform Support Gaps

| Platform | Installation | Configuration | Status |
|----------|-------------|---------------|---------|
| **Linux** | ✅ Complete | ✅ Complete | Production Ready |
| **Windows** | ⚠️ Partial | ❌ Missing | In Development |
| **AIX** | ❌ Missing | ❌ Missing | Not Started |

**Gap Details**:
- Windows installation logic exists in [`sp_server.py`](plugins/modules/sp_server.py:328) but lacks complete implementation
- AIX support is mentioned in design but no implementation found
- Windows-specific configuration tasks missing in roles

#### 2. Storage Management Gaps

**Missing Modules**:
- ❌ Storage pool creation/modification module
- ❌ Device class management module
- ❌ Volume management module
- ❌ Tape library configuration module

**Current State**: Only query operations available via [`sp_server_facts.py`](plugins/modules/sp_server_facts.py:1)

#### 3. Policy Management Gaps

**Missing Modules**:
- ❌ Policy domain creation/modification
- ❌ Policy set management
- ❌ Management class definition
- ❌ Copy group configuration

**Current State**: Only query operations available

#### 4. High Availability & Disaster Recovery Gaps

**Missing Features**:
- ❌ Replication configuration automation
- ❌ Failover automation
- ❌ Database backup automation
- ❌ Configuration backup/restore
- ❌ Multi-server orchestration

#### 5. Certificate Management Gaps

**Existing Implementation**:
- ✅ Certificate distribution playbook exists ([`cert_distribute.yml`](playbooks/cert_distribute.yml:1))
- ✅ Self-signed certificate creation via dsmadmc
- ✅ Certificate fetching from server
- ✅ Certificate distribution to multiple clients
- ✅ GSKit integration for keystore management
- ✅ Certificate verification

**Implementation Gaps**:
- ⚠️ **Not modularized**: Implemented as playbook only, no reusable module
- ❌ **No role abstraction**: Direct playbook implementation without role structure
- ❌ **Limited certificate types**: Only self-signed certificates supported
- ❌ **No CA integration**: Cannot import CA-signed certificates
- ❌ **Manual configuration**: Requires `data.ini` file with credentials
- ❌ **No certificate renewal**: No automation for expiring certificates
- ❌ **No certificate rotation**: No automated rotation workflow
- ❌ **Limited validation**: Basic verification only, no expiry checks
- ❌ **No Windows support**: Linux-only implementation
- ❌ **Hardcoded paths**: Uses fixed paths for GSKit and certificates

**Recommended Improvements**:
1. Create dedicated `certificate_management` role
2. Develop `sp_certificate` module for certificate operations
3. Add support for CA-signed certificates
4. Implement certificate expiry monitoring
5. Add automated renewal workflows
6. Support Windows certificate stores
7. Make paths configurable via variables
8. Add certificate validation and health checks
9. Implement certificate backup and recovery
10. Add integration with external PKI systems

#### 6. Monitoring and Alerting Gaps

**Missing Features**:
- ❌ Performance metrics collection
- ❌ Alert configuration automation
- ❌ Health check automation
- ❌ Capacity planning reports
- ❌ Integration with monitoring tools (Prometheus, Grafana)

#### 7. Testing Gaps

**Current Test Coverage**:
- ✅ Integration tests for installation
- ✅ Integration tests for facts gathering
- ✅ Integration tests for node management
- ✅ Integration tests for schedule management

**Missing Tests**:
- ❌ Unit tests for utility functions
- ❌ Windows platform tests
- ❌ AIX platform tests
- ❌ Upgrade rollback tests
- ❌ Performance tests
- ❌ Security tests

#### 8. Documentation Gaps

**Missing Documentation**:
- ❌ Windows installation guide
- ❌ AIX installation guide
- ❌ Troubleshooting playbooks
- ❌ Best practices guide
- ❌ Performance tuning guide
- ❌ Security hardening guide

#### 9. Error Handling Gaps

**Areas Needing Improvement**:
- ⚠️ Incomplete rollback for configuration failures
- ⚠️ Limited error recovery for network failures
- ⚠️ Insufficient validation of user inputs
- ⚠️ Missing pre-flight checks for some operations

#### 10. Idempotency Gaps

**Issues Identified**:
- ⚠️ Configuration tasks may not be fully idempotent
- ⚠️ Some operations lack proper state checking
- ⚠️ Repeated runs may cause inconsistent state

---

## Next Steps and Roadmap

### Phase 1: Platform Completion (Priority: High)

**Timeline**: Q2 2026

1. **Windows Support**
   - Complete Windows installation implementation
   - Add Windows configuration tasks
   - Create Windows-specific roles
   - Add Windows integration tests
   - Document Windows deployment

2. **AIX Support**
   - Implement AIX installation workflow
   - Add AIX configuration tasks
   - Create AIX-specific roles
   - Add AIX integration tests
   - Document AIX deployment

**Deliverables**:
- Fully functional Windows and AIX support
- Platform-specific documentation
- Integration test suites for all platforms

### Phase 2: Storage and Policy Management (Priority: High)

**Timeline**: Q3 2026

1. **Storage Management Modules**
   - Create storage pool management module
   - Implement device class management
   - Add volume management capabilities
   - Develop tape library configuration

2. **Policy Management Modules**
   - Implement policy domain management
   - Add policy set operations
   - Create management class module
   - Develop copy group configuration

**Deliverables**:
- Complete storage management automation
- Full policy lifecycle management
- Updated documentation and examples

### Phase 3: High Availability and DR (Priority: Medium)

**Timeline**: Q4 2026

1. **Replication and Failover**
   - Implement replication configuration
   - Add failover automation
   - Create multi-server orchestration
   - Develop health monitoring

2. **Backup and Recovery**
   - Automate database backups
   - Implement configuration backup
   - Add restore procedures
   - Create disaster recovery playbooks

**Deliverables**:
- HA/DR automation framework
- Disaster recovery documentation
- Failover testing procedures

### Phase 4: Security and Compliance (Priority: Medium)

**Timeline**: Q1 2027

1. **Certificate Management**
   - Implement SSL certificate automation
   - Add certificate renewal workflows
   - Create certificate distribution
   - Develop validation procedures

2. **Security Hardening**
   - Add security baseline configuration
   - Implement compliance checks
   - Create audit logging
   - Develop security scanning

**Deliverables**:
- Complete certificate lifecycle automation
- Security hardening playbooks
- Compliance reporting

### Phase 5: Monitoring and Operations (Priority: Low)

**Timeline**: Q2 2027

1. **Monitoring Integration**
   - Implement metrics collection
   - Add Prometheus exporters
   - Create Grafana dashboards
   - Develop alerting rules

2. **Operational Automation**
   - Add capacity planning tools
   - Implement performance tuning
   - Create maintenance playbooks
   - Develop troubleshooting automation

**Deliverables**:
- Monitoring and alerting framework
- Operational playbooks
- Performance optimization guides

### Phase 6: Testing and Quality (Ongoing)

**Timeline**: Continuous

1. **Test Coverage Expansion**
   - Add unit tests for all utilities
   - Expand integration test coverage
   - Implement performance tests
   - Add security tests

2. **Quality Improvements**
   - Enhance error handling
   - Improve idempotency
   - Add input validation
   - Refactor code for maintainability

**Deliverables**:
- 80%+ test coverage
- Improved code quality metrics
- Enhanced reliability

### Quick Wins (Immediate Actions)

1. **Documentation**
   - Add inline code documentation
   - Create troubleshooting guides
   - Document best practices
   - Add more examples

2. **Error Handling**
   - Improve error messages
   - Add validation checks
   - Enhance rollback procedures
   - Add pre-flight checks

3. **Idempotency**
   - Review all tasks for idempotency
   - Add state checking
   - Improve change detection
   - Add dry-run mode

### Success Metrics

**Phase 1-2 (Platform & Core Features)**:
- All 3 platforms (Linux, Windows, AIX) fully supported
- 100% of documented features implemented
- Integration tests passing on all platforms

**Phase 3-4 (HA/DR & Security)**:
- HA/DR automation functional
- Certificate management automated
- Security compliance checks passing

**Phase 5-6 (Monitoring & Quality)**:
- Monitoring integrated with 2+ platforms
- Test coverage > 80%
- Zero critical bugs in production

### Community Engagement

1. **Open Source Contribution**
   - Accept community pull requests
   - Provide contribution guidelines
   - Regular release cycles
   - Active issue management

2. **Documentation and Support**
   - Maintain up-to-date documentation
   - Provide example playbooks
   - Create video tutorials
   - Host community forums

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-26 | System | Initial comprehensive design document with architecture diagrams |
| 1.1 | 2026-03-26 | System | Added implementation gaps analysis and next steps roadmap |

---

## References

- [IBM Storage Protect 8.1.27 Documentation](https://www.ibm.com/docs/en/storage-protect/8.1.27?topic=servers)
- [Ansible Collection: ibm.storage_protect](https://galaxy.ansible.com/ibm/storage_protect)
- [IBM Installation Manager Documentation](https://www.ibm.com/docs/en/installation-manager)
- [DB2 Database Documentation](https://www.ibm.com/docs/en/db2)
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)

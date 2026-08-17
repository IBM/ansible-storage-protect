# IBM Storage Protect — Petascale Deployment & Configuration User Guide

## Document Information

| **Field** | **Value** |
|-----------|-----------|
| **Document Title** | Petascale Deployment & Configuration User Guide |
| **Version** | 1.0.0 |
| **Date** | 2026 |
| **Author** | IBM Storage Protect Team |
| **Audience** | System Administrators, DevOps Engineers |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Prerequisites](#2-prerequisites)
3. [Installation & Setup](#3-installation--setup)
4. [Quick Start Guide](#4-quick-start-guide)
5. [Configuration Guide — Variables & Files](#5-configuration-guide--variables--files)
6. [Installation Operations](#6-installation-operations)
7. [Post-Install Configuration](#7-post-install-configuration)
8. [Uninstallation Operations](#8-uninstallation-operations)
9. [Multi-Server Topology](#9-multi-server-topology)
10. [Post-Run Validation](#10-post-run-validation)
11. [Troubleshooting](#11-troubleshooting)
12. [Best Practices](#12-best-practices)
13. [FAQ](#13-faq)
14. [Appendices](#14-appendices)

---

## 1. Introduction

### 1.1 What is Petascale Deployment Ansible Automation?

The IBM Storage Protect Petascale Deployment Ansible Automation provides a comprehensive solution for automating the **installation**, **post-install configuration**, and **uninstallation** of SP Server, HSM Client, and BA Client software across your infrastructure at scale.

### 1.2 Playbooks Overview

| **Playbook** | **Purpose** |
|---|---|
| `petascale_install.yml` | Fresh installation of SP Server, HSM Client, and BA Client |
| `petascale_configure.yml` | Post-install configuration — server options, DB format, client config files, SSL certificates, GPFS policy bootstrap |
| `petascale_uninstall.yml` | Complete removal with cleanup and data preservation |
| `petascale_upgrade.yml` | Upgrade existing installations *(future work — not yet production-ready)* |

> **Important — run order:** Always run `petascale_install.yml` before `petascale_configure.yml`. The configure playbook detects whether each component is installed and skips configuration if it is not.

### 1.3 Key Benefits

- **Automated Deployment** — Install all components on multiple hosts simultaneously
- **Post-Install Configuration** — DB2 instance creation, server options, SSL certificates, GPFS policy bootstrap
- **Idempotent Operations** — Safe to run multiple times without side effects
- **Automatic Rollback** — Automatically reverts changes if operations fail
- **Dependency Validation** — Automated pre-flight checks before installation
- **Component Flexibility** — Install all or specific component groups
- **Configuration Management** — Centralised configuration with host and group variables

### 1.4 Supported Components & Platforms

| **Component** | **Description** | **Inventory Group** | **Supported OS** |
|---|---|---|---|
| **SP Server** | IBM Storage Protect Server | `sp_servers` | Linux |
| **HSM Client** | Hierarchical Storage Management Client | `hsm_clients` | Linux, AIX |
| **BA Client** | Backup-Archive Client | `ba_clients` | Linux, AIX |

> **Note:** Installing the HSM Client automatically includes the BA Client — there is no need to install the BA Client separately when deploying HSM Client nodes.

---

## 2. Prerequisites

### 2.1 Control Node Requirements

| **Component** | **Requirement** |
|---|---|
| Operating System | Linux, macOS, or WSL2 |
| Ansible | Version 2.12 or higher |
| Python | Version 3.6 or higher |
| `ansible.posix` collection | Required for `firewalld` module on SP Server nodes |
| `expect` utility | Required on client nodes for auth-cache bootstrap (optional but recommended) |
| SSH Access | Key-based or password authentication to target hosts |
| Network | Connectivity to all target hosts |

```bash
# Install Ansible
pip3 install ansible

# Install ansible.posix collection
ansible-galaxy collection install ansible.posix

# Verify installation
ansible --version
```

### 2.2 Target Host Requirements

#### 2.2.1 Critical Requirement — Node Separation

> **MANDATORY:** SP Server and BA/HSM Clients **MUST** be installed on **separate** nodes.

Different components require **incompatible GSKit versions**:
- **SP Server 8.1.27**: Requires GSKit 8.0.55.31
- **BA/HSM Client 8.1.x**: Requires GSKit 8.0.60.1

```
CORRECT — Separate Nodes:
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ SP Server   │  │ BA Client   │  │ HSM Client  │
│ Node 1      │  │ Node 2      │  │ Node 3      │
│ GSKit 8.55  │  │ GSKit 8.60  │  │ GSKit 8.60  │
└─────────────┘  └─────────────┘  └─────────────┘

INCORRECT — Same Node:
┌──────────────────────┐
│ SP Server + BA Client│  ← GSKit conflict!
│ Node 1               │
└──────────────────────┘
```

#### 2.2.2 System Requirements

| **Resource** | **All Nodes** | **SP Server (Additional)** |
|---|---|---|
| Python | 3.9+ | 3.9+ |
| Java | JRE/JDK 8+ | JRE/JDK 8+ |
| SSH | Root or sudo | Root or sudo |
| /tmp permissions | `1777` (rwxrwxrwt) | `1777` (rwxrwxrwt) |
| /tmp mount options | No `noexec` flag | No `noexec` flag |
| /tmp disk space | Minimum 20 GB free | Minimum 20 GB free |
| lsof | Required | Required |
| rsync | Required | Required |
| IBM Spectrum Scale (GPFS) | HSM Client nodes only | — |

- **Linux Python path**: `/usr/bin/python3.9`
- **AIX Python path**: `/opt/freeware/bin/python3.9`

#### 2.2.3 Software Packages

All software packages must be present on the **remote nodes** (target hosts), **not** on the Ansible control node.

| **Component** | **Location on Remote Node** | **Format** | **Example** |
|---|---|---|---|
| SP Server | `/tmp/` on SP Server nodes | `.bin` (self-extracting) | `8.1.27.000-IBM-SPSRV-LIC-DEBUG-Linuxx86_64-162.bin` |
| HSM Client | `/tmp/` on HSM Client nodes | `.tar` or `.tar.Z` | `8.1.25.0-TIV-TSMHSM-LinuxX86.tar` |
| BA Client | `/tmp/` on BA Client nodes | `.tar` | `8.1.25.0-TIV-TSMBAC-LinuxX86.tar` |

> **Note:** The BA Client package is **not required** on HSM Client nodes — it is bundled with and installed automatically as part of the HSM Client installation.

### 2.3 Network Requirements

| **Connection** | **Protocol** | **Port** | **Purpose** |
|---|---|---|---|
| Control → Target | SSH | 22 | Ansible communication |
| Client → SP Server | TCP | 1500 | Component communication |

### 2.4 Petascale Environment Prerequisites (Mandatory in Production)

To deploy Petascale automation successfully in standard production environments, the following external setup tasks must be completed out-of-band:

1. **GPFS Filesystem Partitioning & Mounts**
   * The IBM Spectrum Scale (GPFS) cluster, filesystems (e.g., `/gpfs_main`), and any independent filesets (e.g., `/gpfs_main/fileset_2`) must already be configured, formatted, and mounted across the client nodes.
   * The automated playbooks **do not** partition, format, or mount filesystems. They only configure Space Management to manage them.

2. **Client Node Registration on SP Server**
   * In production customer environments, Storage Protect (SP) Server administrators typically do not permit automated tooling to run client node registration commands.
   * Therefore, the BA Client and HSM Client node names (e.g., `hsm-client-03-sp01` defined under `sp_servers` in client configurations) **must be registered on the SP Server(s) by a Storage Administrator prior to deployment**.
   * The configure playbook's client node registration step is **bypassed by default** in production to prevent administrative privilege errors.

> 🧪 **Developer & Automated Testing Note (Optional):**
> If you are testing the playbooks in a sandbox or isolated development environment where you have full administrative privileges, you can set `gpfs_policy_register_nodes: true` in your SP Server variables file (e.g., `host_vars/sp-server-01.yml`). When enabled, the configure playbook will automatically perform the client node registrations on the SP Server for you.

---

## 3. Installation & Setup

### 3.1 Clone the Repository

```bash
git clone https://github.com/IBM/ansible-storage-protect.git
cd ansible-storage-protect
```

### 3.2 File Layout

```
playbooks/
├── petascale_install.yml          ← installation playbook
├── petascale_configure.yml        ← post-install configuration playbook
├── petascale_uninstall.yml        ← uninstallation playbook
├── inventory/
│   └── petascale.ini              ← inventory (hosts + connection settings)
├── group_vars/
│   ├── all.yml                    ← global defaults
│   ├── sp_servers.yml             ← SP Server group defaults
│   ├── ba_clients.yml             ← BA Client group defaults
│   └── hsm_clients.yml            ← HSM Client group defaults
└── host_vars/
    ├── sp-server-01.yml           ← per-host overrides
    ├── ba-client-01.yml
    └── hsm-client-03.yml

roles/
├── sp_server_install/tasks/
│   └── sp_server_configure_petascale.yml
├── ba_client_install/tasks/
│   ├── ba_client_cert_fix.yml
│   └── ba_client_auth_bootstrap.yml
└── hsm_client_install/templates/
    └── hsm_active_binding_policy.j2
```

### 3.3 Configure Inventory File

Create `playbooks/inventory/petascale.ini`:

```ini
[sp_servers]
sp-server-01  ansible_host=9.11.53.28   ansible_user=onecloud-user  ansible_password=<PASSWORD>
sp-server-02  ansible_host=9.11.53.254  ansible_user=onecloud-user  ansible_password=<PASSWORD>

[sp_servers:vars]
ansible_connection=ssh
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
ansible_ssh_private_key_file=~/.ssh/id_rsa
ansible_become=yes
ansible_become_method=sudo

[hsm_clients]
hsm-client-03 ansible_host=p9d-vm4.storage.tucson.ibm.com  ansible_user=root  ansible_password=<PASSWORD>

[hsm_clients:vars]
ansible_connection=ssh
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
ansible_become=yes
ansible_become_method=sudo

[ba_clients]
ba-client-01  ansible_host=9.11.53.28   ansible_user=onecloud-user  ansible_password=<PASSWORD>
ba-client-02  ansible_host=9.11.53.253  ansible_user=onecloud-user
ba-client-03  ansible_host=192.168.1.22 ansible_user=root

[ba_clients:vars]
ansible_connection=ssh
ansible_ssh_common_args='-o StrictHostKeyChecking=no'
ansible_ssh_private_key_file=~/.ssh/id_rsa
ansible_become=yes
ansible_become_method=sudo

[petascale_infrastructure:children]
sp_servers
hsm_clients
ba_clients
```

> **Important — node separation:** Each host may appear in only one group. Mixing roles on the same host is not supported.

### 3.4 Configure Host Variables

Create host-specific configuration files in `playbooks/host_vars/`. These override group and global variables.

**SP Server** (`playbooks/host_vars/sp-server-01.yml`):

```yaml
# ---- Installation ----
sp_server_version: "8.1.27.000"
sp_server_state: "present"
sp_server_action: "install"
sp_server_package_path: "/tmp/8.1.27.000-IBM-SPSRV-LIC-DEBUG-Linuxx86_64-162.bin"
sp_server_install_dest: "/opt/sp_server_binary/"
sp_server_instance_dir: "/opt/tivoli/tsm/server1/TSMServer1"

# ---- Server identity (used by configure playbook) ----
server_name: "PETASCALE-SP01"
server_password: "IBMSPServer@@123456789"
admin_name: "admin"
admin_password: "admin@@123456789"
secure_port: "9443"
ssl_password: "YourSSLPassword@@123"
ssl_password_confirm: "{{ ssl_password }}"

# ---- TSM OS user ----
tsm_user: "tsminst1"
tsm_user_uid: "10001"
tsm_group: "tsmusers"
tsm_group_gid: "10001"
tsm_user_password: "Tsmuser@@123456789"

# ---- Sizing ----
server_size: "xsmall"             # xsmall | small | medium | large
sp_server_active_log_size: 30000  # MB — override only if needed

# ---- GPFS Policy Bootstrap ----
gpfs_policy_bootstrap_enabled: true
gpfs_storage_pool_name: "GPFSPOOL"
gpfs_storage_pool_directory: "/tmp/data"
gpfs_storage_pool_max_size: "100G"
gpfs_policy_domain: "GPFS_DOMAIN"
gpfs_policy_set: "STANDARD"
gpfs_mgmt_class: "GPFS_DAILY"
gpfs_copygroup_verexists: 30
gpfs_copygroup_verdeleted: 60
gpfs_copygroup_retextra: 30
gpfs_copygroup_retonly: 90
```

**HSM Client** (`playbooks/host_vars/hsm-client-03.yml`):

```yaml
# ---- Installation ----
hsm_client_version: "8.2.0.0"
os_type: "LinuxX86"
hsm_client_package_path: "/tmp/8.2.0.0-20251225A-TIV-TSMHSM-LinuxPLEGPFS.tar"
tar_file_location: "remote"
hsm_client_extract_dest: "/opt/hsmClient"
hsm_client_start_daemon: false
hsm_client_state: "present"

# ---- GPFS settings (required for configure playbook) ----
gpfs_filesystem: "/gpfs_main"
hsm_node_password: "P9dVm4Password@@123"
hsm_policy_domain: "GPFS_DOMAIN"

# ---- Single-server connection ----
sp_server_name: "PETASCALE-SP01"
sp_server_address: "9.11.53.0"
sp_server_port: "1500"
node_name: "hsm-client-03"

# ---- Multi-server connection (comment out single-server above if using this) ----
# sp_servers:
#   - name: "PETASCALE-SP01"
#     address: "9.11.53.28"
#     port: "1500"
#     node_name: "hsm-client-03-sp01"
#     domain: "/gpfs_main/fileset_2"
#     inventory_name: "sp-server-01"
#   - name: "PETASCALE-SP03"
#     address: "9.11.53.254"
#     port: "1500"
#     node_name: "hsm-client-03-sp03"
#     domain: "/gpfs_main/fileset_3"
#     inventory_name: "sp-server-02"
# default_server: "PETASCALE-SP01"
```

**BA Client** (`playbooks/host_vars/ba-client-01.yml`):

```yaml
# ---- Installation ----
ba_client_version: "8.1.27.0"
os_type: "LinuxX86"
ba_client_package_path: "/tmp/8.1.27.0-TIV-TSMBAC-LinuxX86.tar"
ba_client_extract_dest: "/opt/baClient"
ba_client_temp_dest: "/tmp/"
ba_client_start_daemon: false
ba_client_state: "present"

# ---- Single-server connection ----
sp_server_name: "PETASCALE-SP01"
sp_server_address: "9.11.53.254"
sp_server_port: "1500"
node_name: "ba-client-01"

# ---- Multi-server connection (comment out single-server above if using this) ----
# sp_servers:
#   - name: "PETASCALE-SP01"
#     address: "9.11.53.28"
#     port: "1500"
#     node_name: "ba-client-01-sp01"
#     domain: "/gpfs_main/fileset_1"
#     inventory_name: "sp-server-01"
#   - name: "PETASCALE-SP02"
#     address: "9.11.53.254"
#     port: "1500"
#     node_name: "ba-client-01-sp02"
#     domain: "/gpfs_main/fileset_2"
#     inventory_name: "sp-server-02"
# default_server: "PETASCALE-SP01"
```

### 3.5 Configure Group Variables

**`playbooks/group_vars/all.yml`** — global defaults:

| Variable | Default | Description |
|---|---|---|
| `software_version` | `"8.2.1.0"` | Default software version |
| `os_type` | `"LinuxX86"` | Default OS type |
| `package_location` | `"/tmp"` | Default package directory on remote nodes |
| `ansible_python_interpreter` | `/usr/bin/python3.9` | Python interpreter (auto-detected per OS) |
| `ansible_become` | `yes` | Privilege escalation |
| `ansible_become_method` | `sudo` | Escalation method |

**`playbooks/group_vars/sp_servers.yml`** — SP Server defaults:

| Variable | Default | Description |
|---|---|---|
| `sp_server_version` | `"8.2.2.000"` | Version used for package matching |
| `server_size` | `"medium"` | xsmall / small / medium / large |
| `sp_server_active_log_size` | `131072` MB | Active log size (overrideable per host) |
| `imcl_path` | `/opt/IBM/InstallationManager/eclipse/tools/imcl` | IBM Installation Manager path |
| `admin_name` | `"admin"` | SP Server admin username |
| `tsm_user` | `"tsminst1"` | OS-level TSM user |
| `tsm_group` | `"tsmusers"` | OS-level TSM group |

### 3.6 Prepare Software Packages on Remote Nodes

Packages must be placed directly on the **remote target nodes**, not on the control node.

**Option A — Copy using Ansible:**

```bash
# SP Server packages
ansible sp_servers -i playbooks/inventory/petascale.ini -m copy \
  -a "src=/local/path/8.1.27.000-IBM-SPSRV-LIC-DEBUG-Linuxx86_64-162.bin dest=/tmp/ mode=0755" \
  --become

# HSM Client packages
ansible hsm_clients -i playbooks/inventory/petascale.ini -m copy \
  -a "src=/local/path/8.1.25.0-TIV-TSMHSM-LinuxX86.tar dest=/tmp/ mode=0644" \
  --become

# BA Client packages
ansible ba_clients -i playbooks/inventory/petascale.ini -m copy \
  -a "src=/local/path/8.1.25.0-TIV-TSMBAC-LinuxX86.tar dest=/tmp/ mode=0644" \
  --become
```

**Option B — Copy with scp:**

```bash
scp 8.1.27.000-IBM-SPSRV-LIC-DEBUG-Linuxx86_64-162.bin root@sp-server-01:/tmp/
scp 8.1.25.0-TIV-TSMHSM-LinuxX86.tar root@hsm-client-03:/tmp/
scp 8.1.25.0-TIV-TSMBAC-LinuxX86.tar root@ba-client-01:/tmp/
```

### 3.7 Test Connectivity

```bash
# Test SSH connectivity to all hosts
ansible all -i playbooks/inventory/petascale.ini -m ping

# Verify Python 3.9 on all nodes
ansible all -i playbooks/inventory/petascale.ini -m raw -a "python3.9 --version"

# Verify packages exist on nodes
ansible all -i playbooks/inventory/petascale.ini -m shell \
  -a "ls -lh /tmp/*.tar* /tmp/*.bin 2>/dev/null || echo 'No packages found'" \
  --become
```

---

## 4. Quick Start Guide

### 4.1 Step 1 — Install All Components

```bash
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini \
  --tags install
```

> **Note:** The `--tags install` flag is required as a safety measure for SP Server installation.

### 4.2 Step 2 — Configure All Components

```bash
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini
```

### 4.3 Step 3 — Verify

```bash
# SP Server — verify process and port
ansible sp_servers -i playbooks/inventory/petascale.ini -m shell \
  -a "ps -ef | grep dsmserv | grep -v grep && netstat -tuln | grep 1500" --become

# HSM Client
ansible hsm_clients -i playbooks/inventory/petascale.ini -m shell \
  -a "rpm -q TIVsm-HSM && dsmc -version" --become

# BA Client
ansible ba_clients -i playbooks/inventory/petascale.ini -m shell \
  -a "rpm -q TIVsm-BA && dsmc query session" --become
```

### 4.4 Quick Uninstallation

```bash
ansible-playbook playbooks/petascale_uninstall.yml \
  -i playbooks/inventory/petascale.ini \
  -e "confirm_uninstall=yes"
```

---

## 5. Configuration Guide — Variables & Files

### 5.1 Variable Precedence (highest → lowest)

1. **Command-line variables** (`-e` flag) — highest priority
2. **Host variables** (`playbooks/host_vars/<hostname>.yml`)
3. **Group variables** (`playbooks/group_vars/<groupname>.yml`)
4. **Global variables** (`playbooks/group_vars/all.yml`)
5. **Role defaults** — lowest priority

### 5.2 Complete Variable Reference

#### SP Server Variables

| Variable | Required | Description | Example |
|---|---|---|---|
| `sp_server_version` | **Yes** | Version string | `"8.1.27.000"` |
| `sp_server_package_path` | **Yes** | Full path to `.bin` on remote node | `"/tmp/8.1.27.000-IBM-SPSRV-LinuxX86_64.bin"` |
| `sp_server_state` | **Yes** | `present` / `absent` / `upgrade` | `"present"` |
| `sp_server_action` | **Yes** | `install` / `upgrade` | `"install"` |
| `sp_server_install_dest` | No | Installation directory | `"/opt/sp_server_binary/"` |
| `server_name` | **Yes** | Unique SP Server name | `"PETASCALE-SP01"` |
| `admin_name` | **Yes** | Admin user for dsmadmc | `"admin"` |
| `admin_password` | **Yes** | Admin password | `"admin@@123456789"` |
| `tsm_user` | **Yes** | OS TSM user name | `"tsminst1"` |
| `tsm_group` | **Yes** | OS TSM group name | `"tsmusers"` |
| `tsm_user_uid` | **Yes** | UID for TSM user | `"10001"` |
| `tsm_group_gid` | **Yes** | GID for TSM group | `"10001"` |
| `server_size` | No | `xsmall` / `small` / `medium` / `large` | `"medium"` |
| `sp_server_active_log_size` | No | Active log size in MB | `131072` |
| `tcpport` | No (default `1500`) | SP Server TCP port | `1500` |
| `gpfs_policy_bootstrap_enabled` | No | Enable GPFS policy bootstrap | `true` |
| `gpfs_policy_register_nodes` | No | Register client nodes automatically (Testing only) | `false` |
| `gpfs_storage_pool_name` | No | GPFS storage pool name | `"GPFSPOOL"` |
| `gpfs_storage_pool_directory` | No | Directory for storage pool | `"/tmp/data"` |
| `gpfs_policy_domain` | No | TSM policy domain for GPFS | `"GPFS_DOMAIN"` |
| `gpfs_mgmt_class` | No | Management class name | `"GPFS_DAILY"` |
| `imcl_path` | No | IBM IM command-line tool path | `"/opt/IBM/InstallationManager/eclipse/tools/imcl"` |

**Server size → active log mapping:**

| `server_size` | Active log (default) | Max sessions (approx.) |
|---|---|---|
| xsmall | 30,000 MB | 75 |
| small | 65,536 MB | 250 |
| medium | 131,072 MB | 500 |
| large | 262,144 MB | 1,000 |

#### BA Client Variables

| Variable | Required | Description | Example |
|---|---|---|---|
| `ba_client_version` | **Yes** | BA Client version | `"8.1.27.0"` |
| `ba_client_package_path` | **Yes** | Full path to `.tar` on remote node | `"/tmp/8.1.27.0-TIV-TSMBAC-LinuxX86.tar"` |
| `os_type` | **Yes** | `LinuxX86` / `LinuxX86_64` / `LinuxS390X` / `LinuxPPC64LE` | `"LinuxX86"` |
| `ba_client_state` | No (default `present`) | `present` / `absent` | `"present"` |
| `ba_client_extract_dest` | No (default `/opt/baClient`) | Installation directory | `"/opt/baClient"` |
| `ba_client_start_daemon` | No | Start daemon after install | `false` |
| `sp_server_name` | **Yes*** | Server name for dsm.sys stanza | `"PETASCALE-SP01"` |
| `sp_server_address` | **Yes*** | Server IP / hostname | `"9.11.53.254"` |
| `sp_server_port` | **Yes*** | Server port | `"1500"` |
| `node_name` | **Yes*** | Client node name | `"ba-client-01"` |
| `sp_servers` | No | List for multi-server mode | see [Section 9](#9-multi-server-topology) |
| `default_server` | Multi-server only | Default server for `dsm.opt` | `"PETASCALE-SP01"` |
| `gpfs_filesystem` | No | GPFS path added as `DOMAIN` in `dsm.sys` | `"/gpfs_main"` |

*\* Required only for single-server mode; replaced by the `sp_servers` list in multi-server mode.*

#### HSM Client Variables

| Variable | Required | Description | Example |
|---|---|---|---|
| `hsm_client_version` | **Yes** | HSM Client version | `"8.2.0.0"` |
| `hsm_client_package_path` | **Yes** | Full path to `.tar` on remote node | `"/tmp/8.2.0.0-TIV-TSMHSM-LinuxPLEGPFS.tar"` |
| `tar_file_location` | **Yes** | `remote` / `controller` | `"remote"` |
| `os_type` | **Yes** | OS type | `"LinuxX86"` |
| `hsm_client_extract_dest` | No (default `/opt/hsmClient`) | Installation directory | `"/opt/hsmClient"` |
| `hsm_client_start_daemon` | No | Start daemon after install | `false` |
| `hsm_client_state` | No (default `present`) | `present` / `absent` | `"present"` |
| `gpfs_filesystem` | **Yes** | GPFS filesystem path | `"/gpfs_main"` |
| `sp_server_name` | **Yes*** | SP Server name | `"PETASCALE-SP01"` |
| `sp_server_address` | **Yes*** | SP Server address | `"9.11.53.0"` |
| `sp_server_port` | **Yes*** | SP Server port | `"1500"` |
| `node_name` | **Yes*** | HSM node name on server | `"hsm-client-03"` |
| `hsm_node_password` | **Yes** | Node password for registration | `"P9dVm4Password@@123"` |
| `hsm_policy_domain` | No | Policy domain name on server | `"GPFS_DOMAIN"` |
| `sp_servers` | No | Multi-server list (includes `domain` per entry) | see [Section 9](#9-multi-server-topology) |
| `default_server` | Multi-server only | Default server name | `"PETASCALE-SP01"` |

*\* Required only for single-server mode.*

---

## 6. Installation Operations

### 6.1 Playbook Execution Flow

1. **OS Detection** — Detects Linux vs AIX, sets Python interpreter path
2. **Dependency Validation** — Checks Python 3.9+, Java, lsof, rsync, `/tmp` permissions, mount options, and disk space
3. **System Requirements Check** *(SP Server only)* — Validates `/tmp` mount options and permissions
4. **Component Installation** — Checks if already installed (idempotent), validates package availability, installs software
5. **Installation Summary** — Reports already-installed nodes, new installations, and failures

### 6.2 Install All Components

```bash
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini \
  --tags install
```

### 6.3 Install Only BA Client and HSM Client (Skip SP Server)

```bash
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini \
  --limit 'all:!sp_servers'
```

### 6.4 Install Specific Component Groups

```bash
# BA Clients only
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini \
  --limit ba_clients

# HSM Clients only
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini \
  --limit hsm_clients

# SP Servers only
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini \
  --limit sp_servers \
  --tags install
```

### 6.5 Install on Specific Hosts

```bash
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini \
  --limit ba-client-01,hsm-client-03

ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini \
  --limit sp-server-01 \
  --tags install
```

### 6.6 Install with Custom Variables

```bash
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini \
  -e "ba_client_version=8.1.26.0" \
  --tags install
```

### 6.7 Dry Run (Check Mode)

```bash
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini \
  --check
```

---

## 7. Post-Install Configuration

### 7.1 What `petascale_configure.yml` Configures

| Component | What is Configured |
|---|---|
| **SP Server** | DB2 instance, `dsmserv.opt`, database format, GPFS policy bootstrap, admin registration, firewall |
| **BA Client** | `dsm.sys` / `dsm.opt`, log files, SSL certificate import, auth cache bootstrap |
| **HSM Client** | `dsm.sys` / `dsm.opt`, DMAPI enablement, filesystem HSM registration, active server binding, DR documentation |

### 7.2 Execution Order

1. OS detection (all nodes)
2. Python 3.9 check (all nodes)
3. SP Server pre-checks
4. SP Server configuration
5. BA Client configuration
6. HSM Client configuration
7. Summary report (localhost)

### 7.3 SP Server Configuration — What Happens

**Phase 1 — TSM user & group setup**
- Creates OS group `tsm_group` with GID `tsm_group_gid`
- Creates OS user `tsm_user` with UID `tsm_user_uid`, home `/home/tsminst1`
- Sets user password, fixes home directory ownership

**Phase 2 — Directory & DB2 instance**
- Creates base, db, alog, and archlog directories under `/home/{{ tsm_user }}`
- Fixes `/opt/tivoli/tsm/db2` ownership for `db2icrt`
- Creates DB2 instance (`db2icrt -a server -u tsminst1 tsminst1`) — skipped if already exists
- Configures `LD_LIBRARY_PATH` in `sqllib/userprofile`

**Phase 3 — Server options file (`dsmserv.opt`)**
- Copies `dsmserv.opt.smp` to the base directory (first run only)
- Adds / updates: `commmethod tcpip`, `tcpport`, `ACTIVELOGSIZE`, `COMMTIMEOUT`, `DEDUPREQUIRESBACKUP`, `EXPINTERVAL`
- Validates available disk space

**Phase 4 — Database format & admin registration**
- If dsmserv is already running — skips format; checks whether admin already exists
- If not running — formats database with `dsmserv format` (async, up to 30 min timeout)
- Runs `register admin`, `grant authority`, then `halt` via stdin pipe
- Starts server in background; waits for TCP port to become available

**Phase 5 — Firewall (SP Server node)**
- Opens TCP port `tcpport` (default 1500) in `firewalld` — both runtime and permanent rules
- Skipped if firewalld is not active

**Phase 6 — GPFS policy bootstrap (if `gpfs_policy_bootstrap_enabled: true`)**
- Storage pool (`define stgpool`) + storage pool directory
- Policy domain (`define domain`), policy set, management class with backup copy group
- Assigns default management class, validates and activates policy set
- Registers HSM client nodes that reference this SP Server
- Each step queries the server first and only runs `define` commands when the object does not already exist

### 7.4 BA Client Configuration — What Happens

**Detection** — checks for `/opt/tivoli/tsm/client/ba/bin`. If absent, configuration is skipped.

**Configuration mode** — if `sp_servers` list is defined → multi-server mode; otherwise → single-server mode.

**`dsm.sys` generation** — written to `/opt/tivoli/tsm/client/ba/bin/dsm.sys`. Single-server example:

```
SERVERNAME PETASCALE-SP01
  COMMMethod         TCPip
  TCPPort            1500
  TCPServeraddress   9.11.53.254
  NODename           ba-client-01
  PASSWORDACCESS     GENERATE
  ERRORLOGNAME       /var/log/tsm/dsmerror_petascale-sp01.log
  SCHEDLOGNAME       /var/log/tsm/dsmsched_petascale-sp01.log
  DOMAIN             /gpfs_main     ← only if gpfs_filesystem is set
```

**`dsm.opt` generation** — written to `/opt/tivoli/tsm/client/ba/bin/dsm.opt`. Contains `SERVERNAME <default_server>`.

**Log directory** — creates `/var/log/tsm/` (mode `0777`), touches `dsmerror.log` / `dsmsched.log` (mode `0666`).

**SSL certificate import (`ba_client_cert_fix.yml`)**
- Tests connection with `dsmadmc`; detects ANS1695E, ANS1592E, ANS1593E
- Multi-server: fetches `cert256.arm` from each SP Server → copies to client → runs `dsmcert -add` per server
- Single-server: extracts cert via `openssl s_client` → runs `dsmcert -add`

**Auth cache bootstrap (`ba_client_auth_bootstrap.yml`)**
- Requires `expect` on the client node (skipped with a warning if absent)
- Performs a PROMPT → GENERATE sequence to populate the auto-generated password cache
- Validates non-interactive `dsmc query session` succeeds

### 7.5 HSM Client Configuration — What Happens

**Phase 1 — Detection** — checks `/opt/tivoli/tsm/client/hsm/bin`. Skipped if absent.

**Phase 2 — Command validation** — verifies TSM commands (`dsmmigfs`, `dsmmigrate`, `dsmrecall`, `dsmc`). In multi-server mode also checks GPFS commands.

**Phase 3 — `dsm.sys` / `dsm.opt` generation** — same logic as BA Client. In multi-server mode, `dsm.opt` also includes HSM-specific directives:

```
SERVERNAME PETASCALE-SP01
HSMMULTISERVER            YES
HSMEXTOBJIDATTR           YES
HSMENABLEIMMEDIATEMIGRATE YES
HSMDISABLEAUTOMIGDAEMONS  YES
```

**Phase 4 — DMAPI enablement** *(multi-server only)* — queries DMAPI status; if disabled: unmounts filesystem → enables DMAPI → remounts.

**Phase 5 — HSM filesystem registration** *(multi-server only)* — queries `dsmmigfs query /gpfs_main`; if not managed runs `dsmmigfs add /gpfs_main`.

**Phase 6 — Active server binding** *(multi-server, 2+ servers)* — generates GPFS policy from template; applies with `mmapplypolicy`; creates disaster recovery documentation at `/gpfs2/config/fileset_server_mapping_<host>.txt`.

**Phase 7 — SSL certificates & auth bootstrap** — same as BA Client.

**Phase 8 — Comprehensive validation report** — validates and prints status for DMAPI, firewall port 1500, config file existence, SSL certs, connectivity to all SP Servers, active server binding, GPFS HSM management.

### 7.6 Running the Configure Playbook

#### Configure all components

```bash
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini
```

#### Configure only SP Servers (skip BA/HSM clients)

```bash
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini \
  -e "configure_clients=false"
```

#### Configure only BA/HSM Clients (skip SP Servers)

```bash
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini \
  -e "configure_servers=false"
```

#### Configure a single host

```bash
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini \
  --limit sp-server-01
```

#### Configure only BA Clients (by group)

```bash
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini \
  --limit ba_clients
```

#### Dry run (check mode)

```bash
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini \
  --check
```

#### Override `server_size` at runtime

```bash
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini \
  --limit sp-server-01 \
  -e "server_size=xsmall"
```

#### Configure playbook tags

| Tag | What it runs |
|---|---|
| `ba_client_config` | BA Client configuration play only |
| `hsm_client_config` | HSM Client configuration play only |
| `always` | OS detection (always runs) |

---

## 8. Uninstallation Operations

### 8.1 What Gets Removed vs. Preserved

**Removed:**

| Component | What Is Removed |
|---|---|
| SP Server | Software (via Installation Manager), instance (stopped), `dsmserv` processes |
| HSM Client | Software packages (RPMs: TIVsm-HSM) |
| BA Client | Software packages (RPMs: TIVsm-BA), `dsmcad.service` stopped, processes terminated |

**Preserved:**

- Configuration files (backed up to `.bk` files)
- RPM packages (backed up to `/opt/*ClientPackagesBk`)
- Backed-up data, node registrations, backup history, and database files on SP Server

### 8.2 Uninstall All Components

```bash
# Step 1: Preview what will be removed (no confirmation needed)
ansible-playbook playbooks/petascale_uninstall.yml \
  -i playbooks/inventory/petascale.ini

# Step 2: Proceed with uninstall
ansible-playbook playbooks/petascale_uninstall.yml \
  -i playbooks/inventory/petascale.ini \
  -e "confirm_uninstall=yes"
```

### 8.3 Uninstall Specific Component Groups

```bash
# SP Servers only
ansible-playbook playbooks/petascale_uninstall.yml \
  -i playbooks/inventory/petascale.ini \
  -e "confirm_uninstall=yes" \
  --limit sp_servers

# HSM Clients only
ansible-playbook playbooks/petascale_uninstall.yml \
  -i playbooks/inventory/petascale.ini \
  -e "confirm_uninstall=yes" \
  --limit hsm_clients

# BA Clients only
ansible-playbook playbooks/petascale_uninstall.yml \
  -i playbooks/inventory/petascale.ini \
  -e "confirm_uninstall=yes" \
  --limit ba_clients
```

### 8.4 Uninstall Specific Hosts

```bash
ansible-playbook playbooks/petascale_uninstall.yml \
  -i playbooks/inventory/petascale.ini \
  -e "confirm_uninstall=yes" \
  --limit ba-client-01,hsm-client-03

ansible-playbook playbooks/petascale_uninstall.yml \
  -i playbooks/inventory/petascale.ini \
  -e "confirm_uninstall=yes" \
  --limit sp-server-01
```

### 8.5 Dry Run (Check Mode)

```bash
ansible-playbook playbooks/petascale_uninstall.yml \
  -i playbooks/inventory/petascale.ini \
  -e "confirm_uninstall=yes" \
  --check
```

---

## 9. Multi-Server Topology

Petascale deployments direct different GPFS filesets to different SP Servers to achieve horizontal scale. The `sp_servers` list in a client's host_vars file drives this behaviour.

```yaml
# In hsm-client-03.yml (or ba-client-01.yml)
sp_servers:
  - name: "PETASCALE-SP01"
    address: "9.11.53.28"
    port: "1500"
    node_name: "hsm-client-03-sp01"
    domain: "/gpfs_main/fileset_2"       # GPFS fileset path this server owns
    inventory_name: "sp-server-01"        # must match inventory hostname (for cert fetch)
  - name: "PETASCALE-SP03"
    address: "9.11.53.254"
    port: "1500"
    node_name: "hsm-client-03-sp03"
    domain: "/gpfs_main/fileset_3"
    inventory_name: "sp-server-02"

default_server: "PETASCALE-SP01"          # used in dsm.opt SERVERNAME line
```

> **Active server binding:** The DMAPI attribute `dmapi.IBMServ` is set on files in each fileset directory, telling the HSM client which SP Server to use for migrate/recall operations. The playbook sets this attribute automatically using `mmapplypolicy`.

### Multi-server `dsm.opt` directives explained

| Option | Meaning |
|---|---|
| `HSMMULTISERVER YES` | Enables multi-server HSM support |
| `HSMEXTOBJIDATTR YES` | Stores extended object ID in DMAPI attributes for server routing |
| `HSMENABLEIMMEDIATEMIGRATE YES` | Allows immediate migration without waiting for recall policy |
| `HSMDISABLEAUTOMIGDAEMONS YES` | Disables automatic migration daemons (manual control) |

---

## 10. Post-Run Validation

### 10.1 SP Server

```bash
# Verify server process is running
ps -ef | grep dsmserv | grep -v grep

# Verify port is listening
netstat -tuln | grep 1500

# Test admin connection
/opt/tivoli/tsm/server/bin/dsmadmc -id=admin -password=admin@@123456789 "query status"

# Verify GPFS storage pool (if bootstrap enabled)
/opt/tivoli/tsm/server/bin/dsmadmc -id=admin -password=admin@@123456789 "query stgpool GPFSPOOL"

# Verify policy domain
/opt/tivoli/tsm/server/bin/dsmadmc -id=admin -password=admin@@123456789 "query domain GPFS_DOMAIN"

# Verify via IBM Installation Manager
/opt/IBM/InstallationManager/eclipse/tools/imcl listInstalledPackages
```

### 10.2 BA Client

```bash
# Check config files exist
ls -la /opt/tivoli/tsm/client/ba/bin/dsm.sys
ls -la /opt/tivoli/tsm/client/ba/bin/dsm.opt

# Test connection to default server
dsmc query session

# Multi-server: test per server
dsmc query session -servername=PETASCALE-SP01

# Verify package installed
ansible ba_clients -i playbooks/inventory/petascale.ini -m shell \
  -a "rpm -q TIVsm-BA" --become
```

### 10.3 HSM Client

```bash
# Check config files
ls -la /opt/tivoli/tsm/client/hsm/bin/dsm.sys
ls -la /opt/tivoli/tsm/client/hsm/bin/dsm.opt

# Verify DMAPI is enabled
/usr/lpp/mmfs/bin/mmlsfs gpfs_main -z

# Verify filesystem is HSM-managed
dsmmigfs query /gpfs_main

# Verify active server binding on a test file (multi-server)
mmlsattr -d -L /gpfs_main/fileset_2/test_binding_PETASCALE-SP01.txt | grep IBMServ

# Test connectivity
dsmc query session -servername=PETASCALE-SP01

# Review disaster recovery documentation
cat /gpfs2/config/fileset_server_mapping_hsm-client-03.txt

# Verify package installed
ansible hsm_clients -i playbooks/inventory/petascale.ini -m shell \
  -a "rpm -q TIVsm-HSM" --become
```

---

## 11. Troubleshooting

### 11.1 Installation Issues

#### Dependency Validation Fails

**Error:**
```
DEPENDENCY VALIDATION FAILED - hostname
Missing or misconfigured dependencies detected.
```

**Solution:**
```bash
# Production (recommended): install dependencies manually per the remediation report

# Non-production: auto-install
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini \
  -e "install_dependencies=true" \
  --tags install
```

> **Note:** Some dependencies like `/tmp` mount options must always be fixed manually.

#### Package Not Found on Remote Node

**Error:**
```
FAILED! => {"msg": "Package not found on <hostname>! Expected location: /tmp/<package>.tar"}
```

**Solution:**
```bash
scp <package>.tar root@<hostname>:/tmp/
ansible <hostname> -i playbooks/inventory/petascale.ini -m stat \
  -a "path=/tmp/<package>.tar" --become
```

#### Python 3.9 Not Found

**Error:**
```
WARNING: Python 3.9 is ABSENT on <hostname>
```

**Solution:**
```bash
yum install python39       # RHEL/CentOS/AIX
apt-get install python3.9  # Ubuntu/Debian
```

#### /tmp Mounted with `noexec` (SP Server)

**Error:**
```
ERROR: /tmp is mounted with 'noexec' flag on <hostname>
```

**Solution:**
```bash
sudo mount -o remount,exec /tmp      # temporary fix
# Permanent: remove 'noexec' from /etc/fstab /tmp entry, then remount
```

#### /tmp Wrong Permissions (SP Server)

**Error:**
```
ERROR: /tmp has incorrect permissions on <hostname>. Current: 755, Required: 1777
```

**Solution:**
```bash
sudo chmod 1777 /tmp
```

#### Component Already Installed

The playbook skips installation and reports the node as `already_installed`. To force reinstall: run the uninstall playbook first, then the install playbook.

#### Architecture Mismatch

**Error:**
```
ERROR: Unsupported architecture: <arch>
```

Ensure you are using the correct package for your system architecture (x86_64, s390x, ppc64le).

### 11.2 Configuration Issues

#### SP Server: "dsmserv binary not found"

SP Server installation did not complete. Run `petascale_install.yml` first.

#### SP Server: "Active log size exceeds available space"

```bash
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini \
  --limit sp-server-01 \
  -e "server_size=xsmall"
```

#### SP Server: Configuration hangs at DB format

Database formatting can take 5–20 minutes. Default async timeout is 1800 s. Increase if needed:

```bash
ansible-playbook playbooks/petascale_configure.yml ... -e "db_format_timeout=3600"
```

#### BA / HSM Client: Variables not being applied

1. Verify `host_vars/` filename matches the inventory hostname exactly (case-sensitive)
2. Check YAML syntax: `yamllint playbooks/host_vars/ba-client-01.yml`
3. Inspect resolved variables: `ansible-inventory -i playbooks/inventory/petascale.ini --host ba-client-01 --yaml`

#### BA / HSM Client: SSL / Certificate error (ANS1695E)

The `cert_fix` task handles this automatically. If it fails:
- Ensure `cert256.arm` exists in `/home/tsminst1/` on the SP Server; generate if missing: `dsmadmc "generate cert256"`
- In multi-server mode, `inventory_name` in the `sp_servers` list must match the SP Server's exact inventory hostname

#### BA / HSM Client: Auth bootstrap skipped

Install `expect` on the client node then re-run:

```bash
yum install -y expect       # RHEL/CentOS
apt-get install -y expect   # Ubuntu/Debian
```

#### HSM Client: DMAPI enablement fails

DMAPI enablement requires the GPFS filesystem to be unmounted. Stop all processes using the filesystem, then re-run the playbook.

#### HSM Client: "not managed by space management"

```bash
export PATH=$PATH:/opt/tivoli/tsm/client/hsm/bin
dsmmigfs add /gpfs_main
```

#### HSM Client: Active server binding shows "NOT SET"

```bash
mmapplypolicy /gpfs_main \
  -P /tmp/hsm_active_binding_policy_hsm-client-03.txt \
  -I defer
```

### 11.3 Debugging

#### Enable Verbose Output

```bash
ansible-playbook playbooks/petascale_install.yml -v     # basic info
ansible-playbook playbooks/petascale_install.yml -vv    # more details
ansible-playbook playbooks/petascale_install.yml -vvv   # debug level
ansible-playbook playbooks/petascale_install.yml -vvvv  # connection debug
```

#### Log File Locations

| Component | Log location |
|---|---|
| SP Server startup | `/home/tsminst1/server.out` |
| SP Server admin register | `/home/tsminst1/admin_register.log` |
| BA Client errors | `/var/log/tsm/dsmerror.log` |
| BA Client schedule | `/var/log/tsm/dsmsched.log` |
| HSM Client errors | `/var/log/tsm/dsmerror.log` |
| Ansible output | stdout / set `ansible_log_path` in `group_vars/all.yml` |

#### Enable Ansible Logging

```ini
# ansible.cfg
[defaults]
log_path = /var/log/ansible.log
```

---

## 12. Best Practices

### Pre-Installation

**Do:**
- Verify node separation (SP Server on its own nodes)
- Check disk space (minimum 20 GB free in `/tmp`)
- Test SSH connectivity to all hosts before running playbooks
- Review system requirements for each component type
- Test in a non-production environment first

**Avoid:**
- Installing BA/HSM Client on the same node as SP Server
- Skipping prerequisite and dependency validation
- Ignoring architecture mismatch warnings

### During Installation & Configuration

**Do:**
- Monitor playbook progress
- Use verbose mode (`-v`) for troubleshooting
- Keep package sources available on remote nodes until installation is confirmed successful

**Avoid:**
- Interrupting running playbooks
- Modifying files during installation
- Running multiple installations simultaneously on the same host

### Post-Installation

**Do:**
- Verify installation success for each component (Section 10)
- Test component connectivity
- Register client nodes with SP Server
- Back up configuration files

**Avoid:**
- Deleting package sources immediately after installation
- Skipping post-installation verification
- Leaving default passwords in place

### Configuration Management

**Do:**
- Use version control for playbooks and variable files
- Store sensitive data in Ansible Vault
- Use host and group variables for environment-specific settings

**Avoid:**
- Hardcoding passwords in playbooks
- Storing credentials in plain text
- Making manual changes without documentation

---

## 13. FAQ

### Q: Can I install all three components on the same node?

No. SP Server must be on a separate node from BA Client and HSM Client due to incompatible GSKit versions.

### Q: Is the automation idempotent?

Yes. You can run the playbooks multiple times safely. If a component is already installed or configured, the relevant step is skipped.

### Q: What happens if installation fails?

The automation automatically rolls back changes, removing any partially installed packages and restoring the system to its previous state.

### Q: Can I install on multiple hosts simultaneously?

Yes. Use Ansible's fork parameter:

```bash
ansible-playbook playbooks/petascale_install.yml -f 10
```

### Q: Do I need to place packages on the control node?

No. Packages must be placed directly on the **remote target nodes** in `/tmp/`.

### Q: How do I apply different settings to different hosts?

Use host variable files in `playbooks/host_vars/<hostname>.yml`. These override group and global variables.

### Q: How do I set a default version for all BA Clients?

Set the variable in `playbooks/group_vars/ba_clients.yml`.

### Q: What is the purpose of `--tags install` for SP Server?

It is a deliberate safety gate to prevent accidental SP Server installations. It must be explicitly passed.

### Q: What is the purpose of `gpfs_policy_bootstrap_enabled`?

When set to `true`, the configure playbook creates the minimum working TSM policy on the SP Server (storage pool, policy domain, management class) required for GPFS/HSM workloads. Each step is idempotent — re-running is safe.

### Q: Which Linux distributions are supported?

SP Server supports Linux. HSM and BA Clients support Linux and AIX.

### Q: What architectures are supported?

x86_64, s390x, and ppc64le for Linux components. ppc64 for AIX (HSM Client).

### Q: Is upgrade supported?

Upgrade automation is planned as future work. A `petascale_upgrade.yml` playbook exists in the repository but is not yet fully validated for production use.

---

## 14. Appendices

### 14.1 Command Reference

#### Installation Commands

```bash
# Full installation
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini --tags install

# Clients only
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini --limit 'all:!sp_servers'

# Specific group
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini --limit ba_clients

# Dry run
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini --check

# Step-by-step
ansible-playbook playbooks/petascale_install.yml \
  -i playbooks/inventory/petascale.ini --step
```

#### Configuration Commands

```bash
# Configure all
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini

# SP Servers only
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini -e "configure_clients=false"

# Clients only
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini -e "configure_servers=false"

# Override server_size
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini --limit sp-server-01 -e "server_size=xsmall"

# Dry run
ansible-playbook playbooks/petascale_configure.yml \
  -i playbooks/inventory/petascale.ini --check
```

#### Uninstallation Commands

```bash
# Full uninstall
ansible-playbook playbooks/petascale_uninstall.yml \
  -i playbooks/inventory/petascale.ini -e "confirm_uninstall=yes"

# Specific group
ansible-playbook playbooks/petascale_uninstall.yml \
  -i playbooks/inventory/petascale.ini \
  -e "confirm_uninstall=yes" --limit ba_clients

# Dry run
ansible-playbook playbooks/petascale_uninstall.yml \
  -i playbooks/inventory/petascale.ini \
  -e "confirm_uninstall=yes" --check
```

#### Ad-hoc Commands

```bash
# Check BA Client version
ansible ba_clients -i playbooks/inventory/petascale.ini \
  -m shell -a "rpm -q TIVsm-BA"

# Check HSM Client version
ansible hsm_clients -i playbooks/inventory/petascale.ini \
  -m shell -a "rpm -q TIVsm-HSM"

# Check /tmp disk space
ansible all -i playbooks/inventory/petascale.ini \
  -m shell -a "df -h /tmp"

# Check /tmp mount options
ansible all -i playbooks/inventory/petascale.ini \
  -m shell -a "mount | grep /tmp"
```

### 14.2 Ansible Configuration (`ansible.cfg`)

```ini
[defaults]
inventory = playbooks/inventory/petascale.ini
remote_user = root
host_key_checking = False
timeout = 60
forks = 5
log_path = /var/log/ansible.log
retry_files_enabled = False
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts
fact_caching_timeout = 3600

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
ssh_args = -o ControlMaster=auto -o ControlPersist=60s -o Compression=yes
pipelining = True
```

### 14.3 Pre-Installation Check Script

```bash
#!/bin/bash
# petascale_pre_check.sh — run on each target node

echo "=== Petascale Pre-Installation Check ==="

echo "Checking Python 3.9..."
command -v python3.9 &>/dev/null \
  && echo "OK Python 3.9: $(python3.9 --version)" \
  || echo "MISSING Python 3.9"

echo "Checking Java..."
command -v java &>/dev/null \
  && echo "OK Java: $(java -version 2>&1 | head -1)" \
  || echo "MISSING Java"

echo "Checking /tmp permissions..."
PERMS=$(stat -c "%a" /tmp)
[ "$PERMS" = "1777" ] && echo "OK /tmp: $PERMS" || echo "WRONG /tmp: $PERMS (required: 1777)"

echo "Checking /tmp mount options..."
mount | grep "/tmp" | grep -q "noexec" \
  && echo "FAIL /tmp has noexec flag" \
  || echo "OK /tmp mount options"

echo "Checking /tmp disk space..."
AVAIL=$(df -BG /tmp | tail -1 | awk '{print $4}' | tr -d 'G')
[ "$AVAIL" -ge 20 ] && echo "OK ${AVAIL}GB available" || echo "LOW ${AVAIL}GB (required: 20GB)"

echo "Checking lsof..."
command -v lsof &>/dev/null && echo "OK lsof" || echo "MISSING lsof"

echo "Checking rsync..."
command -v rsync &>/dev/null && echo "OK rsync" || echo "MISSING rsync"

echo "=== Check complete ==="
```

### 14.4 Glossary

| Term | Definition |
|---|---|
| **SP Server** | IBM Storage Protect Server — central server managing backups and archives |
| **HSM Client** | Hierarchical Storage Management Client — automates data migration between storage tiers |
| **BA Client** | Backup-Archive Client — IBM Storage Protect client for backup operations |
| **GPFS / IBM Spectrum Scale** | General Parallel File System — clustered file system required by HSM Client |
| **GSKit** | IBM Global Security Kit — cryptographic library; incompatible versions between SP Server and clients |
| **DMAPI** | Data Management Application Program Interface — required for HSM Client filesystem management |
| **dsmserv.opt** | SP Server options file defining communications, logging, and performance settings |
| **dsm.sys** | Client system options file defining server connection stanzas |
| **dsm.opt** | Client user options file specifying the default server name |
| **Active server binding** | DMAPI attribute (`dmapi.IBMServ`) on GPFS fileset files that routes HSM operations to the correct SP Server |
| **Idempotent** | Operation that produces the same result regardless of how many times it is executed |
| **Rollback** | Reverting changes to a previous state after a failure |
| **Inventory Group** | Ansible grouping of hosts (`sp_servers`, `hsm_clients`, `ba_clients`) |
| **Host Variables** | Per-host configuration overrides stored in `host_vars/<hostname>.yml` |
| **Group Variables** | Group-level configuration stored in `group_vars/<groupname>.yml` |

### 14.5 Support & Resources

- IBM Storage Protect Documentation: https://www.ibm.com/docs/en/storage-protect
- IBM Spectrum Scale Documentation: https://www.ibm.com/docs/en/spectrum-scale
- Ansible Documentation: https://docs.ansible.com/
- Collection Repository: https://github.com/IBM/ansible-storage-protect
- IBM Support: https://www.ibm.com/support
- GitHub Issues: https://github.com/IBM/ansible-storage-protect/issues

---

**End of User Guide**

# Solution 3: Blueprint Configuration Solution

## Overview

**Category:** Blueprint configuration solution  
**Objective:** Infrastructure-as-Code deployment with multi-phase orchestration, golden configurations, and automated provisioning.

**Status:** ✅ Production Ready

## Use Cases

- Automated infrastructure provisioning
- Golden configuration deployment
- Standardized server builds
- CI/CD pipeline integration
- Repeatable deployments across environments

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│           Blueprint Orchestration Pattern                 │
│                                                           │
│  User/CI-CD                                              │
│      │                                                    │
│      ▼                                                    │
│  ┌─────────────────────┐                                │
│  │ Blueprint Playbook  │ (Orchestrator)                 │
│  └──────────┬──────────┘                                │
│             │                                             │
│    ┌────────┼────────┐                                  │
│    ▼        ▼        ▼                                  │
│  Phase 1  Phase 2  Phase 3                              │
│  Install  Storage  Configure                            │
│                                                           │
│  ┌──────────────────────────────────────┐              │
│  │  Validation Between Each Phase       │              │
│  └──────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────┘
```

## Components Included

### Playbooks (7)
- `sp_server_blueprint_playbook.yml` - **Primary orchestrator**
- `sp_server_install_playbook.yml` - Phase 1: Installation
- `storage_prepare_playbook.yml` - Phase 2: Storage preparation
- `sp_server_configure_playbook.yml` - Phase 3: Configuration
- `storage_cleanup_playbook.yml` - Cleanup operations
- `sp_server_facts_playbook.yml` - Validation
- `sp_server_upgrade_playbook.yml` - Upgrade orchestration

### Roles (6)
All roles vendored for complete independence.

## Prerequisites

### System Requirements
- **Ansible:** >=2.15.0
- **Python:** >=3.9
- **CI/CD Integration:** Jenkins, GitLab CI, GitHub Actions, or AWX

### IBM Binaries Required
- IBM Storage Protect Server 8.1.23+

## Quick Start

### 1. Choose Server Size

```yaml
# vars/small_server_vars.yml
storage_size: "small"
db_size: "50GB"
container_pool_size: "500GB"

# vars/medium_server_vars.yml
storage_size: "medium"
db_size: "100GB"
container_pool_size: "2TB"

# vars/large_server_vars.yml
storage_size: "large"
db_size: "500GB"
container_pool_size: "10TB"
```

### 2. Configure Blueprint Variables

```yaml
# vars/blueprint-vars.yml
sp_server_version: "8.1.24"
sp_server_state: "present"
sp_server_bin_repo: "/data/sp-packages/server/8.1.24"
storage_size: "medium"
target_hosts: "sp_servers"
blueprint_version: "1.0"
```

### 3. Deploy Using Blueprint

```bash
# Complete deployment (all phases)
ansible-playbook -i inventory/production.ini \
  playbooks/sp_server_blueprint_playbook.yml \
  -e @vars/blueprint-vars.yml \
  -e @vars/medium_server_vars.yml \
  --vault-password-file .vault_pass
```

## Blueprint Orchestration Flow

```
Pre-Flight Validation
├─> Validate required variables
├─> Check storage size parameter
└─> Display blueprint information

Phase 1: Server Installation
├─> sp_server_install_playbook.yml
└─> Inter-phase validation

Phase 2: Storage Preparation
├─> storage_prepare_playbook.yml
└─> Inter-phase validation

Phase 3: Server Configuration
├─> sp_server_configure_playbook.yml
└─> Post-deployment validation

Post-Deployment
├─> Generate deployment report
├─> Save deployment metadata
└─> Display next steps
```

## CI/CD Integration

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Deploy SP Server') {
            steps {
                ansiblePlaybook(
                    playbook: 'playbooks/sp_server_blueprint_playbook.yml',
                    inventory: 'inventory/production.ini',
                    extras: '-e @vars/blueprint-vars.yml'
                )
            }
        }
    }
}
```

### GitLab CI

```yaml
deploy_sp_server:
  stage: deploy
  script:
    - ansible-playbook -i inventory/production.ini
      playbooks/sp_server_blueprint_playbook.yml
      -e @vars/blueprint-vars.yml
  only:
    - main
```

### GitHub Actions

```yaml
name: Deploy SP Server
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Blueprint
        run: |
          ansible-playbook -i inventory/production.ini \
            playbooks/sp_server_blueprint_playbook.yml \
            -e @vars/blueprint-vars.yml
```

## Configuration Templates

### Golden Configuration

```yaml
# templates/golden_config.yml
deduplication_enabled: true
compression_enabled: true
encryption_enabled: true
session_security: "strict"

storage_pools:
  - name: "DISKPOOL"
    type: "directory"
    maxsize: "{{ container_pool_size }}"
    
policy_domains:
  - name: "STANDARD"
    description: "Standard backup policy"
    retention_days: 90
```

## Validation

### Pre-Deployment Validation

```bash
# Validate configuration
ansible-playbook -i inventory/production.ini \
  playbooks/sp_server_blueprint_playbook.yml \
  --check \
  --diff
```

### Post-Deployment Validation

```bash
# Verify deployment
ansible-playbook -i inventory/production.ini \
  playbooks/sp_server_facts_playbook.yml
```

## Upgrade Orchestration

```bash
# Upgrade using blueprint
ansible-playbook -i inventory/production.ini \
  playbooks/sp_server_upgrade_playbook.yml \
  -e "sp_server_version=8.1.25"
```

## Rollback Procedure

```bash
# Cleanup failed deployment
ansible-playbook -i inventory/production.ini \
  playbooks/storage_cleanup_playbook.yml

# Reinstall with previous version
ansible-playbook -i inventory/production.ini \
  playbooks/sp_server_blueprint_playbook.yml \
  -e "sp_server_version=8.1.23"
```

## Independence Validation

✅ **Can run standalone:** YES  
✅ **External dependencies:** None  
✅ **CI/CD integration:** YES  
✅ **Offline deployment:** YES  
✅ **Reproducible:** YES

## Support

- **Documentation:** `docs/design/design-sp-blueprint-conf-solution.md`
- **Guide:** `docs/guides/sp-blueprint-conf-solution-guide.md`

## Version

- **Solution Version:** 1.0.0
- **Last Updated:** 2026-05-19
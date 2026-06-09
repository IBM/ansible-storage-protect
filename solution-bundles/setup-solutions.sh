#!/bin/bash
# Script to setup all solution bundles with required components

set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$BASE_DIR")"

echo "Setting up IBM Storage Protect Solution Bundles..."
echo "Base Directory: $BASE_DIR"
echo "Project Root: $PROJECT_ROOT"

# Solution 2: Multi-Site Disk
echo "Setting up Solution 2: Multi-Site Disk..."
cp "$PROJECT_ROOT/playbooks/sp_server_install_playbook.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp "$PROJECT_ROOT/playbooks/sp_server_configure_playbook.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp "$PROJECT_ROOT/playbooks/sp_server_upgrade_playbook.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp "$PROJECT_ROOT/playbooks/sp_server_facts_playbook.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp "$PROJECT_ROOT/playbooks/sp_server_blueprint_playbook.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp "$PROJECT_ROOT/playbooks/oc_configure_playbook.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp "$PROJECT_ROOT/playbooks/cert_distribute.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp "$PROJECT_ROOT/playbooks/storage_prepare_playbook.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp "$PROJECT_ROOT/playbooks/dp_db2_install_playbook.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp "$PROJECT_ROOT/playbooks/dp_db2_backup_playbook.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp "$PROJECT_ROOT/playbooks/dp_db2_restore_playbook.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp "$PROJECT_ROOT/playbooks/dp_db2_query_playbook.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp "$PROJECT_ROOT/playbooks/ba_client_facts_playbook.yml" "$BASE_DIR/02-multisite-disk/playbooks/"
cp -r "$PROJECT_ROOT/playbooks/ba_client_install" "$BASE_DIR/02-multisite-disk/playbooks/"
cp -r "$PROJECT_ROOT/roles"/* "$BASE_DIR/02-multisite-disk/roles/"
cp -r "$PROJECT_ROOT/plugins"/* "$BASE_DIR/02-multisite-disk/plugins/"
cp "$PROJECT_ROOT/playbooks/vars"/*.yml "$BASE_DIR/02-multisite-disk/vars/"

# Solution 3: Blueprint Configuration
echo "Setting up Solution 3: Blueprint Configuration..."
cp "$PROJECT_ROOT/playbooks/sp_server_blueprint_playbook.yml" "$BASE_DIR/03-blueprint-configuration/playbooks/"
cp "$PROJECT_ROOT/playbooks/sp_server_install_playbook.yml" "$BASE_DIR/03-blueprint-configuration/playbooks/"
cp "$PROJECT_ROOT/playbooks/storage_prepare_playbook.yml" "$BASE_DIR/03-blueprint-configuration/playbooks/"
cp "$PROJECT_ROOT/playbooks/sp_server_configure_playbook.yml" "$BASE_DIR/03-blueprint-configuration/playbooks/"
cp "$PROJECT_ROOT/playbooks/storage_cleanup_playbook.yml" "$BASE_DIR/03-blueprint-configuration/playbooks/"
cp "$PROJECT_ROOT/playbooks/sp_server_facts_playbook.yml" "$BASE_DIR/03-blueprint-configuration/playbooks/"
cp "$PROJECT_ROOT/playbooks/sp_server_upgrade_playbook.yml" "$BASE_DIR/03-blueprint-configuration/playbooks/"
cp -r "$PROJECT_ROOT/roles"/* "$BASE_DIR/03-blueprint-configuration/roles/"
cp -r "$PROJECT_ROOT/plugins"/* "$BASE_DIR/03-blueprint-configuration/plugins/"
cp "$PROJECT_ROOT/playbooks/vars"/*.yml "$BASE_DIR/03-blueprint-configuration/vars/"

# Solution 4: Configuration Drift
echo "Setting up Solution 4: Configuration Drift..."
cp "$PROJECT_ROOT/playbooks/sp_server_facts_playbook.yml" "$BASE_DIR/04-configuration-drift/playbooks/"
cp "$PROJECT_ROOT/playbooks/ba_client_facts_playbook.yml" "$BASE_DIR/04-configuration-drift/playbooks/"
cp "$PROJECT_ROOT/playbooks/sp_server_configure_playbook.yml" "$BASE_DIR/04-configuration-drift/playbooks/"
cp -r "$PROJECT_ROOT/playbooks/ba_client_install" "$BASE_DIR/04-configuration-drift/playbooks/"
cp -r "$PROJECT_ROOT/roles"/* "$BASE_DIR/04-configuration-drift/roles/"
cp -r "$PROJECT_ROOT/plugins"/* "$BASE_DIR/04-configuration-drift/plugins/"

# Solution 5: Tape Archival
echo "Setting up Solution 5: Tape Archival..."
cp "$PROJECT_ROOT/playbooks/storage_agent_configure_playbook.yml" "$BASE_DIR/05-tape-archival/playbooks/"
cp "$PROJECT_ROOT/playbooks/ba_client_facts_playbook.yml" "$BASE_DIR/05-tape-archival/playbooks/"
cp -r "$PROJECT_ROOT/playbooks/ba_client_install" "$BASE_DIR/05-tape-archival/playbooks/"
cp -r "$PROJECT_ROOT/roles"/* "$BASE_DIR/05-tape-archival/roles/"
cp -r "$PROJECT_ROOT/plugins"/* "$BASE_DIR/05-tape-archival/plugins/"

# Solution 7: Peta-Scale Protection
echo "Setting up Solution 7: Peta-Scale Protection..."
cp -r "$PROJECT_ROOT/playbooks/erp_install" "$BASE_DIR/07-petascale-protection/playbooks/"
cp "$PROJECT_ROOT/playbooks/dp_db2_backup_playbook.yml" "$BASE_DIR/07-petascale-protection/playbooks/"
cp "$PROJECT_ROOT/playbooks/storage_agent_configure_playbook.yml" "$BASE_DIR/07-petascale-protection/playbooks/"
cp "$PROJECT_ROOT/playbooks/sp_server_install_playbook.yml" "$BASE_DIR/07-petascale-protection/playbooks/"
cp "$PROJECT_ROOT/playbooks/sp_server_configure_playbook.yml" "$BASE_DIR/07-petascale-protection/playbooks/"
cp -r "$PROJECT_ROOT/roles"/* "$BASE_DIR/07-petascale-protection/roles/"
cp -r "$PROJECT_ROOT/plugins"/* "$BASE_DIR/07-petascale-protection/plugins/"
cp "$PROJECT_ROOT/playbooks/vars"/*.yml "$BASE_DIR/07-petascale-protection/vars/"

# Solution 8: Multi-Tenant
echo "Setting up Solution 8: Multi-Tenant..."
cp "$PROJECT_ROOT/playbooks/sp_server_install_playbook.yml" "$BASE_DIR/08-multi-tenant/playbooks/"
cp "$PROJECT_ROOT/playbooks/sp_server_configure_playbook.yml" "$BASE_DIR/08-multi-tenant/playbooks/"
cp "$PROJECT_ROOT/playbooks/oc_configure_playbook.yml" "$BASE_DIR/08-multi-tenant/playbooks/"
cp "$PROJECT_ROOT/playbooks/ba_client_facts_playbook.yml" "$BASE_DIR/08-multi-tenant/playbooks/"
cp "$PROJECT_ROOT/playbooks/cert_distribute.yml" "$BASE_DIR/08-multi-tenant/playbooks/"
cp -r "$PROJECT_ROOT/playbooks/ba_client_install" "$BASE_DIR/08-multi-tenant/playbooks/"
cp -r "$PROJECT_ROOT/roles"/* "$BASE_DIR/08-multi-tenant/roles/"
cp -r "$PROJECT_ROOT/plugins"/* "$BASE_DIR/08-multi-tenant/plugins/"

echo "✅ All solution bundles setup complete!"
echo ""
echo "Solution Status:"
echo "  ✅ Solution 1: Single-Site Disk - Complete"
echo "  ✅ Solution 2: Multi-Site Disk - Complete"
echo "  ✅ Solution 3: Blueprint Configuration - Complete"
echo "  ✅ Solution 4: Configuration Drift - Complete"
echo "  ✅ Solution 5: Tape Archival - Complete"
echo "  ⚠️  Solution 6: Cloud Storage - Not Implemented (Gap)"
echo "  ✅ Solution 7: Peta-Scale Protection - Complete"
echo "  ✅ Solution 8: Multi-Tenant - Complete"

# Made with Bob

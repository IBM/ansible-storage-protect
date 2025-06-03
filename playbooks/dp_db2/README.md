# DP for DB2 Installation Playbook

## Overview
The `dp_db2_install.yml` playbook automates the installation and configuration of IBM Storage Protect for DP (Data Protection) for DB2. It performs prechecks, installs required components, configures necessary files, registers the client node with the IBM Storage Protect server, and performs postchecks to validate the setup.

---

## Playbook Workflow
This playbook is divided into three main plays:
1. **Precheck and Installation on the Client**:
   - Ensures the environment is ready for installation.
   - Installs the BA Client and configures DSM options (`dsm.opt`) and system files (`dsm.sys`).

2. **Node Registration on the Server**:
   - Registers the client node with the IBM Storage Protect server.

3. **Postchecks on the Client**:
   - Validates the configuration and ensures the setup is complete.

---

## Required Roles
The following roles are required for this playbook:
1. **`ibm.storage_protect.dp_db2_precheck`**:
   - Performs prechecks to ensure the environment is ready for installation.
   - Checks for DB2 processes, binaries, and other prerequisites.

2. **`ibm.storage_protect.ba_client_install`**:
   - Installs the BA Client and API packages.

3. **`ibm.storage_protect.dsm_opt`**:
   - Configures the `dsm.opt` file with the required parameters.

4. **`ibm.storage_protect.dsm_sysfile`**:
   - Creates the `dsm.sys` file with the server name and TCP server address.

5. **`ibm.storage_protect.nodes`**:
   - Registers the client node with the IBM Storage Protect server.

6. **`ibm.storage_protect.dp_db2_postcheck`**:
   - Performs postchecks to validate the configuration and ensure the setup is complete.

---

## Hosts
The playbook operates on two types of hosts:
1. **`storage_protect_client`**:
   - The DB2 client where IBM Storage Protect for DP for DB2 will be installed and configured.
   - Variables for this host will be defined in `client_vars.yml`.

2. **`storage_protect_server`**:
   - The IBM Storage Protect server where the client node will be registered.
   - Variables for this host will be defined in `server_vars.yml`.

---

## Variables
### **Client Variables (`client_vars.yml`)**
### **Server Variables (`server_vars.yml`)**
---

## How the Playbook Works
### **Play 1: Precheck and Installation on the Client**
1. **Prechecks**:
   - Runs the `dp_db2_precheck` role to ensure the environment is ready.
   - Checks for DB2 processes, binaries, and other prerequisites.

2. **BA Client Installation**:
   - Queries the installed version of `TIVsm-API64`.
   - Installs the SP Client packages if it is not already installed.

3. **DSM Configuration**:
   - Configures the `dsm.opt` file with the required parameters.
   - Creates the `dsm.sys` file with the server name and TCP server address.

### **Play 2: Node Registration on the Server**
1. **Node Registration**:
   - Runs the `nodes` role to register the client node with the IBM Storage Protect server.
   - Uses the `node_name`, `policy_domain`, and `node_password` variables.

### **Play 3: Postchecks on the Client**
1. **Postchecks**:
   - Runs the `dp_db2_postcheck` role to validate the configuration.
   - Ensures that the setup is complete and ready for use.

---

## Example Inventory File
```ini
[storage_protect_client]
db2_client ansible_host=192.168.1.10

[storage_protect_server]
storage_server ansible_host=192.168.1.20
```

---

## Example `client_vars.yml`
```yaml
db2_instance_owner: "db2inst1"
storage_protect_server_name: "SP_SERVER"
storage_protect_server_ip: "192.168.1.20"
```

---

## Example `server_vars.yml`
```yaml
node_name: "db2_client_node"
policy_domain: "DB2_POLICY"
node_password: "secure_password"
```

---

## How to Run the Playbook
1. Ensure all required roles are installed and accessible.
2. Define the inventory file (`inventory.yml`) with the `storage_protect_client` and `storage_protect_server` groups.
3. Define the variables in `client_vars.yml` and `server_vars.yml`.
4. Run the playbook using the following command:
   ```bash
   ansible-playbook dp_db2_install.yml -i inventory.yml
   ```

---

## Notes
- Ensure that the `db2_instance_owner` user has the necessary permissions to run DB2 commands and access configuration files.
- Use Ansible Vault to securely store sensitive variables like `node_password`.

### Example:
Encrypt sensitive variables:
```bash
ansible-vault encrypt server_vars.yml
```

Run the playbook with the vault password:
```bash
ansible-playbook dp_db2_install.yml -i inventory.yml --ask-vault-pass
```

---

## Troubleshooting
1. **Task Fails**:
   - Check the `failed_when` conditions in the playbook to identify the failure point.
   - Review the logs for detailed error messages.

2. **Debugging**:
   - Use the `-vvv` flag with the `ansible-playbook` command to enable verbose output:
     ```bash
     ansible-playbook dp_db2_install.yml -i inventory.yml -vvv
     ```

3. **Role-Specific Issues**:
   - Refer to the `README.md` files in each role for detailed information about their variables and usage.

---

Let me know if you need further clarification or adjustments!
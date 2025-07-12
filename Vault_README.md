# Ansible Vault Integration for IBM Storage Protect

This repository uses **Ansible** to automate the deployment and management of the IBM Spectrum Protect BA Client. It leverages **Ansible Vault** to securely store sensitive data such as credentials and file paths.

---

## Prerequisites

* Ansible >= 2.10
* Python >= 3.8
* GitHub self-hosted runner (or GitHub-hosted if using secrets)
* Ansible Collections:

  ```bash
  ansible-galaxy collection install ibm.storage_protect
  ansible-galaxy collection install ansible.posix
  ```

---

## Setup Instructions

### 1. Install Required Tools

```bash
sudo apt install python3-pip
pip install ansible
```

### 2. Clone Repository

```bash
git clone <repo-url>
cd <repo-directory>
```

### 3. Add Encrypted Vault File

Create secrets and encrypt them:

```bash
ansible-vault create vars/vault.yml
```

Add variables like:

Sample vault.yml (before encryption)

```yaml
storage_protect_username: root
storage_protect_password: adminPass
CLIENT_NAME: tsmcbuildlnx24.storage.tucson.ibm.com
CLIENT_PASSWORD: torug
CLIENT_POLICY_DOMAIN: MY_DOMAIN
CLIENT_HOST: 9.11.61.55
STORAGE_PROTECT_REQUEST_TIMEOUT: 10
ba_client_version: "8.1.27.0"
BA_CLIENT_TAR_REPO_PATH: "/home/githubrunner/tars"
```

Encrypt the file:

```bash
ansible-vault encrypt vars/vault.yml
```
Sample Encrypted vault.yml

```
$ANSIBLE_VAULT;1.1;AES256\36673963393338653533616635343438386437303032626335386538373831323630633665653832
3362646238356233303763373064333336613839356331640a3537343233343831373063623531656433613761313663383065613763
```

### View/Edit/Decrypt

```
ansible-vault view vars/vault.yml
ansible-vault edit vars/vault.yml
ansible-vault decrypt vars/vault.yml
```
### 4. Create `vault_pass.txt` File

This file holds the vault password and is used in automation (DO NOT COMMIT):

```bash
echo "your-vault-password" > vault_pass.txt
```

## Using Vault in Playbooks

### Sample Playbook

```yaml
- name: Install BA Client
  hosts: all
  become: true
  vars_files:
    - ../vars/vault.yml
  roles:
    - role: ibm.storage_protect.ba_client_install
      vars:
        ba_client_start_daemon: true
        ba_client_state: "present"
        ba_client_version: "{{ ba_client_version }}"
        ba_client_tar_repo: "{{ BA_CLIENT_TAR_REPO_PATH }}"

- name: Uninstall BA Client
  hosts: all
  become: true
  vars_files:
    - ../vars/vault.yml
  roles:
    - role: ibm.storage_protect.ba_client_install
      vars:
        ba_client_state: "absent"
```

Run the playbook:

```bash
ansible-playbook -i inventory.yml playbooks/playbook.yml --vault-password-file vault_pass.txt
```

---

## GitHub Actions Integration

### Storing Vault Password Securely

1. In GitHub Secrets

Create a GitHub secret called VAULT_PASSWORD. Then in your GitHub Actions:
```
- name: Write vault password
  run: echo "$VAULT_PASSWORD" > vault_pass.txt
  env:
    VAULT_PASSWORD: ${{ secrets.VAULT_PASSWORD }}
```

2.  Using Environment Variable (optional for local run)

```
export ANSIBLE_VAULT_PASSWORD_FILE=~/vault_pass.txt
```



### Sample Workflow

`.github/workflows/ansible.yml`

```yaml
name: Run Ansible Playbook to Register Client

on:
  push:
    branches: [main]

jobs:
  run_ansible:
    runs-on: self-hosted

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python and Ansible
        run: |
          python3 -m venv venv
          source venv/bin/activate
          pip install --upgrade pip
          pip install ansible

      - name: Install Ansible Collections
        run: |
          ansible-galaxy collection install ibm.storage_protect ansible.posix

      - name: Run Playbook
        run: |
          ansible-playbook -i inventory.yml playbooks/playbook.yml \
            --vault-password-file vault_pass.txt
```

---

## Best Practices

* **Do not commit `vault_pass.txt`** to the repository.
* Store vault passwords securely using GitHub Secrets or a secrets manager.
* Use separate vault files per environment (e.g., `dev/vault.yml`, `prod/vault.yml`).
* Rotate vault passwords regularly.
* Validate playbook with dry runs before production deployments.

---

## How to Use This Repository

* Clone the repo
* Create your vault.yml with sensitive vars
* Encrypt it using ansible-vault encrypt vars/vault.yml
* Set vault password in GitHub secrets or use environment variable
* Trigger GitHub Action via git push
---

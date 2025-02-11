# ibm.storage_protect.dsm_opt

This Ansible role generates a `dsm.opt` configuration file for IBM Storage Protect clients.

## Features
- Dynamically generates the `dsm.opt` file
- Handles `present` and `absent` states for file creation and deletion.
- Automatic Value Mapping**: Reads an existing `dsm.opt` file and automatically maps the existing values.

## Variables

| Variable              | Default Value   | Required | Description                                                                                                                                                                                                                                     |
|-----------------------|-----------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `dsm_opt_servername`          | `""`           | No       | Server name defined in dsm.sys                                                                                                                                                                                                                  |
| `dsm_opt_nodename`            | `""`           | No       | Node name of the client                                                                                                                                                                                                                         |
| `dsm_opt_password`            | `""`           | No       | Specifies the password you use to log on to the IBM Storage Protect server.                                                                                                                                                                     |
| `dsm_opt_domain`              | `""`             | No       | Directories or file systems to back up                                                                                                                                                                                                          |
| `dsm_opt_optfile_path`        | `"/opt/tivoli/tsm/client/ba/bin/dsm.opt"` | No       | Path for the dsm.opt file                                                                                                                                                                                                                       |
| `dsm_opt_state`               | `"present"`    | No       | Ensure file is present or absent                                                                                                                                                                                                                |


## Usage

### Example Playbooks
- The example playbooks are available in the playbooks directory of this collection.
- To configure a dsm_opt file, execute the 'dsm_opt' playbook from the playbooks directory and define variables mentioned above in your inventory or pass them as extra vars.
```bash
 ansible-playbook -i inventory.ini playbooks/dsm_opt/dsm_opt.yml --extra-vars 'target_hosts=group1 dsm_opt_parameters={"dsm_opt_servername": "NewServer", "dsm_opt_nodename": "NewClient"}' 
```
- If the number of variables is large, create a separate vars file and pass the vars file as --extra-vars to the command.
```bash
# vars.yml
target_hosts: group1
dsm_opt_parameters:
  dsm_opt_servername: "NewServer"
  dsm_opt_nodename: "NewClient"
  dsm_opt_domain: "C: D: E:\\UserData"
  dsm_opt_password: "mypassword"
 
```
```bash
ansible-playbook -i inventory.ini playbooks/dsm_opt/dsm_opt.yml --extra-vars "@vars.yml"
```
- To remove a existing opt file execute playbook using the below command.

```bash
 ansible-playbook -i inventory.ini playbooks/dsm_opt/dsm_opt.yml --extra-vars 'target_hosts=group1 dsm_opt_state=absent' 
```

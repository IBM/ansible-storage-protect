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
- Example playbooks are available under the playbooks directory of [IBM/ansible-storage-protect](https://github.com/IBM/ansible-storage-protect/tree/main/playbooks/) github repo.
- The `target_hosts` variable allows you to dynamically specify the target hosts or host group at runtime.
- If `target_hosts` is not provided, the playbook defaults to using "all" hosts from your inventory.
Make sure the specified target_hosts exist in your inventory file (INI, YAML, or dynamic inventory).
- To configure a dsm.opt file, execute the 'dsm_opt_playbook' included with the collection and define variables mentioned above.
- Create a seperate vars file in working directory and execute the below command.
```bash
 ansible-playbook -i inventory.ini ibm.storage_protect.dsm_opt_playbook.yml -e @your_vars_file.yml
```
- Example vars file
```bash
# vars.yml
dsm_opt_parameters:
  dsm_opt_servername: "NewServer"
  dsm_opt_nodename: "NewClient"
  dsm_opt_domain: "C: D: E:\\UserData"
  dsm_opt_password: "mypassword"
 
```
- To remove a existing opt file execute playbook using the below command.

```bash
 ansible-playbook -i inventory.ini ibm.storage_protect.dsm_opt_playbook.yml --extra-vars 'dsm_opt_state=absent' 
```

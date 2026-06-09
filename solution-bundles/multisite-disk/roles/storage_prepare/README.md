# ibm.storage_protect.storage_prepare

## Overview
This Ansible role automates the **storage preparation and cleanup** tasks for IBM Storage Protect (SP) Server on Linux systems. It performs:
- Dynamic disk discovery and allocation based on instance size.
- Creates the required directories for server configuration.
- Directories for db,storage pools,db backup,actlog and archlog are created.
- Full cleanup of volumes and mount points for rollback or re-deployment.
---

## Role Variables
The following variables can be configured in the `defaults/main.yml` file:

| Variable               | Default Value                                    | Description                                                                 |
|------------------------|--------------------------------------------------|-----------------------------------------------------------------------------|
| `clean_up`             | `false`                                          | Set to `true` to perform cleanup. Set to `false` to prepare storage.       |
| `instance_dir`         | `/tsminst1`                                      | Root directory where mount points and data folders will be created.        |
| `storage_prepare_size` | `xsmall`                                         | Size category (`xsmall`, `small`, `medium`, `large`) for disk allocation.  |
| `dsk_size`             | See `dsk_size` values specified in next section. | Dictionary of disk allocation size ranges (in GB) for each TSM group.      |
| `actlog.vg`            | `vg_actlog`                                      | Volume Group name for active log.                                           |
| `actlog.lv`            | `lv_actlog`                                      | Logical Volume name for active log.                                         |
| `actlog.mount_point`   | `TSMalog`                                        | Mount point directory for active log.                                       |
| `archlog.vg`           | `vg_archlog`                                     | Volume Group name for archive log.                                          |
| `archlog.lv`           | `lv_archlog`                                     | Logical Volume name for archive log.                                        |
| `archlog.mount_point`  | `TSMarchlog`                                     | Mount point directory for archive log.                                      |

---

### `dsk_size` Values

```yaml
dsk_size:
  xsmall:
    TSMdbspace: [200, 250]
    TSMalog: [30, 80]
    TSMarchlog: [251, 300]
    TSMfile: [10000, 10050]
    TSMbkup: [1000, 1050]
  small:
    TSMdbspace: [1000, 1050]
    TSMalog: [140, 190]
    TSMarchlog: [1000, 1005]
    TSMfile: [38000, 38050]
    TSMbkup: [3000, 3050]
  medium:
    TSMdbspace: [2000, 2005]
    TSMalog: [140, 190]
    TSMarchlog: [2000, 2005]
    TSMfile: [180000, 180050]
    TSMbkup: [10000, 10050]
  large:
    TSMdbspace: [4000, 4050]
    TSMalog: [550, 600]
    TSMarchlog: [4000, 4050]
    TSMfile: [500000, 500050]
    TSMbkup: [16000, 16050]
  ```
## Role Workflow

### When `clean_up` is `false`:
1. Validates the `size` input.
2. Parses available block devices using `lsblk`.
3. Filters free disks based on `dsk_size` thresholds.
4. For example if disk size=120GB and size specified=xsmall, this disk will be allocated to TSMdbspace group. Since 100<=120>=150.
5. If multiple disks are allocated to a group, multiple directories are created, formatted using `xfs` and are mount to those disks. 
6. Multiple directories are created for TSMdbspace,TSMfile,TSMbkup groups. Names of directories are in the following format. `TSMdbspace01`,`TSMdbspace02`,etc.
7. If multiple disks are allocated to actlog and archlog, volume group is created for this groups and a single logical volume is mount to corresponding directory. Hence only one directory for actlog and archlog is created with namespace as `TSMalog` and `TSMarchlog`.
8. Adds entries in `etc/fstab`.
9. Sets the fact in following variables ( required in `sp_server_install` role:
   - `tsmstgpaths`: 
     - type: `string`
     - Contains the name of directories created for storage pools. [eg: /tsminst1/TSMfile01]
   - `tsmbkpaths`: 
     - type: `string`
     - Contains the name of directories created for db abckup. [eg: /tsminst1/TSMbkup01,/tsminst1/TSMbkup02"]
   - `tsmdbpaths`: 
     - type: `string`
     - Contains the name of directories created for db. [eg: /tsminst1/TSMdbspace01,/tsminst1/TSMdbspace02]


### When `clean_up` is `true`:
1. Gathers all mount points under `instance_dir`.
2. Unmounts all the directories.
3. Removes:
   - Logical volumes for active and archive logs.
   - Volume groups for active and archive logs.

## Note
1. The `dsk_size` variable contains the values in `GB` and are set as mentioned in the server blueprint document.
2. If you are planning to modify the blueprint, override the variable in playbook and specify the values in `GB` accordingly.
3. Make sure you handle the lower and upper-bound, since based on the same, disks will be allocated.
---

## Example Playbooks
- Example playbooks are available under the playbooks directory of [IBM/ansible-storage-protect](https://github.com/IBM/ansible-storage-protect/tree/main/playbooks/) github repo.
- The `target_hosts` variable allows you to dynamically specify the target hosts or host group at runtime.
- If `target_hosts` is not provided, the playbook defaults to using "all" hosts from your inventory.
Make sure the specified target_hosts exist in your inventory file (INI, YAML, or dynamic inventory).
- To prepare the storage according to the blueprint, execute the below command.
```bash
ansible-playbook -i inventory.ini ibm.storage_protect.storage_prepare_playbook.yml -e 'storage_prepare_size=xsmall' 
```
- To cleanup the storage, execute the below command.
```bash
ansible-playbook -i inventory.ini ibm.storage_protect.storage_cleanup_playbook.yml -e 'clean_up=true' 
```
- For custom storage preparation:-
  - Create a vars file in working directory.
  - Include all the vars as mentioned in `role_varibles` above.
  - Modify the dsk_size variable accordingly.
  - Execute the playbook provided by collection using below command.
```bash
ansible-playbook -i inventory.ini ibm.storage_protect.storage_prepare_playbook.yml -e @your_vars_file.yml 
  ```

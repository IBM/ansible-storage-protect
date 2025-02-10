# ibm.storage_protect.backup

## Description
An ansible role to take on demand backup on Storage protect client.

## Requirements 
- Ansible 2.9+ 
- IBM Storage Protect server configured and accessible  and atleast one BA client node registered with server.

## Environment Variables

Before running the playbook, set the following environment variables in your terminal:

```bash
export STORAGE_PROTECT_SERVERNAME="<Storage protect server name that client is registered with>"
export STORAGE_PROTECT_NODENAME="<Node name registered with storage protect server>"
export STORAGE_PROTECT_NODE_PASSWORD="<Node password of the node that is registered with storage protect server"
```

## Variables
The following role variables are child of storage_protect_node_file_backup.

|Variable Name|Default Value|Required|Description|
|:---|:---:|:---:|:---|
|`backup_action`||yes|Backup type (selective/incremental)|
|`filespec`||yes|The paths of the files or directories to backup.Supports list of multiple files and directories, separated by a space character;in addition,use wildcard characters to include a group of files or to include all files in a directory.| 
|`absolute`||no|Use the absolute variable with the incremental command to force a backup of all files and directories that match the file specification or domain,even if the objects were not changed since the last incremental backup.Setting to a value of "Yes" will enable the mentioned functionality.|
|`compression`||no|The compression variable compresses files before you send them to the server.Use with the incremental,and selective commands.Setting to a value of "Yes" will enable the compression. A value of "No" will ensure files are not compressed. |
|`is_compress_always`||no|Use this variable together with is_compression_enabled. When is_compression_enabled is set to "Yes", the is_compress_always variable specifies whether to continue compressing an object if it grows during compression.Setting to a velue of "Yes" will continue to compress an object even if size of object grows after compression. Setting to a value of "No" will send the file uncompressed if the file size increases.Use with the incremental, and selective commands.|
|`diff_snapshot`||no|The diff_snapshot variable controls whether the backup-archive client creates the differential snapshot when it runs a snapshot difference incremental backup. Use with incremental command.If value is set to "create"  backup-archive client will create the snapshot during incremental backup. If the value it set to "latest" client will use the latest snapshot that is found on the file server as source snapshot.|
|`dirs_only`||no|The dirs_only variable when set to "Yes" processes directories only during backup. The client does not process files. Use with incremental and selective command.|
|`file_list`||no|Use the file_list variable to process a list of files. The backup-archive client opens the file you specify with this variable and processes the list of files within according to the specific command.Use with incremental and selective command.|
|`files_only`||no|The files_only variable when set to "Yes" restricts backup processing to files only. Use with incremental and selective comand.|
|`remove_operand_limit`||no|The remove_operand_limit variable specifies that the client removes the 20-operand limit as this limits the number of files and directories that can be specified with command.Use with incremental and selective commands.Setting the value to "Yes" will remove the limit.|
|`snapshot_root`||no|Use the snapshot_root variable with the incremental, selective, commands to specify the root directory of snapshot that should be used for backup.This option is used in snapshot-supported environments. With this mechanism backup only processes snapshot data and not live filesystem. For ex : dsmc incremental /mnt/snapshot1/data -snapshotroot=/mnt/snapshot1|
|`is_subdir`||no|The subdir variable specifies whether you want to include subdirectories of named directories for processing.If set to "Yes" subdirectories are processed otherwise not.Use with incremental and selective commands.|


## Example Playbooks
```yaml
- name: Take on demand backup in IBM Storage Protect
  hosts: storage_protect_client 
  roles:
    - role: ibm.storage_protect.node_file_backup 
      vars:
        backup_action: "selective" 
        filespec: "/root/ODB" 
        is_subdir: "yes"
```


## License Information
Apache License, Version 2.0

See [LICENSE](LICENSE) for the full license text.

## Author
[Amol kumar](https://github.com/amol-kumar1) 

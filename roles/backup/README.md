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
## Variables

|Variable Name|Default Value|Required|Description|
|:---:|:---:|:---:|:---:|
|`backup_action`|``|yes|Backup type (selective/incremental)|
|`filespec`|``|yes|File/Directory path to be backed up.|
|`absolute`|``|no|Use the absolute option with the incremental command to force a backup of all files and directories that match the file specification or domain,even if the objects were not changed since the last incremental backup.|
|`autofsrename`|``|no|The autofsrename option is used with incremental command to rename an existing file space that is not Unicode-enabled on the IBM Storage Protectserver so that a Unicode-enabled file space with the original name can be created for the current operation.|
|`changingretries`|``|no|The changingretries option specifies how many additional times you want the client to attempt to back up or archive a file that is in use.Use this option with the incremental, and selective commands.|
|`compressalways`|``|no|The compressalways option specifies whether to continue compressing an object if it grows during compression.Use this option with the incremental,and selective commands.|
|`compression`|``|no|The compression option compresses files before you send them to the server.Use this option with the incremental,and selective commands.|
|`detail`|``|no|Use the detail option to display detailed infomration about backup operation. Use with incremental command.|
|`diffsnapshot`|``|no|The diffsnapshot option controls whether the backup-archive client creates the differential snapshot when it runs a snapshot difference incremental backup. Use with incremental command.|
|`dirsonly`|``|no|The dirsonly option processes directories only. The client does not process files. Use with incremental and selective command.|
|`domain`|``|no|The domain option specifies what you want to include for incremental backup. Use with incremental command.|
|`encryptiontype`|``|no|Use the encryptiontype option to specify the algorithm for data encryption.Use with incremental command.|
|`encryptkey`|``|no|The backup-archive client supports the option to encrypt files that are being backed up or archived to the IBM Storage Protect server.Use with incremental command.|
|`filelist`|``|no|Use the filelist option to process a list of files. Use with incremental and selective command..|
|`filesonly`|``|no|The filesonly option restricts backup processing to files only. Use with incremental and selective comand.|
|`incrbydate`|``|no|Use the incrbydate option with the incremental command to back up new and changed files with a modification date later than the last incremental backup stored at the server, unless you exclude the file from backup.|
|`memoryefficientbackup`|``|no|The memoryefficientbackup option specifies the memory-conserving algorithm to use for processing full file space backups.Use with incremental command.|
|`nojournal`|``|no|Use the nojournal option with the incremental command to specify that you want to perform a traditional full incremental backup,instead of the default journal-based backup.Use with incremental commands.|
|`postsnapshotcmd`|``|no|The postsnapshotcmd option allows you to run operating system shell commands or scripts after the backup-archive client starts a snapshot during a snapshot-based backup operation.Use with incremental and selective command.|
|`preservelastaccessdate`|``|no|Use the preservelastaccessdate option to specify whether a backup or archive operation changes the last access time.Use with incremental and selective commands.|
|`presnapshotcmd`|``|no|The presnapshotcmd option allows you to run operating system commands before the backup-archive client starts a snapshot.Use with incremental and selective commands.|
|`removeoperandlimit`|``|no|The removeoperandlimit option specifies that the client removes the 20-operand limit.Use with incremental and selective commands..|
|`resetarchiveattribute`|``|no|Use the resetarchiveattribute option to specify whether the backup-archive client resets the Windows archive attribute on files that are successfully backed up to the IBM Storage Protect server.Use with incremental and selective commands.|
|`skipntpermissions`|``|no|The skipntpermissions option bypasses processing of Windows file system security information.Use with incremental and selective commands.|
|`skipntsecuritycrc`|``|no|The skipntsecuritycrc option controls the computation of the security cyclic redundancy check (CRC) for a comparison of Windows NTFS or ReFS security information during an incremental or selective backup operation.Use with incremental and selective commands. |
|`snapdiff`|``|no|Using the snapdiff (snapshot difference) option with the incremental command streamlines the incremental backup process. The command runs an incremental backup of the files that were reported as changed by NetApp instead of scanning all of the volume for changed files.|
|`snapshotcachesize`|``|no|Use the snapshotcachesize option to specify an appropriate size to create the snapshot.Use with incremental and selective commands.|
|`snapshotproviderfs`|``|no|Use the snapshotproviderfs option to enable snapshot-based file backup operations, and to specify a snapshot provider. Use with incremental and selective commands.|
|`snapshotproviderimage`|``|no|Use the snapshotproviderimage option to enable snapshot-based image backup, and to specify a snapshot provider. Use with incremental and selective commands.|
|`snapshotroot`|``|no|Use the snapshotroot option with the incremental, selective, or archive commands with an independent software vendor application that provides a snapshot of a logical volume, to associate the data on the local snapshot with the real file space data that is stored on the IBM Storage Protect server.Use with incremental and selective commands.|
|`subdir`|``|no|The subdir option specifies whether you want to include subdirectories of named directories for processing.Use with incremental and selective commands.|
|`tapeprompt`|``|no|The tapeprompt option specifies whether you want the backup-archive client to wait for a tape mount if it is required for a backup.|


## Example Playbooks
```yaml
- name: Take on demand backup in IBM Storage Protect
  hosts: storage_protect_client 
  roles:
    - role: bm.storage_protect.backup 
      vars:
        backup_action: "selective" 
        filespec: "/root/ODB" 
        subdir: "yes"
```


## License Information
Apache License, Version 2.0

See [LICENSE](LICENSE) for the full license text.

## Author
[Amol kumar](https://github.com/amol-kumar1) 

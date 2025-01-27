#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2025,Amol kumar <amol.kumar2@ibm.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: backup
author: Amol kumar
short_description: Manage IBM Storage Protect Schedules
description:
    - This module takes selective/incremental backup in IBM Storage Protect.
    - It uses the dsmc CLI for backend operations.
options:
    backup_action:
        description: Type of backup to perform (selective or incremental).
        required: true
        type: str
    filespec:
        description: The path of the file or directory to backup.
        required: true
        type: str
    absolute:
        description: Use the absolute option with the incremental command to force a backup of all files and directories that match the file specification or domain,
                     even if the objects were not changed since the last incremental backup.
        required: false
        type: No Value
    autofsrename:
        description: The autofsrename option is used with incremental command to rename an existing file space that is not Unicode-enabled on the IBM Storage Protect 
                     server so that a Unicode-enabled file space with the original name can be created for the current operation.
        required: false
        type: No value
    changingretries:
        description: The changingretries option specifies how many additional times you want the client to attempt to back up or archive a file that is in use. 
                    Use this option with the incremental, and selective commands.
        required: false
        type: int
    compressalways: 
        description: The compressalways option specifies whether to continue compressing an object if it grows during compression.Use this option with the incremental, 
                    and selective commands.
        required: false
        type: yes/no
    compression:
        description: The compression option compresses files before you send them to the server.Use this option with the incremental,and selective commands.
        required: false
        type: yes/no
    detail:
        description: Use the detail option to display detailed infomration about backup operation. Use with incremental command.
        required: false
        type: No value
    diffsnapshot:
        description: The diffsnapshot option controls whether the backup-archive client creates the differential snapshot when it runs a snapshot difference
                     incremental backup. Use with incremental command.
        required: false
        type: No value
    dirsonly:
        description: The dirsonly option processes directories only. The client does not process files. Use with incremental and selective command.
        required: false
        type: No value
    domain:
        description: The domain option specifies what you want to include for incremental backup. Use with incremental command.
        required: false
        type: str
    encryptiontype:
        description: Use the encryptiontype option to specify the algorithm for data encryption.Use with incremental command.
        required: false
        type: str
    encryptkey:
        description: The backup-archive client supports the option to encrypt files that are being backed up or archived to the IBM Storage Protect server.
                     Use with incremental command.
        required: false
        type: str
    filelist:
        description: Use the filelist option to process a list of files. Use with incremental and selective command.
        required: false
        type: str
    filesonly:
        description: The filesonly option restricts backup processing to files only. Use with incremental and selective comand.
        required: false
        type: str
    incrbydate:
        description: Use the incrbydate option with the incremental command to back up new and changed files with a modification date later than the last 
                     incremental backup stored at the server, unless you exclude the file from backup.
        required: false
        type: No value
    memoryefficientbackup:
        description: The memoryefficientbackup option specifies the memory-conserving algorithm to use for processing full file space backups.
                     Use with incremental command.
        required: false
        type: yes/no
    nojournal:
        description: Use the nojournal option with the incremental command to specify that you want to perform a traditional full incremental backup, 
                     instead of the default journal-based backup.Use with incremental commands.
        required: false
        type: No value
    postsnapshotcmd:
        description: The postsnapshotcmd option allows you to run operating system shell commands or scripts after the backup-archive client starts a 
                     snapshot during a snapshot-based backup operation.Use with incremental and selective command.
        required: false
        type: str
    preservelastaccessdate:
        description: Use the preservelastaccessdate option to specify whether a backup or archive operation changes the last access time.
                     Use with incremental and selective commands.
        required: false
        type: No value
    presnapshotcmd:
        description: The presnapshotcmd option allows you to run operating system commands before the backup-archive client starts a snapshot.
                     Use with incremental and selective commands.
        required: false
        type: str
    removeoperandlimit:
        description: The removeoperandlimit option specifies that the client removes the 20-operand limit.Use with incremental and selective commands.
        required: false
        type: No value
    resetarchiveattribute:
        description: Use the resetarchiveattribute option to specify whether the backup-archive client resets the Windows archive attribute on files that are 
                     successfully backed up to the IBM Storage Protect server.Use with incremental and selective commands.
        required: false
        type: yes/no
    skipntpermissions:
        description: The skipntpermissions option bypasses processing of Windows file system security information.Use with incremental and selective commands.
        required: false
        type: No value
    skipntsecuritycrc:
        description: The skipntsecuritycrc option controls the computation of the security cyclic redundancy check (CRC) for a comparison of Windows NTFS or
                     ReFS security information during an incremental or selective backup operation.Use with incremental and selective commands.
        required: false
        type: No value
    snapdiff:
        description: Using the snapdiff (snapshot difference) option with the incremental command streamlines the incremental backup process. The command 
                     runs an incremental backup of the files that were reported as changed by NetApp instead of scanning all of the volume for changed files.
        required: false
        type: No value
    snapshotcachesize:
        description: Use the snapshotcachesize option to specify an appropriate size to create the snapshot.Use with incremental and selective commands.
        required: false
        type: int
    snapshotproviderfs:
        description: Use the snapshotproviderfs option to enable snapshot-based file backup operations, and to specify a snapshot provider.
                     Use with incremental and selective commands.
        required: false
        type: str
    snapshotproviderimage:
        description: Use the snapshotproviderimage option to enable snapshot-based image backup, and to specify a snapshot provider.
                     Use with incremental and selective commands.
        required: false
        type: str
    snapshotroot:
        description: Use the snapshotroot option with the incremental, selective, or archive commands with an independent software vendor application that 
                     provides a snapshot of a logical volume, to associate the data on the local snapshot with the real file space data that is stored on the IBM Storage
                     Protect server.Use with incremental and selective commands.
        required: false
        type: str
    subdir:
        description: The subdir option specifies whether you want to include subdirectories of named directories for processing.
                     Use with incremental and selective commands.
        required: false
        type: yes/no
    tapeprompt:
        description: The tapeprompt option specifies whether you want the backup-archive client to wait for a tape mount if it is required for a backup
                     or retrieve process, or to be prompted for a choice.Use with incremental and selective commands.
        required: false
        type: yes/no
extends_documentation_fragment: ibm.storage_protect.auth
...
'''

EXAMPLES = '''
- name: Test On Demand backup in IBM Storage Protect
  hosts: storage_protect_client
  vars:
    storage_protect_server_name: cabin4
    storage_protect_node_name: fenrir98
    storage_protect_node_password: fenrir98
    backup_action: "selective"
    filespec: "/root/backup_test/"
    filesonly: "yes"
    subdir: "yes"

  roles:
    - ibm.storage_protect.backup

  tasks:
    - name: "Verify the Result of the backup Taken"
      ansible.builtin.debug:
        msg: "Backup test completed successfully."
...
'''

from ..module_utils.dsmc_adapter import DsmcAdapter

def main():
    argument_spec = dict(
        backup_action=dict(required=True, choices=['selective', 'incremental']),
        filespec=dict(required=True),
        absolute=dict(),
        autofsrename=dict(),
        changingretries=dict(),
        compressalways=dict(),
        compression=dict(),
        detail=dict(),
        diffsnapshot=dict(),
        dirsonly=dict(),
        domain=dict(),
        encryptiontype=dict(),
        encryptkey=dict(),
        filelist=dict(),
        filesonly=dict(),
        incrbydate=dict(),
        memoryefficientbackup=dict(),
        nojournal=dict(),
        postsnapshotcmd=dict(),
        preservelastaccessdate=dict(),
        presnapshotcmd=dict(),
        removeoperandlimit=dict(),
        resetarchiveattribute=dict(),
        skipntpermissions=dict(),
        skipntsecuritycrc=dict(),
        snapdiff=dict(),
        snapshotcachesize=dict(),
        snapshotproviderfs=dict(),
        snapshotproviderimage=dict(),
        snapshotroot=dict(),
        subdir=dict(),
        tapeprompt=dict(),
        server_name=dict(),
        node_name=dict(),
        password=dict(),
        request_timeout=dict(),

    )
    module = DsmcAdapter(argument_spec=argument_spec, supports_check_mode=True)
    backup_action = module.params.get('backup_action')
    filespec = module.params.get('filespec')
    option_params = [
        "absolute",
        "autofsrename",
        "changingretries",
        "compressalways",
        "compression",
        "detail",
        "diffsnapshot",
        "dirsonly",
        "domain",
        "encryptiontype",
        "encryptkey",
        "filelist",
        "filesonly",
        "incrbydate",
        "memoryefficientbackup",
        "nojournal",
        "postsnapshotcmd",
        "preservelastaccessdate",
        "presnapshotcmd",
        "removeoperandlimit",
        "resetarchiveattribute",
        "skipntpermissions",
        "skipntsecuritycrc",
        "snapdiff",
        "snapshotcachesize",
        "snapshotproviderfs",
        "snapshotproviderimage",
        "snapshotroot",
        "subdir",
        "tapeprompt",
    ]
    option_params_no_value = [
        "absolute",
        "autofsrename",
        "detail",
        "diffsnapshot",
        "filesonly",
        "dirsonly",
        "incrbydate",
        "nojournal",
        "preservelastaccessdate",
        "removeoperandlimit",
        "skipntpermissions",
        "skipntsecuritycrc",
        "snapdiff",
    ]
    options = ''
    for opt in option_params:
        value = module.params.get(opt)
        if value is not None:
            value = str(value)
            if opt in option_params_no_value:
                options += f" -{opt}"
            else:
                options += f" -{opt}={value}"

    rc, output, error = module.perform_action(backup_action, filespec, options)

if __name__ == "__main__":
    main()

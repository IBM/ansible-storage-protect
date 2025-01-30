#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2025,Amol kumar <amol.kumar2@ibm.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: node_file_backup 
author: Amol kumar
short_description: Take an on-demand file back-up on IBM Storage protect. 
description:
    - Use this module
	(i) to perform selective backup of files or directories(with support for wildcard) characters in the specified location OR
	(ii) to perform incremental backup of all new or changed files or directories in the specified locations.
    - It uses the "dsmc selective" and "dsmc incremental"  CLI's for respective operations.
options:
    backup_action:
        description: Type of backup to perform (selective or incremental).
        required: true
        type: str
    filespec:
        description: The paths of the files or directories to backup.Supports list of multiple files and directories, separated by a space character;in addition, 
		     use wildcard characters to include a group of files or to include all files in a directory.
        required: true
        type: str
    absolute:
        description: Use the absolute variable with the incremental command to force a backup of all files and directories that match the file specification or domain,
                     even if the objects were not changed since the last incremental backup.Setting to a value of "Yes" will enable the mentioned functionality. 
        required: false
        type: Boolean.
    is_compression_enabled:
        description: The compression variable compresses files before you send them to the server.Use with the incremental,and selective commands.Setting to a value
                     of "Yes" will enable the compression. A value of "No" will ensure files are not compressed.  
        required: false
        type: boolean
    is_compress_always: 
        description: Use this variable together with is_compression_enabled. When is_compression_enabled is set to " Yes", the is_compress_always variable specifies
                     whether to continue compressing an object if it grows during compression.Setting to a velue of "Yes" will continue to compress an object even if
                     size of object grows after compression. Setting to a value of "No" will send the file uncompressed if the file size increases.Use with the incremental
                     , and selective commands
        required: false
        type: boolean
    diff_snapshot:
        description: The diff_snapshot variable controls whether the backup-archive client creates the differential snapshot when it runs a snapshot difference
                     incremental backup. Use with incremental command.If value is set to "create"  backup-archive client will create the snapshot
                     during incremental backup. If the value it set to "latest" client will use the latest snapshot that is found on the file server as source
                     snapshot.
        required: false
        type: str
    dirs_only:
        description: The dirs_only variable when set to "Yes" processes directories only during backup. The client does not process files. Use with incremental and
                     selective command.
        required: false
        type: boolean
    file_list:
        description: Use the file_list variable to process a list of files. The backup-archive client opens the file you specify with this variable and processes the 
                     list of files within according to the specific command.Use with incremental and selective command.
        required: false
        type: str
    files_only:
        description: The files_only variable when set to "Yes" restricts backup processing to files only. Use with incremental and selective comand.
        required: false
        type: boolean
    remove_operand_limit:
        description: The remove_operand_limit variable  specifies that the client removes the 20-operand limit as this limits the number of files and directories
                     that can be specified with command.Use with incremental and selective commands.Setting the value to "Yes" will remove the limit.
        required: false
        type: boolean
    snapshot_root:
        description: Use the snapshot_root variable with the incremental, selective, commands to specify the root directory of snapshot that should be used for
                     backup.This option is used in snapshot-supported environments. With this mechanism backup only processes snapshot data
                     and not live filesystem.
                     For ex : dsmc incremental /mnt/snapshot1/data -snapshotroot=/mnt/snapshot1
        required: false
        type: str
    is_subdir:
        description: The subdir variable specifies whether you want to include subdirectories of named directories for processing.If set to Yes subdirectories are processed
		     otherwise no.Use with incremental and selective commands.
        required: false
        type: boolean 
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
    files_only: "yes"
    is_subdir: "yes"

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
        is_compression_enabled=dict(),
        is_compress_always=dict(),
        diff_snapshot=dict(),
        dirs_only=dict(),
        file_list=dict(),
        files_only=dict(),
        remove_operand_limit=dict(),
        snapshot_root=dict(),
        is_subdir=dict(),
        server_name=dict(),
        node_name=dict(),
        password=dict(),
        request_timeout=dict(),

    )
    module = DsmcAdapter(argument_spec=argument_spec, supports_check_mode=True)
    backup_action = module.params.get('backup_action')
    filespec = module.params.get('filespec')
    option_params = {
        'absolute': 'absolute',
        'is_compression_enabled': 'compression',
        'is_compress_always': 'compressalways',
        'diff_snapshot': 'diffsnapshot',
        'dirs_only': 'dirsonly',
        'file_list': 'filelist',
        'files_only': 'filesonly',
        'remove_operand_limit': 'removeoperandlimit',
        'snapshot_root': 'snapshotroot',
        'is_subdir': 'subdir',
    }
    option_params_no_value = [
        "absolute",
        "filesonly",
        "dirsonly",
        "removeoperandlimit",
    ]
    options = ''
    for opt in option_params.keys():
        value = module.params.get(opt)
        if value is not None:
            value = str(value)
            if option_params[opt] in option_params_no_value:
                if value.lower() == "yes":
                    options += f" -{option_params[opt]}"
            else:
                options += f" -{option_params[opt]}={value}"

    rc, output, error = module.perform_action(backup_action, filespec, options)

if __name__ == "__main__":
    main()

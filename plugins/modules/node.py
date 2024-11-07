#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2024,Tom page <tpage@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# ibm.storage_protect.register:
#    node: "{{ physical_node }}"
#    url: "{{ tcp_node_address }}"
#    username: "{{ username }}"
#    password: "{{ password }}"
#    state: present

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: node
author: "Tom Page (@Tompage1994)"
short_description: Register or Remove a client node and set its configuration in IBM Storage Protect
description:
    - Register or Remove a client node and set its configuration in IBM Storage Protect
options:
    name:
      description:
        - The name of the node to register or deregister
      required: True
      type: str
      aliases:
        - name
    schedules:
      description:
        - The name of the exising schedules to associate with the node
      required: True
      type: list
      elements: str
    node_password:
      description:
        - Specifies the client node password
        - If you authenticate passwords locally with the IBM Storage Protect server, you must specify a password.
        - The minimum length of the password is 15 characters unless a different value is specified by using the SET MINPWLENGTH command.
        - The maximum length of the password is 64 characters.
      type: str
    node_password_expiry:
      description:
        - Specifies the number of days the password remains valid
        - You can set the password expiration period 0 - 9999 days. A value of 0 means that the password never expires.
        - If you do not specify this parameter, the server common-password expiration period is used which is 90 days unless changed.
      type: int
    user_id:
      description:
        - Administrative user ID with client owner authority or 'NONE' (the default value).
      required: false
      type: str
    contact:
      description:
        - Contact information for the node, up to 255 characters.
      required: false
      type: str
    policy_domain:
      description:
        - The policy domain to assign the node to. Default is 'STANDARD'.
      required: false
      type: str
    compression:
      description:
        - Defines whether the node compresses files before sending them to the server.
      choices: ['client', 'true', 'false']
      default: 'client'
      required: false
      type: str
    can_archive_delete:
      description:
        - Specifies whether the node can delete archived data.
      required: false
      type: bool
    can_backup_delete:
      description:
        - Specifies whether the node can delete backed-up data.
      required: false
      type: bool
    option_set:
      description:
        - Client option set to be used by the node.
      required: false
      type: str
    force_password_reset:
      description:
        - Forces a password reset on the node upon the next login.
      required: false
      type: bool
    node_type:
      description:
        - Specifies the type of node being registered. System default is 'Client'.
      choices: ['client', 'nas', 'server', 'objectclient']
      required: false
      type: str
    url:
      description:
        - URL associated with the node.
      required: false
      type: str
    utility_url:
      description:
        - Utility URL for the node.
      required: false
      type: str
    max_mount_points:
      description:
        - Maximum number of mount points for the node.
        - The default value is 1. You can specify an integer in the range 0 - 999.
      required: false
      type: int
    auto_rename_file_spaces:
      description:
        - Specifies whether file spaces should be automatically renamed.
      choices: ['client', 'true', 'false']
      default: 'No'
      required: false
      type: str
    keep_mount_points:
      description:
        - Specifies if mount points should persist after use.
      required: false
      type: bool
    max_transaction_group:
      description:
        - Maximum number of objects in a single transaction group.
        - The default value is 0. Specifying 0 indicates that the node uses the server global value that is set in the server options file.
        - To use a value other than the server global value, specify a value in the range 4 - 65000.
      required: false
      type: int
    data_write_path:
      description:
        - Defines the data write path.
      choices: ['any', 'lan', 'lanfree']
      default: 'any'
      required: false
      type: str
    data_read_path:
      description:
        - Defines the data read path.
      choices: ['any', 'lan', 'lanfree']
      default: 'any'
      required: false
      type: str
    target_level:
      description:
        - Specifies the target replication level for the node.
        - The parameter applies only to nodes with a type of CLIENT.
        - You can substitute an applicable release package for Version.Release.Modification.Fix (V.R.M.F) Level. For example: TARGETLevel=7.1.0.0.
      required: false
      type: str
    session_initiation:
      description:
        - Determines whether the session is initiated by the client or server.
      choices: ['clientorserver', 'serveronly']
      default: 'clientorserver'
      required: false
      type: str
    session_ip:
      description:
        - Specifies the client IP address that the server contacts to initiate scheduled events.
        - Matches to the HLAddress Parameter for the dsmadmc CLI.
      required: false
      type: str
    session_port:
      description:
        - Specifies the client port number on which the client listens for sessions from the server.
        - Matches to the LLAddress Parameter for the dsmadmc CLI.
      required: false
      type: int
    email:
      description:
        - Email address associated with the node.
      required: false
      type: str
    deduplication:
      description:
        - Enables deduplication for the node.
      choices: ['clientorserver', 'serveronly']
      default: 'clientorserver'
      required: false
      type: str
    backup_initiation:
      description:
        - Specifies backup initiation type.
      choices: ['all', 'root']
      default: 'all'
      required: false
      type: str
    repl_state:
      description:
        - Controls the replication state for the node.
      choices: ['enabled', 'disabled']
      required: false
      type: str
    backup_repl_rule_default:
      description:
        - Default rule for backup replication.
      choices: ['ALL_DATA', 'ACTIVE_DATA', 'ALL_DATA_HIGH_PRIORITY', 'ACTIVE_DATA_HIGH_PRIORITY', 'DEFAULT', 'NONE']
      required: false
      type: str
    archive_repl_rule_default:
      description:
        - Default rule for archive replication.
      choices: ['ALL_DATA', 'ACTIVE_DATA', 'ALL_DATA_HIGH_PRIORITY', 'ACTIVE_DATA_HIGH_PRIORITY', 'DEFAULT', 'NONE']
      required: false
      type: str
    space_repl_rule_default:
      description:
        - Default rule for space replication.
      choices: ['ALL_DATA', 'ACTIVE_DATA', 'ALL_DATA_HIGH_PRIORITY', 'ACTIVE_DATA_HIGH_PRIORITY', 'DEFAULT', 'NONE']
      required: false
      type: str
    recover_damaged:
      description:
        - Specifies if the node should recover damaged objects.
      required: false
      type: bool
    role_override:
      description:
        - Specifies the role override.
      choices: ['client', 'server', 'other', 'usereported']
      default: 'usereported'
      required: false
      type: str
    auth_method:
      description:
        - Authentication method for the node.
      choices: ['local', 'ldap']
      default: 'local'
      required: false
      type: str
    session_security:
      description:
        - Specifies whether the node must use the most secure settings to communicate with an IBM Storage Protect server.
        - The system will default to "transitional"
      choices: ["strict", "transitional"]
      default: 'transitional'
      type: str
    split_large_objects:
      description:
        - Specifies if large objects should be split during backup.
      required: false
      type: bool
    min_extent_size:
      description:
        - Minimum size of extents in KB (50, 250, or 750).
      choices: [50, 250, 750]
      default: 50
      required: false
      type: int
    state:
      description:
        - Desired state of the registration.
        - States 'present' and 'registered' have the same effect.
        - States 'absent', 'deregistered' and 'removed' have the same effect.
      default: "registered"
      choices: ["present", "absent", "registered", "deregistered", "removed"]
      type: str

extends_documentation_fragment: ibm.storage_protect.auth
...
'''


EXAMPLES = '''
- name: Register node
  ibm.storage_protect.node:
    name: "{{ physical_node }}"
    node_password: P@ssword123456789
    node_password_expiry: 90
    policy_domain: "DOMAIN1"
    compression: true
    auth_method: "local"
    contact: "admin@company.com"
    server_name: "{{ tcp_node_address }}"
    username: "{{ username }}"
    password: "{{ password }}"
    state: registered

- name: Deregister node
  ibm.storage_protect.node:
    name: "{{ physical_node }}"
    server_name: "{{ tcp_node_address }}"
    username: "{{ username }}"
    password: "{{ password }}"
    state: deregistered
...
'''

from ..module_utils.dsmadmc_adapter import DsmadmcAdapter


def main():
    argument_spec = dict(
        name=dict(required=True, aliases=['node']),
        schedules=dict(type='list', elements='str'),
        node_password=dict(no_log=True),
        node_password_expiry=dict(type='int', no_log=False),
        user_id=dict(),
        contact=dict(),
        policy_domain=dict(),
        compression=dict(choices=['client', 'true', 'false'], default='client'),
        can_archive_delete=dict(type='bool'),
        can_backup_delete=dict(type='bool'),
        option_set=dict(),
        force_password_reset=dict(type='bool', no_log=False),
        node_type=dict(choices=['client', 'nas', 'server', 'objectclient']),
        url=dict(),
        utility_url=dict(),
        max_mount_points=dict(type='int'),
        auto_rename_file_spaces=dict(choices=['client', 'true', 'false'], default='false'),
        keep_mount_points=dict(type='bool'),
        max_transaction_group=dict(type='int'),
        data_write_path=dict(choices=['any', 'lan', 'lanfree'], default='any'),
        data_read_path=dict(choices=['any', 'lan', 'lanfree'], default='any'),
        target_level=dict(),
        session_initiation=dict(choices=['clientorserver', 'serveronly'], default='clientorserver'),
        session_ip=dict(),
        session_port=dict(),
        email=dict(),
        deduplication=dict(choices=['clientorserver', 'serveronly'], default='clientorserver'),
        backup_initiation=dict(choices=['all', 'root'], default='all'),
        repl_state=dict(choices=['enabled', 'disabled']),
        backup_repl_rule_default=dict(choices=['ALL_DATA', 'ACTIVE_DATA', 'ALL_DATA_HIGH_PRIORITY', 'ACTIVE_DATA_HIGH_PRIORITY', 'DEFAULT', 'NONE']),
        archive_repl_rule_default=dict(choices=['ALL_DATA', 'ACTIVE_DATA', 'ALL_DATA_HIGH_PRIORITY', 'ACTIVE_DATA_HIGH_PRIORITY', 'DEFAULT', 'NONE']),
        space_repl_rule_default=dict(choices=['ALL_DATA', 'ACTIVE_DATA', 'ALL_DATA_HIGH_PRIORITY', 'ACTIVE_DATA_HIGH_PRIORITY', 'DEFAULT', 'NONE']),
        recover_damaged=dict(type='bool'),
        role_override=dict(choices=['client', 'server', 'other', 'usereported'], default='usereported'),
        auth_method=dict(choices=['local', 'ldap'], default='local'),
        session_security=dict(choices=['transitional', 'strict'], default='transitional'),
        split_large_objects=dict(type='bool'),
        min_extent_size=dict(type='int', choices=[50, 250, 750], default=50),
        state=dict(choices=['present', 'absent', 'registered', 'deregistered', 'removed'], default='present'),
    )

    required_by = {
        'backup_repl_rule_default': 'repl_state',
        'archive_repl_rule_default': 'repl_state',
        'space_repl_rule_default': 'repl_state',
        'schedules': 'policy_domain',
    }

    module = DsmadmcAdapter(argument_spec=argument_spec, supports_check_mode=True, required_by=required_by)

    name = module.params.get('name')
    state = module.params.get('state')
    exists, existing = module.find_one('node', name)

    if state == 'absent' or state == 'deregistered' or state == 'removed':
        module.perform_action('remove', 'node', name, exists=exists)
    else:
        options_params = {
            'node_password_expiry': 'PASSExp',
            'user_id': 'USerid',
            'contact': 'CONtact',
            'policy_domain': 'DOmain',
            'compression': 'COMPression',
            'can_archive_delete': 'ARCHDELete',
            'can_backup_delete': 'BACKDELete',
            'option_set': 'CLOptset',
            'force_password_reset': 'FORCEPwreset',
            'node_type': 'Type',
            'url': 'URL',
            'utility_url': 'UTILITYUrl',
            'max_mount_points': 'MAXNUMMP',
            'auto_rename_file_spaces': 'AUTOFSRename',
            'keep_mount_points': 'KEEPMP',
            'max_transaction_group': 'TXNGroupmax',
            'data_write_path': 'DATAWritepath',
            'data_read_path': 'DATAReadpath',
            'target_level': 'TARGETLevel',
            'session_initiation': 'SESSIONINITiation',
            'session_ip': 'HLAddress',
            'session_port': 'LLAddress',
            'email': 'EMAILADdress',
            'deduplication': 'DEDUPlication',
            'backup_initiation': 'BACKUPINITiation',
            'repl_state': 'REPLState',
            'backup_repl_rule_default': 'BKREPLRuledefault',
            'archive_repl_rule_default': 'ARREPLRuledefault',
            'space_repl_rule_default': 'SPREPLRuledefault',
            'recover_damaged': 'RECOVERDamaged',
            'role_override': 'ROLEOVERRIDE',
            'auth_method': 'AUTHentication',
            'session_security': 'SESSIONSECurity',
            'split_large_objects': 'SPLITLARGEObjects',
            'min_extent_size': 'MINIMUMExtentsize',
        }

        not_on_update = ['node_type', 'backup_repl_rule_default', 'archive_repl_rule_default', 'space_repl_rule_default', 'user_id', 'option_set']

        node_password = module.params.get('node_password')
        if node_password:
            module.warn(
                'The node_password field has encrypted data and may inaccurately report task is changed.'
            )

        options = f"{node_password if node_password else ''}"

        for opt in options_params.keys():
            value = module.params.get(opt)
            if value is not None and not (exists and opt in not_on_update):
                value = str(value)
                if value.lower() == 'true':
                    value = 'Yes'
                elif value.lower() == 'false':
                    value = 'No'
                if opt == 'min_extent_size':
                    value = f'{value}KB'
                options += f" {options_params[opt]}={value}"
            elif value is not None and exists and opt in not_on_update:
                module.warn(f'{opt} can not be updated so will not change if different from existing value.')

        schedules = module.params.get('schedules')
        policy_domain = module.params.get('policy_domain')
        node_schedules = []
        if schedules:
            if exists:
                _, all_schedules, _ = module.run_command(f'-comma q association {policy_domain}', auto_exit=False)
                all_schedules = all_schedules.split('\n')
                for sched in all_schedules:
                    sched = sched.split(',')
                    if len(sched) == 3 and sched[2] == name.upper():
                        node_schedules += [sched[1]]

            for schedule in schedules:
                # Test if schedule exists and fail if not
                module.find_one('schedule', f'{policy_domain} {schedule}', fail_on_not_found=True)

        module.perform_action('update' if exists else 'register', 'node', name, options=options, exists=exists, existing=existing, auto_exit=schedules is None)

        if schedules:
            for schedule in schedules:
                if schedule.upper() not in node_schedules:
                    module.perform_action('define', 'association', f'{policy_domain} {schedule} {name}', auto_exit=False)
                else:
                    # Remove them from the list because we will use this list to remove extra ones
                    node_schedules.remove(schedule.upper())

            # if any schedules exist for the node which weren't listed, then disassociate them
            for schedule in node_schedules:
                module.perform_action('delete', 'association', f'{policy_domain} {schedule} {name}', exists=True, auto_exit=False)

            module.exit_json(**module.json_output)


if __name__ == "__main__":
    main()

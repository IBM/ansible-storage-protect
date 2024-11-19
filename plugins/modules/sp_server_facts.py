#!/usr/bin/python
# coding: utf-8 -*-

from ansible.module_utils.dsmadmc_adapter import DsmadmcAdapter
from ansible.module_utils.sp_server_facts import DSMParser,SpServerResponseMapper

from plugins.modules.node import DOCUMENTATION

DOCUMENTATION = '''
---
module: sp_server_facts
author: "Sarthak Kshirsagar"
short_description: Gather IBM Storage Protect Server facts
description:
    - This module gathers various server facts related to the IBM Storage Protect (SP) server using the DSMADMC command-line interface.
    - It supports multiple queries such as server status, database, monitor settings, storage pools, and more.
    - The output of each query is parsed and returned in a developer-friendly format.

options:
    server_name:
        description: 
            - The name or IP address of the IBM Storage Protect server to query.
    username:
        description: 
            - The username to authenticate with the IBM Storage Protect server.
    password:
        description: 
            - The password associated with the username for authentication.
    q_status:
        description:
            - Whether to gather status information from the server.
        type: bool
        default: False
    q_monitorsettings:
        description:
            - Whether to gather monitor settings information from the server.
        type: bool
        default: False
    q_db:
        description:
            - Whether to gather database information from the server.
        type: bool
        default: False
    q_dbspace:
        description:
            - Whether to gather database space information from the server.
        type: bool
        default: False
    q_log:
        description:
            - Whether to gather log information from the server.
        type: bool
        default: False
    q_domain:
        description:
            - Whether to gather domain information from the server.
        type: bool
        default: False
    q_copygroup:
        description:
            - Whether to gather copygroup information from the server.
        type: bool
        default: False
    q_replrule:
        description:
            - Whether to gather replication rule information from the server.
        type: bool
        default: False
    q_devclass:
        description:
            - Whether to gather device class information from the server.
        type: bool
        default: False
    q_mgmtclass:
        description:
            - Whether to gather management class information from the server.
        type: bool
        default: False
    q_stgpool:
        description:
            - Whether to gather storage pool information from the server.
        type: bool
        default: False
'''

EXAMPLES = '''
---
- name: Gather server facts from IBM Storage Protect server
  sp_server_facts:
    server_name: "sp-server01"
    username: "admin"
    password: "password"
    q_status: true
    q_db: true
    q_stgpool: true
  register: result

- name: Display results
  debug:
    var: result.results

'''
def main():
    argument_spec = dict(
        server_name=dict(type='str', required=False),
        username=dict(type='str', required=False),
        password=dict(type='str', required=False),
        q_status=dict(type='bool', default=False),
        q_monitorsettings=dict(type='bool', default=False),
        q_db=dict(type='bool', default=False),
        q_dbspace=dict(type='bool', default=False),
        q_log=dict(type='bool', default=False),
        q_domain=dict(type='bool', default=False),
        q_copygroup=dict(type='bool', default=False),
        q_replrule=dict(type='bool', default=False),
        q_devclass=dict(type='bool', default=False),
        q_mgmtclass=dict(type='bool', default=False),
        q_stgpool=dict(type='bool', default=False)
    )

    dsmadmc = DsmadmcAdapter(argument_spec=argument_spec)
    results = {}

    if dsmadmc.params.get('q_status'):
        rc, output, _ = dsmadmc.run_command('q status', auto_exit=False)
        if rc == 0:
            results['q_status'] = DSMParser.parse_q_status(output)

    if dsmadmc.params.get('q_monitorsettings'):
        rc, output, _ = dsmadmc.run_command('q monitorsettings', auto_exit=False)
        if rc == 0:
            results['q_monitorsettings'] = DSMParser.parse_q_monitorsettings(output)

    if dsmadmc.params.get('q_db'):
        rc, output, _ = dsmadmc.run_command('q db', auto_exit=False)
        if rc == 0:
            results['q_db'] = DSMParser.parse_database_info(output)

    if dsmadmc.params.get('q_dbspace'):
        rc, output, _ = dsmadmc.run_command('q dbspace', auto_exit=False)
        if rc == 0:
            results['q_dbspace'] = DSMParser.parse_space_info(output)

    if dsmadmc.params.get('q_log'):
        rc, output, _ = dsmadmc.run_command('q log', auto_exit=False)
        if rc == 0:
            results['q_log'] = DSMParser.parse_space_info(output)

    if dsmadmc.params.get('q_domain'):
        rc, output, _ = dsmadmc.run_command('q domain', auto_exit=False)
        if rc == 0:
            results['q_domain'] = DSMParser.parse_policy_info(output)

    if dsmadmc.params.get('q_copygroup'):
        rc, output, _ = dsmadmc.run_command('q copygroup', auto_exit=False)
        if rc == 0:
            results['q_copygroup'] = DSMParser.parse_policy_settings(output)

    if dsmadmc.params.get('q_replrule'):
        rc, output, _ = dsmadmc.run_command('q replrule', auto_exit=False)
        if rc == 0:
            results['q_replrule'] = DSMParser.parse_replication_rules(output)

    if dsmadmc.params.get('q_devclass'):
        rc, output, _ = dsmadmc.run_command('q devclass', auto_exit=False)
        if rc == 0:
            results['q_devclass'] = DSMParser.parse_device_class(output)

    if dsmadmc.params.get('q_mgmtclass'):
        rc, output, _ = dsmadmc.run_command('q mgmtclass', auto_exit=False)
        if rc == 0:
            results['q_mgmtclass'] = DSMParser.parse_policy_management_class(output)

    if dsmadmc.params.get('q_stgpool'):
        rc, output, _ = dsmadmc.run_command('q stgpool', auto_exit=False)
        if rc == 0:
            results['q_stgpool'] = DSMParser.parse_storage_pool(output)

    mapped_result = SpServerResponseMapper.map_to_developer_friendly(results)

    dsmadmc.exit_json(changed=False, results=mapped_result)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# coding: utf-8 -*-

from ..module_utils.sp_server_facts import DSMParser, SpServerResponseMapper
from ..module_utils.dsmadmc_adapter import DsmadmcAdapter
from  ..module_utils.sp_server_facts import DsmadmcAdapterExtended

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
extends_documentation_fragment: ibm.storage_protect.auth
'''

EXAMPLES = '''
---
- name: Gather server facts from IBM Storage Protect server
  sp_server_facts:
    q_status: true
    q_db: true
    q_stgpool: true
    q_dbspace: false
    q_log: false
    q_domain: false
    q_copygroup: false
    q_replrule: false
    q_devclass: false
    q_mgmtclass: false
    q_stgpool: false
  register: sp_server_facts

- name: Display results
  debug:
    var: sp_server_facts.results
'''
def main():
    argument_spec = dict(
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

    results = {}

    queries = [
        'status',
        'monitorsettings',
        'db',
        'dbspace',
        'log',
        'domain',
        'copygroup',
        'replrule',
        'devclass',
        'mgmtclass',
        'stgpool'
    ]

    dsmadmc = DsmadmcAdapterExtended(argument_spec=argument_spec)
    for query in queries:
        if dsmadmc.params.get(f'q_{query}'):
            rc, output, _ = dsmadmc.run_command(f'q {query}', auto_exit=False)
            if rc == 0:
                results[f'q_{query}'] = getattr(DSMParser, f'parse_q_{query}')(output)

    mapped_result = SpServerResponseMapper.map_to_developer_friendly(results)

    dsmadmc.exit_json(changed=False, results=mapped_result)

if __name__ == '__main__':
    main()

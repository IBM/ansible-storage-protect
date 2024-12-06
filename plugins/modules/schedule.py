#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2024,Tom page <tpage@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: sp_client_policy
author: "Subhajit Patra (@subhpa01)"
short_description: Configure backup schedule policies for IBM Storage Protect clients
description:
    - This module defines backup schedules and assigns client nodes in IBM Storage Protect.
options:
    schedule_name:
        description: Name of the backup schedule.
        required: true
        type: str
    schedule_type:
        description: Type of the schedule (clientaction/admin).
        required: true
        type: str
        choices: ["clientaction", "admin"]
    start_time:
        description: Schedule start time (HH:MM:SS format).
        required: true
        type: str
    period:
        description: Period between backups.
        required: true
        type: int
    period_unit:
        description: Unit of the period (hours/days).
        required: true
        type: str
        choices: ["hours", "days"]
    client_nodes:
        description: List of client nodes to associate with the schedule.
        required: true
        type: list
        elements: str
extends_documentation_fragment: ibm.storage_protect.auth
...
'''


EXAMPLES = '''
- name: Configure backup schedule for client nodes
  ibm.storage_protect.sp_client_policy:
    schedule_name: "{{ DailyBackup }}"
    schedule_type: "{{ clientaction }}"
    start_time: "22:00:00"
    period: 1
    period_unit: "days"
    client_nodes:
      - "node1"
      - "node2"
...
'''

from ..module_utils.dsmadmc_adapter import DsmadmcAdapter


def main():
    argument_spec = dict(
        domain_name=dict(type='str', required=True),
        schedule_name=dict(type='str', required=True),
        action=dict(type='str', choices=['Incremental', 'Selective', 'Archive'], required=True),
        subaction=dict(type='str', choices=['', 'FASTBack', 'SYSTEMState', 'VApp', 'VM'], required=False),
        priority=dict(type='int', default=5),
        start_date=dict(type='str', default=str(datetime.date.today())),
        start_time=dict(type='str', default=datetime.datetime.now().strftime("%H:%M:%S")),
        duration=dict(type='int', default=1),
        dur_units=dict(type='str', choices=['Hours', 'Minutes', 'Days'], default='Hours'),
        max_runtime=dict(type='int', default=0),
        sched_style=dict(type='str', choices=['Enhanced'], default='Enhanced'),
        month=dict(type='str', choices=['ANY', 'JANuary', 'February', 'MARch', 'APril', 'May', 'JUNe', 'JULy', 'AUgust', 'September', 'October', 'November', 'December'], default='ANY'),
        day_of_month=dict(type='str', default='ANY'),
        week_of_month=dict(type='str', choices=['ANY', 'First', 'Second', 'Third', 'Fourth', 'Last'], default='ANY'),
        day_of_week=dict(type='str', choices=['ANY', 'WEEKDay', 'WEEKEnd', 'SUnday', 'Monday', 'TUesday', 'Wednesday', 'THursday', 'Friday', 'SAturday'], default='ANY'),
        expiration=dict(type='str', default='Never')
    )


    module = DsmadmcAdapter(argument_spec=argument_spec, supports_check_mode=True)
    

    schedule_name = module.params["schedule_name"]
    schedule_type = module.params["schedule_type"]
    start_time = module.params["start_time"]
    period = module.params["period"]
    period_unit = module.params["period_unit"]
    client_nodes = module.params["client_nodes"]

    schedule_name = module.params.get('schedule_name')
    state = module.params.get('state')
    exists, existing = module.find_one('schedule', schedule_name)

    if state == 'absent' or state == 'deregistered' or state == 'removed':
        module.perform_action('remove', 'schedule', schedule_name, exists=exists)
    else:
        options_params = {
            'schedule_type': 'Type',
            'start_time': 'STARTTime',
            'period': 'PERiod',
            'period_unit': 'PERUnits',
        }

        not_on_update = ['type']

        options = ""

        for opt in options_params.keys():
            value = module.params.get(opt)
            if value is not None and not (exists and opt in not_on_update):
                value = str(value)
            elif value is not None and exists and opt in not_on_update:
                module.warn(f'{opt} can not be updated so will not change if different from existing value.')


        module.perform_action('schedule', schedule_name, options=options, exists=exists, existing=existing, auto_exit=True)



if __name__ == "__main__":
    main()

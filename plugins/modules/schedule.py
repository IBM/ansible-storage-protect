#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2024,Subhajit Patra <subhpa01@in.ibm.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: schedule
author: Subhajit Patra
short_description: Manage IBM Storage Protect Schedules
description:
    - This module defines schedules in IBM Storage Protect.
    - It uses the dsmadmc CLI for backend operations.
options:
    name:
        description: Name of the schedule to define.
        required: true
        type: str
    policy_domain:
        description: Policy domain to associate with the schedule.
        required: true
        type: str
    description:
        description: Description of the schedule.
        required: false
        type: str
    action:
        description: Type of action to perform.
        type: str
        choices: ['incremental', 'selective', 'archive', 'restore', 'retrieve', 'imagebackup', 'imagerestore', 'command', 'macro']
    subaction:
        description: Sub-action to perform.
        required: false
        type: str
        choices: ['fasrback', 'systemstate', 'vapp', 'vm', '']
    options:
        description: Custom options string.
        required: false
        type: str
    objects:
        description: Objects to process.
        required: false
        type: str
    priority:
        description: Priority of the schedule.
        required: false
        type: int
        default: 5
    start_date:
        description: Start date of the schedule in formal MM/DD/YYYY.
        required: false
        type: str
    start_time:
        description: Start time of the schedule.
        required: false
        type: str
    duration:
        description: Duration of the schedule execution.
        required: false
        type: int
    duration_units:
        description: Units for the schedule duration.
        required: false
        type: str
        choices: ['hours', 'minutes', 'days']
    max_runtime:
        description: Maximum runtime allowed for the schedule.
        required: false
        type: int
    month:
        description: Month for schedule execution.
        required: false
        type: str
    day_of_month:
        description: Day of the month to run the schedule. Can be 'ANY' or a number from -31 through 31, excluding zero. Negative values are a day from the end of the month, counting backwards.
        required: false
        type: str
    week_of_month:
        description: Week of the month to run the schedule.
        required: false
        type: str
    day_of_week:
        description: Day of the week to run the schedule.
        required: false
        type: str
    expiration:
        description: Expiration date of the schedule.
        required: false
        type: str
    state:
        description: Desired state of the schedule.
        default: 'present'
        choices: ['present', 'absent']
        type: str
extends_documentation_fragment: ibm.storage_protect.auth
...
'''

EXAMPLES = '''
- name: Define an IBM Storage Protect schedule
  ibm.storage_protect.schedule:
    policy_domain: "PROD_DOMAIN"
    name: "Daily_Backup"
    description: "Daily incremental backup"
    action: "Incremental"
    start_date: "2024-12-06"
    start_time: "23:00"
    duration: 2
    duration_units: "Hours"
    max_runtime: 4
...
'''

from ..module_utils.dsmadmc_adapter import DsmadmcAdapter


def main():
    argument_spec = dict(
        name=dict(required=True),
        policy_domain=dict(required=True),
        description=dict(type='str'),
        action=dict(
            choices=[
                'incremental', 'selective', 'archive',
                'backup', 'restore', 'retrieve',
                'imagebackup', 'imagerestore', 'command', 'macro'
            ]
        ),
        subaction=dict(
            choices=['', 'fastback', 'systemstate', 'vapp', 'vm']
        ),
        options=dict(),
        objects=dict(),
        priority=dict(type='int'),
        start_date=dict(),
        start_time=dict(),
        duration=dict(type='int'),
        duration_units=dict(
            choices=['hours', 'minutes', 'days']
        ),
        max_runtime=dict(type='int'),
        month=dict(
            choices=[
                'any', 'january', 'february', 'march', 'april', 'may',
                'june', 'july', 'august', 'september', 'october', 'november', 'december'
            ]
        ),
        day_of_month=dict(),
        week_of_month=dict(
            choices=['any', 'first', 'second', 'third', 'fourth', 'last']
        ),
        day_of_week=dict(
            choices=[
                'any', 'weekday', 'weekend', 'sunday', 'monday',
                'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'
            ]
        ),
        expiration=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    mutually_exclusive = [('day_of_month', 'day_of_week')]

    module = DsmadmcAdapter(argument_spec=argument_spec, mutually_exclusive=mutually_exclusive)

    name = module.params.get('name')
    policy_domain = module.params.get('policy_domain')
    fq_name = f'{policy_domain} {name}'
    state = module.params.get('state')
    exists, existing = module.find_one('schedule', fq_name)

    if state == 'absent':
        module.perform_action('remove', 'schedule', fq_name, exists=exists)
    else:
        options_params = {
            'description': 'DESCription',
            'action': 'ACTion',
            'subaction': 'SUBACTion',
            'options': 'OPTions',
            'objects': 'OBJects',
            'priority': 'PRIority',
            'start_date': 'STARTDate',
            'start_time': 'STARTTime',
            'duration': 'DURation',
            'duration_units': 'DURUnits',
            'max_runtime': 'MAXRUNtime',
            'month': 'MONth',
            'day_of_month': 'DAYOFMonth',
            'week_of_month': 'WEEKofmonth',
            'day_of_week': 'DAYofweek',
            'expiration': 'EXPiration',
        }

        options = "Type=Client SCHEDStyle=Enhanced"

        for opt in options_params.keys():
            value = module.params.get(opt)
            if value is not None:
                value = str(value)
                options += f' {options_params[opt]}=\\"{value}\\"'

        module.perform_action('update' if exists else 'define', 'schedule', fq_name, options=options, exists=exists, existing=existing)


if __name__ == "__main__":
    main()

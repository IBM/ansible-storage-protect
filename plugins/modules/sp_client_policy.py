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
        schedule_name=dict(type="str", required=True),
        schedule_type=dict(type="str", required=True, choices=["clientaction", "admin"]),
        start_time=dict(type="str", required=True),
        period=dict(type="int", required=True),
        period_unit=dict(type="str", required=True, choices=["hours", "days"]),
        client_nodes=dict(type="list", elements="str", required=True)
    )

    required_by = {
        'backup_repl_rule_default': 'replication_state',
        'archive_repl_rule_default': 'replication_state',
        'space_repl_rule_default': 'replication_state',
        # 'schedules': 'policy_domain',
    }

    module = DsmadmcAdapter(argument_spec=argument_spec, supports_check_mode=True, required_by=required_by)
    

    schedule_name = module.params["schedule_name"]
    schedule_type = module.params["schedule_type"]
    start_time = module.params["start_time"]
    period = module.params["period"]
    period_unit = module.params["period_unit"]
    client_nodes = module.params["client_nodes"]

    schedule_name = module.params.get('schedule_name')
    state = module.params.get('state')
    exists, existing = module.find_one('sp_client_policy', schedule_name)

    if state == 'absent' or state == 'deregistered' or state == 'removed':
        module.perform_action('remove', 'sp_client_policy', schedule_name, exists=exists)
    else:
        options_params = {
            'schedule_type': 'Client',
            'start_time': 'current_time',
            'period': '1',
            'period_unit': 'DAYS',
            'client_nodes': 'client_nodes',
        }

        not_on_update = ['node_type', 'backup_repl_rule_default', 'archive_repl_rule_default', 'space_repl_rule_default', 'admin_user_id', 'option_set']

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
                    if len(sched) == 3 and sched[2] == schedule_name.upper():
                        node_schedules += [sched[1]]

            for schedule in schedules:
                # Test if schedule exists and fail if not
                module.find_one('schedule', f'{policy_domain} {schedule}', fail_on_not_found=True)

        module.perform_action('sp_client_policy', schedule_name, options=options, exists=exists, existing=existing, auto_exit=schedules is None)

        if schedules:
            for schedule in schedules:
                if schedule.upper() not in node_schedules:
                    module.perform_action('define', 'association', f"DEFINE SCHEDULE {schedule_name} "
            f"TYPE={schedule_type} "
            f"STARTDATE=TODAY STARTTIME={start_time} "
            f"PERIOD={period} PERIODUNIT={period_unit}", auto_exit=False)
                else:
                    # Remove them from the list because we will use this list to remove extra ones
                    node_schedules.remove(schedule.upper())

            # if any schedules exist for the node which weren't listed, then disassociate them
            for schedule in node_schedules:
                module.perform_action('delete', 'association', f"DEFINE SCHEDULE {schedule_name} "
            f"TYPE={schedule_type} "
            f"STARTDATE=TODAY STARTTIME={start_time} "
            f"PERIOD={period} PERIODUNIT={period_unit}", exists=True, auto_exit=False)

            module.exit_json(**module.json_output)


if __name__ == "__main__":
    main()

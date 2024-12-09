#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2024,Subhajit Patra <subhpa01@in.ibm.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native
from datetime import datetime

# Import the custom DsmadmcAdapter class from the previous code
from ansible.module_utils.dsmadmc_adapter import DsmadmcAdapter


def run_module():
    argument_spec = dict(
        domain_name=dict(type='str', required=True),
        schedule_name=dict(type='str', required=True),
        description=dict(type='str', required=False, default=""),
        action=dict(
            type='str',
            required=True,
            choices=[
                'Incremental', 'Selective', 'Archive',
                'Backup', 'Restore', 'Retrieve',
                'IMAGEBACkup', 'IMAGEREStore', 'Command', 'Macro'
            ]
        ),
        subaction=dict(
            type='str',
            required=False,
            choices=['', 'FASTBack', 'SYSTEMSTate', 'VApp', 'VM']
        ),
        options=dict(type='str', required=False, default=""),
        objects=dict(type='str', required=False, default=""),
        priority=dict(type='int', required=False, default=5),
        start_date=dict(type='str', required=False, default=str(datetime.today().date())),
        start_time=dict(type='str', required=False, default=str(datetime.now().time().replace(second=0, microsecond=0))),
        duration=dict(type='int', required=False, default=1),
        dur_units=dict(
            type='str',
            required=False,
            default='Hours',
            choices=['Hours', 'Minutes', 'Days']
        ),
        max_runtime=dict(type='int', required=False, default=0),
        sched_style=dict(
            type='str',
            required=False,
            default='Enhanced',
            choices=['Enhanced']
        ),
        month=dict(
            type='str',
            required=False,
            default='ANY',
            choices=[
                'ANY', 'JAnuary', 'February', 'MARch', 'APril', 'May',
                'JUNe', 'JULy', 'AUgust', 'September', 'October', 'November', 'December'
            ]
        ),
        day_of_month=dict(type='str', required=False, default='ANY'),
        week_of_month=dict(
            type='str',
            required=False,
            default='ANY',
            choices=['ANY', 'FIrst', 'Second', 'Third', 'FOurth', 'Last']
        ),
        day_of_week=dict(
            type='str',
            required=False,
            default='ANY',
            choices=[
                'ANY', 'WEEKDay', 'WEEKEnd', 'SUnday', 'Monday',
                'TUesday', 'Wednesday', 'THursday', 'Friday', 'SAturday'
            ]
        ),
        expiration=dict(
            type='str',
            required=False,
            default='Never',
            choices=['Never', 'date']
        )
    )

    module = DsmadmcAdapter(argument_spec=argument_spec)

    domain_name = module.params['domain_name']
    schedule_name = module.params['schedule_name']
    description = module.params['description']
    action = module.params['action']
    subaction = module.params['subaction']
    options = module.params['options']
    objects = module.params['objects']
    priority = module.params['priority']
    start_date = module.params['start_date']
    start_time = module.params['start_time']
    duration = module.params['duration']
    dur_units = module.params['dur_units']
    max_runtime = module.params['max_runtime']
    sched_style = module.params['sched_style']
    month = module.params['month']
    day_of_month = module.params['day_of_month']
    week_of_month = module.params['week_of_month']
    day_of_week = module.params['day_of_week']
    expiration = module.params['expiration']

    command = (
        f"DEFine SCHedule {domain_name} {schedule_name} "
        f"Type=Client DESCription=\"{description}\" ACTion={action} "
        f"{f'SUBACTion={subaction}' if subaction else ''} "
        f"{f'OPTions={options}' if options else ''} "
        f"{f'OBJects={objects}' if objects else ''} "
        f"PRIority={priority} STARTDate={start_date} STARTTime={start_time} "
        f"DURation={duration} DURUnits={dur_units} MAXRUNtime={max_runtime} "
        f"SCHEDStyle={sched_style} MONth={month} DAYOFMonth={day_of_month} "
        f"WEEKofmonth={week_of_month} DAYofweek={day_of_week} "
        f"EXPiration={expiration}"
    )

    # Execute the command
    try:
        rc, out, err = module.run_command(command, auto_exit=True)
        module.exit_json(changed=True, output=out)
    except Exception as e:
        module.fail_json(msg=f"Failed to define schedule: {to_native(e)}")


if __name__ == '__main__':
    run_module()

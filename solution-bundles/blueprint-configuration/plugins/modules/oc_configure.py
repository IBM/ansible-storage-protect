from ansible.module_utils.basic import AnsibleModule
from ..module_utils.dsmadmc_adapter import DsmadmcAdapter

DOCUMENTATION='''
---
module: oc_configure
author: Sarthak Kshirsagar
short_description: Configure, stop, or restart IBM Storage Protect Operations Center
description:
  - Configures IBM Storage Protect Operations Center.
  - Stops or restarts the Operations Center (OC) service.
options:
  admin_name:
    description:
      - The name of the admin user of the hub server.
    required: true
    type: str
  action:
    description:
      - The action to be performed using this module.
    required: true
    type: str
    choices:
      - configure
      - restart
      - stop

'''

EXAMPLES='''
---
- name: Configure OC
  ibm.storage_protect.oc_configure:
    admin_name: tsmuser1
    action: configure

- name: Stop OC
  ibm.storage_protect.oc_configure:
    admin_name: tsmuser1
    action: stop

- name: Start OC
  ibm.storage_protect.oc_configure:
    admin_name: tsmuser1
    action: restart
'''
def main():
    argument_spec = dict(
        admin_name=dict(type='str', required=False),
        action=dict(type='str', required=True, choices=['configure', 'restart', 'stop'])
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    dsmadmc_adapter = DsmadmcAdapter(argument_spec=argument_spec)

    admin_name = module.params['admin_name']
    action = module.params['action']

    if action == 'configure' and not admin_name:
        module.fail_json(msg="'admin_name' is required when action is 'configure'")

    rc, out, err = module.run_command('systemctl status opscenter.service')

    if 'could not be found' in (out + err).lower() or 'not-found' in (out + err).lower():
        module.fail_json(msg="OC is not installed or service is not registered.")

    if action == 'configure':
        rc, out, err = dsmadmc_adapter.run_command(
            f'update admin {admin_name} sessionsecurity=transitional',
            auto_exit=False
        )
        if rc == 0:
            module.exit_json(
                msg="OC configuration complete. Access the OC at https://<hostname>:<port>/oc",
                stdout=out,
                changed=False
            )
        else:
            module.fail_json(msg='Failed to configure the OC', stdout=out, stderr=str(err))

    else:
        rc, out, err = module.run_command(["systemctl", action, "opscenter.service"])
        if rc == 0:
            module.exit_json(changed=True,stdout=out,tderr=err)
        else:
            module.fail_json(
                msg=f'Failed to {action} the OC',
                stdout=out,
                stderr=err,
                changed=False
            )

if __name__ == '__main__':
    main()

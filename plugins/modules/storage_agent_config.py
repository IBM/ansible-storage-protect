from ansible.module_utils.basic import AnsibleModule
import os
from ..module_utils.dsmadmc_adapter import DsmadmcAdapter
from ..module_utils.dsmc_adapter import DsmcAdapter

EXAMPLES = '''
---
- name: Configure Storage Agent on server side
  hosts: server
  ibm.storage_protect.storage_agent_configure:
    stg_agent_name: true
    server_name: true
    stg_agent_password: true
    stg_agent_hl_add: false
    lladdress: false
    library: false
    device: false
    stg_agent_path_name: false
    stg_agent_path_dest: false
    copygroup_domain: false
    copygroup_policyset: false
    copygroup_mngclass: false
    copygroup_destination: false
    validate_lan_free: false
    node_name: false
    stg_pool: false
    config_role: server
    client_options_file_path: false
    stg_agent_options_file_path: false
    server_tcp_port: false
    server_hl_address: false
    server_password: false

- name: Configure Storage Agent on client side
  hosts: client
  ibm.storage_protect.storage_agent_configure:
    stg_agent_name: true
    server_name: true
    stg_agent_hl_add: false
    lladdress: false
    config_role: client
    client_options_file_path: false
    stg_agent_options_file_path: false
    server_tcp_port: false
    server_hl_address: false
    server_password: false

- name: Validate lanfree node
  hosts: all
  ibm.storage_protect.storage_agent_configure:
    stg_agent_name:
    validate_lan_free:
    node_name
...
'''

def main():
    module_args = dict(
        stg_agent_name=dict(type='str', required=True),
        server_name=dict(type='str', required=True),
        stg_agent_password=dict(type='str', required=False),
        stg_agent_hl_add=dict(type='str', required=False),
        lladdress=dict(type='str', required=False),
        stg_agent_path_name=dict(type='str', required=False),
        stg_agent_path_dest=dict(type='str', required=False),
        library=dict(type='str', required=False),
        device=dict(type='str', required=False),
        copygroup_domain=dict(type='str', required=False),
        copygroup_policyset=dict(type='str', required=False),
        copygroup_mngclass=dict(type='str', required=False),
        copygroup_destination=dict(type='str', required=False),
        stg_pool=dict(type='str', required=False),
        validate_lan_free=dict(type='bool', required=False, default=False),
        node_name=dict(type='str', required=False),
        config_role=dict(type='str', required=False, choices=['server', 'client']),
        client_options_file_path=dict(type='str', required=True, default="/opt/tivoli/tsm/client/ba/bin/dsm.sys"),
        stg_agent_options_file_path=dict(type='str', required=False, default='/opt/tivoli/tsm/StorageAgent/bin/dsmsta.opt'),
        server_tcp_port=dict(type='str', required=False),
        server_hl_address=dict(type='str', required=False),
        server_password=dict(type='str', required=False),
        server_ip=dict(type='str', required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)
    params = module.params
    changed = False

    dsmadmc_adapter = DsmadmcAdapter(argument_spec=module_args)
    dsmc_adapter = DsmcAdapter(argument_spec=module_args)

    if not params['config_role'] and not params['validate_lan_free']:
        module.fail_json(msg='Either config_role must be provided or validate_lan_free must be True')

    # Validate LAN-Free
    if params['validate_lan_free']:
        if not params['stg_agent_name'] or not params['node_name']:
            module.fail_json(msg="For LAN-Free validation, both stg_agent_name and node_name must be provided.")
        command = f"validate lanfree {params['node_name']} {params['stg_agent_name']}"
        rc, std_out = dsmc_adapter.run_command(command)
        if rc == 0:
            changed = True
        else:
            module.fail_json(msg=f"Failed to validate LAN-Free data movement. Error: {std_out}")

    if params['config_role'] == 'server':
        if not all([params['stg_agent_name'], params['stg_agent_password'], params['stg_agent_hl_add'],
                    params['server_name'], params['server_password'], params['server_hl_address'], params['lladdress'],params['library'],
                    params['stg_agent_path_name'],params['stg_agent_path_dest'],params['device'],
                    params['server_name'],params['server_password'],params['server_hl_address'],params['server_tcp_port'],
                    params['copygroup_domain'],params['copygroup_policyset'],params['copygroup_mngclass'],params['stg_pool'],
                    ]):
            module.fail_json(msg="Missing parameters for configuration.")

        commands = []
        # storage -> server
        define_server = (
            f"define server {params['stg_agent_name']} "
            f"serverpassword={params['stg_agent_password']} "
            f"hladdress={params['stg_agent_hl_add']} "
            f"lladdress={params['lladdress']} ssl=YES "
        )
        commands.append(define_server)
        # path for storage agent
        define_path = (
                f"define path {params['stg_agent_name']} {params['stg_agent_path_name']} "
                f"srctype=server desttype={params['stg_agent_path_dest']} "
                f"library={params['library']} device={params['device']}"
            )
        commands.append(define_path)
        # define copygroup
        define_copygroup = (
                f"define copygroup {params['copygroup_domain']} {params['copygroup_policyset']} "
                f"{params['copygroup_mngclass']} type=backup destination={params['stg_pool']}"
            )
        commands.append(define_copygroup)
        # activate policyset
        activate_policy_set = f"activate policyset {params['copygroup_domain']} {params['copygroup_policyset']}"
        commands.append(activate_policy_set)

        for cmd in commands:
            rc, std_out = dsmadmc_adapter.run_command(cmd)
            if rc != 0:
                module.fail_json(msg=f"Command failed: {cmd}\nError: {std_out}")
        changed = True

        # setup server to server communication
        server_to_server_communication = [
            f"set servername {params['server_name']}",
            f"set serverhladdress {params['server_ip']}",
            f"set serverpassword {params['server_password']}",
            f"set serverlladdress {params['lladdress']}",
        ]

        for cmd in server_to_server_communication:
            rc, std_out = dsmadmc_adapter.run_command(cmd)
            if rc != 0:
                module.fail_json(msg=f"Command failed: {cmd}\nError: {std_out}")
            changed = True

    if params['config_role'] == 'client':
        if not all([params['stg_agent_name'], params['stg_agent_password'], params['stg_agent_hl_add'],
                    params['server_name'], params['server_password'], params['server_tcp_port']]):
            module.fail_json(msg="Missing parameters for client configuration.")

        setstorageserver_command = (
            f"dsmsta setstorageserver myname={params['stg_agent_name']} "
            f"mypassword={params['stg_agent_password']} myhladdress={params['stg_agent_hl_add']} "
            f"servername={params['server_name']} serverpassword={params['server_password']} "
            f"hladdress={params['server_hl_address']} lladdress={params['server_tcp_port']} ssl=yes"
        )

        rc, std_out = dsmc_adapter.run_command(setstorageserver_command)
        if rc != 0:
            module.fail_json(msg=f"Failed to set storage server: {std_out}")
        changed = True

        # Modify dsmsta.opt
        try:
            opt_lines = [
                f"COMMmethod         TCPip",
                f"TCPPort            {params['server_tcp_port']}",
                f"SSLPort            {params['server_tcp_port']}",
                f"SSLadminPort       {params['lladdress']}",
                f"DEVCONFIG          devconfig.txt"
            ]
            with open(params['stg_agent_options_file_path'], 'w') as f:
                f.write("\n".join(opt_lines) + "\n")
        except Exception as e:
            module.fail_json(msg=f"Failed to update dsmsta.opt: {str(e)}")

        # modify dsm.sys file on client for lan-free backup
        try:
            dsm_sys_lines = [
                f"Servername            {params['server_name']}",
                "LANfreeCOMMmethod     tcpip",
                "enablelanfree         yes",
                f"lanfreetcpserveraddress {params['server_ip']}",
                f"lanfreetcpport        {params['lladdress']}"
            ]
            with open(params['client_options_file_path'], 'w') as f:
                f.write("\n".join(dsm_sys_lines) + "\n")
        except Exception as e:
            module.fail_json(msg=f"Failed to update dsm.sys: {str(e)}")
    module.exit_json(changed=changed, msg="Storage agent configuration completed successfully.")

if __name__ == '__main__':
    main()

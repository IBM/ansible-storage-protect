from ansible.module_utils.basic import AnsibleModule
import os
from ..module_utils.dsmadmc_adapter import DsmadmcAdapter

EXAMPLES = '''
---
- name: Configure Storage Agent
  hosts: all
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
    ser_pass: false

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
            stg_agent_server_name=dict(type='str', required=False),
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
            client_options_file_path=dict(type='str', default="/opt/tivoli/tsm/client/ba/bin/dsm.sys"),
            stg_agent_options_file_path=dict(type='str', default='/opt/tivoli/tsm/StorageAgent/bin/dsmsta.opt'),
            stg_agent_bin_dir=dict(type='str', default='/opt/tivoli/tsm/StorageAgent/bin/'),
            server_tcp_port=dict(type='str', required=False),
            server_hl_address=dict(type='str', required=False),
            ser_pass=dict(type='str', required=False),
            start_stg_agent = dict(type=bool,default=True)
        )

    module = AnsibleModule(argument_spec=module_args)
    params = module.params

    # tasks to be performed on the client
    # 1. copy the dsmsta.opt.smp to dsmsta.opt required for setstorageserver command

    rc,std_out,std_err = module.run_command('cp dsmsta.opt.smp dsmsta.opt', cwd=f"{params['stg_agent_bin_dir']}")
    if rc:
        module.fail_json(msg="Failed", std_err=std_err, std_out=std_out)

    # steps to be performed on SP Server
    dsmadmc_adapter = DsmadmcAdapter(argument_spec=module_args)

    # Validate if a node is capable for LAN-Free data movement
    # if params['validate_lan_free']:
    #     if not params['stg_agent_name'] or not params['node_name']:
    #         module.fail_json(msg="For LAN-Free validation, both stg_agent_name and node_name must be provided.")
    #
    #     rc, std_out, std_err = module.run_command(f"./dsmsta", cwd=f"{params['stg_agent_bin_dir']}")
    #     command = f"validate lanfree {params['node_name']} {params['stg_agent_name']}"
    #     rc, std_out = dsmadmc_adapter.run_command(command)

    if not all([params['stg_agent_name'], params['stg_agent_password'], params['stg_agent_hl_add'],
                    params['stg_agent_server_name'], params['ser_pass'], params['server_hl_address'], params['lladdress'],params['library'],
                    params['stg_agent_path_name'],params['stg_agent_path_dest'],params['device'],
                    params['stg_agent_server_name'],params['ser_pass'],params['server_hl_address'],params['server_tcp_port'],
                    params['copygroup_domain'],params['copygroup_policyset'],params['copygroup_mngclass'],params['stg_pool'],
                    params['stg_agent_name'], params['stg_agent_password'], params['stg_agent_hl_add'],
                     params['stg_agent_server_name'], params['ser_pass'], params['server_tcp_port']
                    ]):
        module.fail_json(msg="Please Provide all the parameters")

    commands = []
    result = {}
        # storage -> server
    define_server = (
            f"define server {params['stg_agent_name']} "
            f"serverpassword={params['stg_agent_password']} "
            f"hladdress={params['stg_agent_hl_add']} "
            f"lladdress={params['lladdress']} ssl=YES "
    )
    # path for storage agent
    define_path = (
                f"define path {params['stg_agent_name']} {params['stg_agent_path_name']} "
                f"srctype=server desttype={params['stg_agent_path_dest']} "
                f"library={params['library']} device={params['device']}"
            )
    # define copygroup
    define_copygroup = (
                f"define copygroup {params['copygroup_domain']} {params['copygroup_policyset']} "
                f"{params['copygroup_mngclass']} type=backup destination={params['stg_pool']}"
            )
    activate_policy_set = f"activate policyset {params['copygroup_domain']} {params['copygroup_policyset']}"

    commands.append(define_server)
    commands.append(define_path)
    commands.append(define_copygroup)
    commands.append(activate_policy_set)

    for cmd in commands:
        rc, std_out, std_err = dsmadmc_adapter.run_command(cmd,auto_exit=False)
        result[cmd] = std_out
        if rc!=10 and rc!=0:
            module.fail_json(msg=f"Command failed here2: {cmd}\nError: {std_out}")

    # setup server to server communication
    server_to_server_communication = [
            f"set servername {params['stg_agent_server_name']}",
            f"set serverhladdress {params['server_hl_address']}",
            f"set serverpassword {params['ser_pass']}",
            f"set serverlladdress {params['lladdress']}",
    ]

    for cmd in server_to_server_communication:
        rc, std_out, std_err = dsmadmc_adapter.run_command(cmd,auto_exit=False)
        result[cmd] = std_out
        if rc:
            module.fail_json(msg=f"Command failed here: {cmd}\nError: {std_out}")


    setstorageserver_command = f"./dsmsta setstorageserver myname={params['stg_agent_name']} mypassword={params['stg_agent_password']} myhladdress={params['stg_agent_hl_add']} servername={params['stg_agent_server_name']} serverpassword={params['ser_pass']} hladdress={params['server_hl_address']} lladdress={params['server_tcp_port']} ssl=yes"

    rc, std_out, std_err = module.run_command(setstorageserver_command, cwd=f"{params['stg_agent_bin_dir']}")
    if rc:
        module.fail_json(msg="Failed", std_err=std_err, std_out=std_out)
    result['cmd'] = std_out

    # start stg agent
    if params['start_stg_agent']:
        rc, std_out, std_err = module.run_command(f"./dsmsta",cwd=f"{params['stg_agent_bin_dir']}")
        if rc:
            module.fail_json(msg="Failed to start the storage agent",std_err=std_err,std_out=std_out)
        else:
            result['stg_agent_started'] = True

    try:
        opt_lines = [
                f"Servername {params['stg_agent_server_name']}"
                f"COMMmethod         TCPip",
                f"TCPPort            {params['server_tcp_port']}",
                f"SSLTCPPort            {params['server_tcp_port']}",
                f"SSLTCPadminPort       {params['lladdress']}",
                f"DEVCONFIG          devconfig.txt"
        ]
        os.makedirs(os.path.dirname(params['stg_agent_options_file_path']), exist_ok=True)
        with open(params['stg_agent_options_file_path'], 'w') as f:
            f.write("\n".join(opt_lines) + "\n")
        changed = True
    except Exception as e:
        module.fail_json(msg=f"Failed to update dsmsta.opt: {str(e)}")

 # modify dsm.sys file on client for lan-free backup
    try:
        dsm_sys_lines = [
                f"Servername           {params['stg_agent_server_name']}",
                "LANfreeCOMMmethod     tcpip",
                "enablelanfree         yes",
                f"lanfreetcpserveraddress {params['server_hl_address']}",
                f"lanfreetcpport        {params['lladdress']}",
                f"TCPServeraddress   {params['server_hl_address']}",
        ]
        os.makedirs(os.path.dirname(params['client_options_file_path']), exist_ok=True)
        with open(params['client_options_file_path'], 'w') as f:
            f.write("\n".join(dsm_sys_lines) + "\n")
        changed = True
    except Exception as e:
        module.fail_json(msg=f"Failed to update dsm.sys: {str(e)}")

    module.exit_json(msg="Configured",result=result)

if __name__ == '__main__':
    main()

from ansible.module_utils.basic import AnsibleModule
import os
from ..module_utils.sp_utils import StorageProtectUtils
from ..module_utils.dsmadmc_adapter import DsmadmcAdapter

DOCUMENTATION = '''
---
module: storage_agent_config
author: "Sarthak Kshirsagar"
short_description: Configures IBM Storage Protect Storage Agent
description:
  - This module configures the IBM Storage Protect Storage Agent
  - Module executes the required dsmadmc commands to enable the communication between storage agent and server.
  - Module configures storage agent by executing setstorageserver command on client and adds required parameters in dsmsta.opt and dsm.sys file
options:
    stg_agent_name:
        description:
            - Name of the Storage Agent, which will be defined on the server
        type: str
        default: ''
    stg_agent_server_name:
        description:
            - Name of the server where storage agent will be defined
        type: str
        default: ''
    stg_agent_password:
        description:
            - Password for the storage agent.
        type: str
        default: ''
    stg_agent_hl_add:
        description:
            - High-level address where client and storage agent are installed.
        type: str
        default: ''
    lladdress:
        description:
            - Port on which server will listen for lan free communication
        type: str
        default: ''
    server_tcp_port:
        description:
            - Port for the TCP/IP communication of server
        type: str
        default: ''
    server_hl_address:
        description:
            - High level address of the SP Server
        type: ''
        default: ''
    server_password:
        description:
            - Password for the server, to enable server to server communication
        type: ''
        default: ''
    stg_agent_path_name:
        description:
          - Name to assign to the path when defining the SCSI path on the TSM server.
          - (for example “drv1”, “drv2”) is used in DEFINE PATH commands.
        type: str
        required: false

    stg_agent_path_dest:
      description:
        - Destination type for the SCSI path on the TSM server.
        - Valid values are “drive” (for tape drives) or “library” (for the tape changer).
      type: str
      required: false

    library:
      description:
        - Name of the tape library as defined on the TSM server (e.g. MSLG3LIB).
        - Used when defining the path to tell the server which library the drive belongs to.
      type: str
      required: false

    device:
      description:
        - Device on the storage‐agent host (e.g. “/dev/sg0” or “/dev/st0”).
      type: str
      required: false

    copygroup_domain:
      description:
        - Policy domain under which the LAN‑free copy group resides (e.g. “LANFREEDOMAIN”).
      type: str
      required: false

    copygroup_policyset:
      description:
        - Policy set name within the domain (e.g. “STANDARD”).
      type: str
      required: false

    copygroup_mngclass:
      description:
        - Management class to use for the LAN‑free backup copy (e.g. “LANFREEMGMT”).
      type: str
      required: false

    copygroup_destination:
      description:
        - Storage pool name to which the LAN‑free backup will be written (e.g. “LANFREEPOOL”).
      type: str
      required: false

    validate_lan_free:
      description:
        - If true, run the TSM “VALIDATE LANFREE” command to verify the node/agent path is LAN‑free capable.
        - Does not perform any configuration changes, only validation.
      type: bool
      default: false

    node_name:
      description:
        - Name of the TSM client node registered in the LAN‑free domain (e.g. “LANFREECLIENT”).
        - Used by the validate operation to check that the node can backup via the storage agent.
      type: str
      required: false

    stg_pool:
      description:
        - The TSM server storage pool name where the LAN‑free backup will be written.
        - Should match the pool defined in your copy group (e.g. “LANFREEPOOL”).
      type: str
      required: false
      
    max_attempts:
      description:
        - Specifies the maximum number of times the module will retry the “validate lanfree” command.
        - Because the Storage Agent process can take several seconds to become fully available, each retry is spaced by the configured delay to ensure the agent has time to connect before the final validation attempt.
      type: int
      default: 3
      required: false

extends_documentation_fragment: ibm.storage_protect.auth
...
'''

EXAMPLES = '''
---
- name: Storage agent config
  hosts: all
  become: yes
  environment:
    STORAGE_PROTECT_SERVERNAME: "server2"
    STORAGE_PROTECT_USERNAME: "tsmuser1"
    STORAGE_PROTECT_PASSWORD: "tsmuser1@@123456789"
  tasks:
    - name: Configure client
      ibm.storage_protect.storage_agent_config:
        stg_agent_name: "stgagent8"
        stg_agent_password: "STGAGENT@123456789"
        stg_agent_server_name: "server2"
        stg_agent_hl_add: "client_address"
        lladdress: "1502"
        server_tcp_port: "1500"
        server_hl_address: "server_address"
        server_password: "ServerPassword@@12345"
        stg_agent_path_name: "drv1"
        stg_agent_path_dest: "drive"
        library: "MSLG3LIB"
        device: "/dev/sg1"
        copygroup_domain: "lanfreedomain"
        copygroup_policyset: "standard"
        copygroup_mngclass: "LANFREEMGMT"
        copygroup_destination: "LANFREEPOOL"
        validate_lan_free: false
        node_name: "lanfreeclient"
        stg_pool: "LANFREEPOOL"
      register: stg_agent_config_result

    - name: Validate lanfree
      ibm.storage_protect.storage_agent_config:
        validate_lan_free: true
        node_name: "lanfreeclient"
        stg_agent_name: "stgagent7"
      register: lanfree_out
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
            stg_agent_bin_dir=dict(type='str', default='/opt/tivoli/tsm/StorageAgent/bin'),
            server_tcp_port=dict(type='str', required=False),
            server_hl_address=dict(type='str', required=False),
            server_password=dict(type='str', required=False),
            start_stg_agent = dict(type=bool,default=True),
            imcl_path = dict(type='str', default="/opt/IBM/InstallationManager/eclipse/tools/imcl"),
            max_attempts = dict(type='int', default=3)
        )

    module = AnsibleModule(argument_spec=module_args)
    utils = StorageProtectUtils(module)
    params = module.params
    result = {}

    # Checking availability of Storage Agent via Installation Manager
    # imcl_cmd = f"{params['imcl_path']} listinstalledpackages"
    # rc, imcl_out, imcl_err = module.run_command(imcl_cmd)
    # if rc != 0:
    #     module.fail_json(msg=f"Failed to query installed packages: {imcl_err.strip() or imcl_out.strip()}")
    #
    # if "com.tivoli.dsm.stagent_" not in imcl_out.lower():
    #     module.fail_json(msg="IBM Storage Protect Storage Agent is not installed.")
    # Checking availability of Storage Agent via Installation Manager
    utils.server_component_check(imcl_path=f"{params['imcl_path']}",package_prefix="com.tivoli.dsm.stagent_")

    module.run_command(f"pkill -f {params['stg_agent_bin_dir']}/dsmsta", check_rc=False)

    # Checking availability of BA Client
    utils.rpm_package_check("TIVsm-BA")
    # Checking availability of BA Client
    # rc, rpm_out, rpm_err = module.run_command("rpm -q TIVsm-BA")
    # if rc != 0:
    #     module.fail_json(msg="BA client package 'TIVsm-BA' is not installed.")

    # copy the dsmsta.opt.smp to dsmsta.opt, required for setstorageserver command
    if not params['validate_lan_free']:
        rc,std_out,std_err = module.run_command('cp dsmsta.opt.smp dsmsta.opt', cwd=f"{params['stg_agent_bin_dir']}")
        if rc:
            module.fail_json(msg="Failed to copy dsmsta.opt.smp file", std_err=std_err, std_out=std_out)

    dsmadmc_adapter = DsmadmcAdapter(argument_spec=module_args)

    # Validate if a node is capable for LAN-Free data movement
    if params['validate_lan_free']:
        if not params['stg_agent_name'] or not params['node_name']:
            module.fail_json(msg="For LAN-Free validation, both stg_agent_name and node_name must be provided.")

        agent_bin = params['stg_agent_bin_dir']
        rc, out, err = module.run_command(f"nohup {agent_bin}/dsmsta > {agent_bin}/dsmsta.log 2>&1 &",
                                          cwd=agent_bin, use_unsafe_shell=True)
        if rc != 0:
            module.fail_json(msg="Failed to start storage agent", stderr=err)
        result['start_agent'] = out
        for i in range(params['max_attempts']):
            command = f"validate lanfree {params['node_name']} {params['stg_agent_name']}"
            rc, std_out, std_err = dsmadmc_adapter.run_command(command,auto_exit=False)
            result[command] = std_out
        module.exit_json(msg="Lanfree Validation Completed",result=result)

    if not all([params['stg_agent_name'], params['stg_agent_password'], params['stg_agent_hl_add'],
                    params['stg_agent_server_name'], params['server_password'], params['server_hl_address'], params['lladdress'],params['library'],
                    params['stg_agent_path_name'],params['stg_agent_path_dest'],params['device'],
                    params['stg_agent_server_name'],params['server_password'],params['server_hl_address'],params['server_tcp_port'],
                    params['copygroup_domain'],params['copygroup_policyset'],params['copygroup_mngclass'],params['stg_pool'],
                    params['stg_agent_name'], params['stg_agent_password'], params['stg_agent_hl_add'],
                     params['stg_agent_server_name'], params['server_password'], params['server_tcp_port']
                    ]):
        module.fail_json(msg="Provide all the parameters mentioned in documentation")

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
        result[cmd] = f'{std_out}\n'
        if rc!=10 and rc!=0:
            module.fail_json(msg=f"Failed to execute: {cmd}\nError: {std_err}, std_out: {std_out}")

    # setup server to server communication
    server_to_server_communication = [
            f"set servername {params['stg_agent_server_name']}",
            f"set serverhladdress {params['server_hl_address']}",
            f"set serverpassword {params['server_password']}",
            f"set serverlladdress {params['lladdress']}",
    ]

    for cmd in server_to_server_communication:
        rc, std_out, std_err = dsmadmc_adapter.run_command(cmd,auto_exit=False)
        result[cmd] = f'{std_out}\n'
        if rc:
            module.fail_json(msg=f"Failed to execute:  {cmd}\nError: {std_err}")


    setstorageserver_command = f"./dsmsta setstorageserver myname={params['stg_agent_name']} mypassword={params['stg_agent_password']} myhladdress={params['stg_agent_hl_add']} servername={params['stg_agent_server_name']} serverpassword={params['server_password']} hladdress={params['server_hl_address']} lladdress={params['server_tcp_port']} ssl=yes"

    rc, std_out, std_err = module.run_command(setstorageserver_command, cwd=f"{params['stg_agent_bin_dir']}")
    if rc:
        module.fail_json(msg="setstorageserver command failed", std_err=std_err, std_out=std_out)
    result[setstorageserver_command] = f'{std_out}\n'

    try:
        opt_lines = [
                f"Servername {params['stg_agent_server_name'].upper()}",
                f"COMMmethod         TCPip",
                f"TCPPort            {params['server_tcp_port']}",
                f"SSLTCPPort            {params['server_tcp_port']}",
                f"SSLTCPadminPort       {params['lladdress']}",
                f"DEVCONFIG          devconfig.txt"
        ]
        os.makedirs(os.path.dirname(params['stg_agent_options_file_path']), exist_ok=True)
        with open(params['stg_agent_options_file_path'], 'w') as f:
            f.write("\n".join(opt_lines) + "\n")
    except Exception as e:
        module.fail_json(msg=f"Failed to update dsmsta.opt: {str(e)}")

 # modify dsm.sys file on client for lan-free backup
    try:
        dsm_sys_lines = [
                f"Servername           {params['stg_agent_server_name'].upper()}",
                "LANfreeCOMMmethod     tcpip",
                "enablelanfree         yes",
                f"lanfreetcpserveraddress {params['server_hl_address']}",
                f"lanfreetcpport        {params['lladdress']}",
                f"TCPServeraddress   {params['server_hl_address']}",
        ]
        os.makedirs(os.path.dirname(params['client_options_file_path']), exist_ok=True)
        with open(params['client_options_file_path'], 'w') as f:
            f.write("\n".join(dsm_sys_lines) + "\n")

    except Exception as e:
        module.fail_json(msg=f"Failed to update dsm.sys: {str(e)}")

    module.exit_json(msg="Configuration Completed",result=result)

if __name__ == '__main__':
    main()

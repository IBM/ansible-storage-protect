#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2024,Tom page <tpage@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# ibm.storage_protect.register:
#    node: "{{ physical_node }}"
#    url: "{{ tcp_node_address }}"
#    username: "{{ username }}"
#    password: "{{ password }}"
#    state: present

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: node
author: "Tom page (@Tompage1994)"
short_description: Create a dsm.sys file for interaction with IBM Storage Protect
description:
    - Create a dsm.sys file for interaction with IBM Storage Protect
    - Creates the file on the machine you are connected to.
    - Works also for localhost for running the modules in this collection against a remote IBM Storage Protect Server.
options:
    server_name:
      description:
        - SERVERNAME your IBM Storage Protect instance.
        - If value not set, will try environment variable C(STORAGE_PROTECT_SERVERNAME)
        - If value not specified by any means, the value of C(local) will be used
      type: str
    comm_method:
      description:
        - Specifies a communication method to be used by the server.
      type: str
      default: "tcpip"
      choices: ["namedpipes", "none", "sharedmem", "tcpip", "v6tcpip"]
    tcp_port:
      description:
        - The TCPPORT option specifies the port number on which the server TCP/IP communication driver waits for requests for client sessions.
        - Valid values are 1024 - 32767
      type: int
      default: 1500
    tcp_server_address:
      description:
        - Specifies the TCP/IP address for the IBM Storage Protect server.
        - Can be an IP address or TCP/IP domain name
      type: str
      default: "127.0.0.1"
    tcp_admin_port:
      description:
        - Specifies the port number on which the server TCP/IP communication driver waits for requests for TCP/IP sessions other than client sessions
        - The default is the tcp_port
      type: int
    sysfile_path:
      description:
        - Desired location of the file.
        - Note that is the location is changes then you will need to ensure that this file is properly used.
      default: "/opt/tivoli/tsm/client/ba/bin/dsm.sys"
      type: str
    state:
      description:
        - Desired state of the file.
      default: "present"
      choices: ["present", "absent"]
      type: str

'''


EXAMPLES = '''
- name: Create dsm.sys
  ibm.storage_protect.sysfile:
    server_name: "ibmsp01"
    tcp_server_address: "10.10.10.10"

- name: Create dsm copy in /tmp
  ibm.storage_protect.sysfile:
    server_name: "ibmsp01test"
    tcp_server_address: "10.10.10.10"
    sysfile_path: /tmp/dsm.sym
'''

from ansible.module_utils.basic import AnsibleModule, env_fallback
import os


def main():
    argument_spec = dict(
        server_name=dict(required=False, fallback=(env_fallback, ['STORAGE_PROTECT_SERVERNAME'])),
        comm_method=dict(choices=['namedpipes', 'none', 'sharedmem', 'tcpip', 'v6tcpip'], default='tcpip'),
        tcp_port=dict(type='int', default=1500),
        tcp_server_address=dict(default='127.0.0.1'),
        tcp_admin_port=dict(type='int'),
        sysfile_path=dict(default='/opt/tivoli/tsm/client/ba/bin/dsm.sys'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    server_name = module.params.get('server_name') or 'local'
    comm_method = module.params.get('comm_method')
    tcp_port = module.params.get('tcp_port')
    tcp_server_address = module.params.get('tcp_server_address')
    tcp_admin_port = module.params.get('tcp_admin_port')

    sysfile_path = module.params.get('sysfile_path')
    state = module.params.get('state')

    if state == 'present':
        changed = False
        file_exists = os.path.isfile(sysfile_path)

        content = f"""SERVERNAME {server_name}
COMMMETHOD {comm_method}
TCPPORT {tcp_port}
TCPSERVERADDRESS {tcp_server_address}
{('TCPADMINPORT ' + str(tcp_admin_port)) if tcp_admin_port else ''}
"""

        if file_exists:
            with open(sysfile_path, 'r') as f:
                existing_content = f.read()
                changed = existing_content != content
                if not changed:
                    module.exit_json(path=sysfile_path, content=content)
        else:
            os.makedirs(os.path.dirname(sysfile_path), exist_ok=True)
        with open(sysfile_path, 'w') as sysfile:
            sysfile.write(content)
        module.exit_json(changed=True, path=sysfile_path, content=content)

    # Delete the file if exists
    else:
        try:
            os.remove(sysfile_path)
            module.exit_json(changed=True)
        except FileNotFoundError:
            module.exit_json()


if __name__ == "__main__":
    main()

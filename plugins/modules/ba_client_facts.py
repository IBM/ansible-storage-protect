#!/usr/bin/python
# coding: utf-8 -*-

import sys
import json
import platform

# Try to import the real Ansible module (Linux / normal use)
HAS_ANSIBLE = False
try:
    from ansible.module_utils.basic import AnsibleModule
    HAS_ANSIBLE = True
except Exception:
    # On Windows (or no-ansible environment) we'll fall back to a shim
    AnsibleModule = None

try:
    # When running as real Ansible module (Linux)
    from ..module_utils.ba_client_facts import DSMCParser, BAClientResponseMapper
    from ..module_utils.ba_client_facts import DsmcAdapterExtended
except ImportError:
    # When running as standalone script (Windows via win_command)
    import sys
    import os
    
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    UTILS_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "module_utils"))
    
    sys.path.insert(0, UTILS_PATH)
    
    from ba_client_facts import DSMCParser, BAClientResponseMapper, DsmcAdapterExtended

DOCUMENTATION = '''
---
module: ba_client_facts
author: "Shalu Mishra"
short_description: Gather IBM Storage Protect BA Client facts
description:
    - This module gathers various facts related to the IBM Storage Protect (SP) Backup-Archive (BA) Client using the DSMC command-line interface.
    - It supports multiple queries such as client version, configuration, schedules, file spaces, and backup status.
    - The output of each query is parsed and returned in a developer-friendly format.
    - Works on Linux, Windows, and AIX platforms.

options:
    q_version:
        description:
            - Whether to gather BA Client version information.
        type: bool
        default: False
    q_session:
        description:
            - Whether to gather current session information.
        type: bool
        default: False
    q_schedule:
        description:
            - Whether to gather schedule information from the server.
        type: bool
        default: False
    q_filespace:
        description:
            - Whether to gather filespace information.
        type: bool
        default: False
    q_backup:
        description:
            - Whether to gather backup information and statistics.
        type: bool
        default: False
    q_archive:
        description:
            - Whether to gather archive information.
        type: bool
        default: False
    q_inclexcl:
        description:
            - Whether to gather include/exclude list information.
        type: bool
        default: False
    q_systeminfo:
        description:
            - Whether to gather system information (OS, hostname, etc.).
        type: bool
        default: False
    q_options:
        description:
            - Whether to gather client options from dsm.opt and dsm.sys.
        type: bool
        default: False

extends_documentation_fragment: ibm.storage_protect.auth
...
'''

EXAMPLES = '''
---
- name: Gather BA Client facts from IBM Storage Protect client
  ibm.storage_protect.ba_client_facts:
    q_version: true
    q_session: true
    q_schedule: true
    q_filespace: true
    q_backup: false
    q_archive: false
    q_inclexcl: false
    q_systeminfo: true
    q_options: true
  register: ba_client_facts

- name: Display BA Client facts
  debug:
    var: ba_client_facts.results

- name: Check if client is at desired version
  debug:
    msg: "Client version is {{ ba_client_facts.results.q_version.client_version }}"
  when: ba_client_facts.results.q_version is defined
...
'''

RETURN = '''
results:
    description: Dictionary containing all requested BA Client facts
    returned: always
    type: dict
    sample:
        q_version:
            client_version: "8.1.25.0"
            client_name: "IBM Storage Protect"
            api_version: "8.1.25.0"
        q_session:
            server_name: "TSM_SERVER"
            server_address: "192.168.1.100"
            server_port: "1500"
            node_name: "CLIENT_NODE"
        q_filespace:
            - filespace_name: "/"
              platform: "Linux"
              capacity_mb: "102400"
              used_mb: "45678"
              backup_start: "2024-01-15 10:30:00"
              backup_end: "2024-01-15 11:45:00"
'''

def build_windows_like_module():
    """
    Create a minimal Ansible-like module for Windows / no-ansible environments.
    - reads CLI args
    - exposes .params
    - exposes .exit_json() / .fail_json()
    """
    import argparse

    parser = argparse.ArgumentParser(description="BA Client facts gathering (no-ansible mode)")

    parser.add_argument("--server-name", dest="server_name", required=True)
    parser.add_argument("--node-name", dest="node_name", required=False)
    parser.add_argument("--password", dest="password", required=False, help="Password (optional if using password file)")
    parser.add_argument("--user-id", dest="user_id", required=False, help="Admin user ID (if different from node name)")
    parser.add_argument("--q-version", dest="q_version", action="store_true", default=False)
    parser.add_argument("--q-session", dest="q_session", action="store_true", default=False)
    parser.add_argument("--q-schedule", dest="q_schedule", action="store_true", default=False)
    parser.add_argument("--q-filespace", dest="q_filespace", action="store_true", default=False)
    parser.add_argument("--q-backup", dest="q_backup", action="store_true", default=False)
    parser.add_argument("--q-archive", dest="q_archive", action="store_true", default=False)
    parser.add_argument("--q-inclexcl", dest="q_inclexcl", action="store_true", default=False)
    parser.add_argument("--q-systeminfo", dest="q_systeminfo", action="store_true", default=False)
    parser.add_argument("--q-options", dest="q_options", action="store_true", default=False)

    args = parser.parse_args()

    # We make an object that looks just enough like DsmcAdapter for the rest of the code.
    class WinModuleShim:
        def __init__(self, args_ns):
            # Use user_id if provided, otherwise use node_name
            effective_user = args_ns.user_id if args_ns.user_id else args_ns.node_name
            effective_node = args_ns.node_name if args_ns.node_name else effective_user
            
            # mimic .params from ansible
            self.params = {
                "server_name": args_ns.server_name,
                "node_name": effective_node,
                "password": args_ns.password,
                "user_id": effective_user,
                "q_version": args_ns.q_version,
                "q_session": args_ns.q_session,
                "q_schedule": args_ns.q_schedule,
                "q_filespace": args_ns.q_filespace,
                "q_backup": args_ns.q_backup,
                "q_archive": args_ns.q_archive,
                "q_inclexcl": args_ns.q_inclexcl,
                "q_systeminfo": args_ns.q_systeminfo,
                "q_options": args_ns.q_options,
            }
            self.server_name = args_ns.server_name
            self.node_name = effective_node
            self.user_id = effective_user
            self.password = args_ns.password
            self.json_output = {'changed': False}

        def exit_json(self, **kwargs):
            # print JSON and exit 0 — similar to Ansible
            print(json.dumps(kwargs, indent=2))
            sys.exit(0)

        def fail_json(self, **kwargs):
            # print JSON and exit non-zero
            kwargs.setdefault("failed", True)
            print(json.dumps(kwargs, indent=2), file=sys.stderr)
            sys.exit(1)

        def warn(self, msg):
            print(f"[Windows WARN] {msg}")

        def log(self, msg):
            print(f"[ba_client_facts] {msg}", file=sys.stderr)

    return WinModuleShim(args)


def get_module():
    """
    Return an object that has the Ansible-like interface.
    - on Linux/AIX/Ansible: real DsmcAdapterExtended
    - on Windows/no-ansible: our shim
    """
    system_platform = platform.system().lower()
    
    if HAS_ANSIBLE and system_platform not in ["windows", "win32"]:
        # Linux, AIX, or other Unix-like systems with Ansible
        argument_spec = dict(
            q_version=dict(type='bool', default=False),
            q_session=dict(type='bool', default=False),
            q_schedule=dict(type='bool', default=False),
            q_filespace=dict(type='bool', default=False),
            q_backup=dict(type='bool', default=False),
            q_archive=dict(type='bool', default=False),
            q_inclexcl=dict(type='bool', default=False),
            q_systeminfo=dict(type='bool', default=False),
            q_options=dict(type='bool', default=False)
        )
        return DsmcAdapterExtended(argument_spec=argument_spec)
    else:
        # Windows / no ansible
        return build_windows_like_module()


def main():
    module = get_module()

    results = {}

    queries = [
        'version',
        'session',
        'schedule',
        'filespace',
        'backup',
        'archive',
        'inclexcl',
        'systeminfo',
        'options'
    ]

    # For Windows shim, we need to handle DSMC commands differently
    if not HAS_ANSIBLE or platform.system().lower() == "windows":
        # Windows standalone mode - execute DSMC commands directly
        import subprocess
        import os
        
        # Find dsmc.exe and its directory - check common locations
        dsmc_paths = [
            r"C:\Program Files\Tivoli\TSM\baclient",
            r"C:\Program Files\Tivoli\TSM\client\ba\bin",
            r"C:\Program Files (x86)\Tivoli\TSM\baclient",
        ]
        
        dsmc_dir = None
        dsmc_exe = None
        for path in dsmc_paths:
            exe_path = os.path.join(path, "dsmc.exe")
            if os.path.exists(exe_path):
                dsmc_dir = path
                dsmc_exe = "dsmc.exe"  # Use relative name since we'll change directory
                break
        
        if not dsmc_dir:
            module.fail_json(msg="Could not find dsmc.exe. Please ensure IBM Storage Protect BA Client is installed.")
        
        for query in queries:
            if module.params.get(f'q_{query}'):
                # Build DSMC command - simple commands without parameters
                # DSMC reads configuration from dsm.opt and uses password file
                if query == 'version':
                    cmd = f'{dsmc_exe} query session'
                elif query == 'session':
                    cmd = f'{dsmc_exe} query session'
                elif query == 'systeminfo':
                    cmd = f'{dsmc_exe} query systeminfo'
                elif query == 'options':
                    cmd = f'{dsmc_exe} query options'
                else:
                    cmd = f'{dsmc_exe} query {query}'
                
                try:
                    # Run from DSMC directory so it can find dsm.opt
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False, timeout=30, cwd=dsmc_dir)
                    if result.returncode == 0 and result.stdout:
                        # Parse the output
                        parsed_data = getattr(DSMCParser, f'parse_q_{query}')(result.stdout)
                        if parsed_data:
                            results[query] = parsed_data
                        else:
                            module.log(f"Query {query} parsing returned None. Output: {result.stdout[:200]}")
                    else:
                        # Log error for debugging - include both stdout and stderr
                        module.log(f"Query {query} failed: rc={result.returncode}, stdout={result.stdout[:200]}, stderr={result.stderr[:200]}")
                except subprocess.TimeoutExpired:
                    module.log(f"Query {query} timed out after 30 seconds")
                except Exception as e:
                    module.log(f"Error executing query {query}: {str(e)}")
    else:
        # Linux Ansible mode
        dsmc = module
        for query in queries:
            if dsmc.params.get(f'q_{query}'):
                # Special handling for different query types
                if query == 'version':
                    rc, output, _ = dsmc.run_command('query session', auto_exit=False)
                elif query == 'systeminfo':
                    rc, output, _ = dsmc.run_command('query systeminfo', auto_exit=False)
                elif query == 'options':
                    rc, output, _ = dsmc.run_command('query options', auto_exit=False)
                else:
                    rc, output, _ = dsmc.run_command(f'query {query}', auto_exit=False)
                
                if rc == 0:
                    results[f'q_{query}'] = getattr(DSMCParser, f'parse_q_{query}')(output)

    mapped_result = BAClientResponseMapper.map_to_developer_friendly(results)

    module.exit_json(changed=False, results=mapped_result)

if __name__ == '__main__':
    main()

# Made with Bob

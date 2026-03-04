
# sp_baclient_install.py
"""
Combined Ansible-module / standalone installer wrapper.

- On Linux (when run as an Ansible custom module), uses AnsibleModule and behaves as an Ansible module.
  To make Ansible use it as a module, place it in your role/playbook `library/` directory and call it by name.

- On Windows (when run with Python via win_command/win_shell), runs as a standalone script using the SimpleModule shim.
  Example: C:\Python313\python.exe C:\temp\sp_baclient_install.py --ba_client_version 8.1.26.0 --package_source C:\temp\BAclient_installer.exe --version 8.1.26.0
"""

import sys
import os
import platform
import json
import argparse
import subprocess
from typing import Tuple

# import helper class from same dir
from ..module_utils.ba_client_updated_linux_win_aix import BAClientHelper

def is_windows():
    return platform.system().lower().startswith("win")

class SimpleModule:
    """
    Minimal shim implementing the subset of AnsibleModule interface used by BAClientHelper.
    """
    def __init__(self, params: dict):
        self.params = params

    def run_command(self, cmd, use_unsafe_shell=False) -> Tuple[int, str, str]:
        # If cmd is list, run directly; else pass to shell depending on use_unsafe_shell
        if isinstance(cmd, (list, tuple)):
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
        else:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=use_unsafe_shell)
        out, err = proc.communicate()
        try:
            stdout = out.decode("utf-8", errors="ignore")
            stderr = err.decode("utf-8", errors="ignore")
        except Exception:
            stdout = str(out)
            stderr = str(err)
        return proc.returncode, stdout, stderr

    def fail_json(self, **kwargs):
        sys.stderr.write(json.dumps({"failed": True, **kwargs}) + "\n")
        sys.exit(1)

    def exit_json(self, **kwargs):
        sys.stdout.write(json.dumps({"changed": kwargs.get("changed", False), **kwargs}) + "\n")
        sys.exit(0)

    def warn(self, msg):
        sys.stderr.write(f"WARNING: {msg}\n")

    def log(self, msg):
        self.warn(msg)

def normalize_version(ver):
    try:
        return [int(x) for x in str(ver).split('.') if x != ""]
    except Exception:
        return []

def linux_main():
    # Import AnsibleModule here (won't be imported on Windows)
    from ansible.module_utils.basic import AnsibleModule

    argument_spec = dict(
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        ba_client_version=dict(type='str', required=True),
        package_source=dict(type='str', required=True),
        version=dict(type='str', required=True),
        install_path=dict(type='str', default='/opt/tivoli/tsm/client/ba/bin'),
        force=dict(type='bool', default=False),
        temp_dir=dict(type='str', default='/opt/baClient'),
        start_daemon=dict(type='bool', default=True),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    utils = BAClientHelper(module)

    state = module.params['state']
    ba_client_version = module.params['ba_client_version']
    package_source = module.params['package_source']
    desired_version = module.params['version']
    install_path = module.params['install_path']
    force = module.params['force']
    temp_dir = module.params['temp_dir']

    installed, installed_version = utils.check_installed()
    version_available = utils.file_exists(package_source)
    installed_version_list = normalize_version(installed_version) if installed_version else []
    user_version_list = normalize_version(desired_version) if desired_version else []

    if installed_version and user_version_list > installed_version_list and version_available:
        action = "upgrade"
    elif not installed_version and version_available:
        action = "install"
    else:
        action = "none"

    utils.log(f"Determined BA Client action: {action}")

    try:
        if action == 'install':
            installed, _ = utils.check_installed()
            if installed and not force:
                module.exit_json(changed=False, msg="BA Client already installed after extraction check")
            precheck = utils.verify_system_prereqs()
            if not utils.file_exists(package_source):
                module.fail_json(msg=f"Package source not found on remote host: {package_source}")
            utils.install_ba_client(package_source, install_path, temp_dir)
            verify_result = utils.post_installation_verification(ba_client_version, action)
            module.exit_json(changed=True, msg=f"BA Client {verify_result['ba_client_version']} verification completed", **verify_result)

        elif action == 'upgrade':
            upgrade_result = utils.upgrade_ba_client(package_source, desired_version, install_path, ba_client_version, state, temp_dir)
            module.exit_json(**upgrade_result)

        elif state == 'absent':
            if not installed:
                module.exit_json(changed=False, msg="BA Client not installed, nothing to remove")
            uninstalled = utils.uninstall_ba_client()
            if uninstalled:
                module.exit_json(changed=True, msg="BA Client successfully uninstalled")
            else:
                module.exit_json(changed=False, msg="BA Client was not installed, nothing to uninstall")

        module.exit_json(changed=False, msg="No action taken: BA Client is already at the desired state or no package available")
    except Exception as e:
        module.fail_json(msg=f"Unhandled exception: {str(e)}")

def windows_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--state', default='present', choices=['present', 'absent'])
    parser.add_argument('--ba_client_version', required=True)
    parser.add_argument('--package_source', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--install_path', default=r'C:\Program Files\IBM\BAClient')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--temp_dir', default=r'C:\temp\baClient')
    parser.add_argument('--start_daemon', action='store_true', default=True)

    args = parser.parse_args()
    params = vars(args)

    module = SimpleModule(params)
    utils = BAClientHelper(module)

    state = params['state']
    ba_client_version = params['ba_client_version']
    package_source = params['package_source']
    desired_version = params['version']
    install_path = params['install_path']
    force = params['force']
    temp_dir = params['temp_dir']

    installed, installed_version = utils.check_installed()
    version_available = utils.file_exists(package_source)
    installed_version_list = normalize_version(installed_version) if installed_version else []
    user_version_list = normalize_version(desired_version) if desired_version else []

    if installed_version and user_version_list > installed_version_list and version_available:
        action = "upgrade"
    elif not installed_version and version_available:
        action = "install"
    else:
        action = "none"

    utils.log(f"Determined BA Client action: {action}")

    try:
        if action == 'install':
            installed, _ = utils.check_installed()
            if installed and not force:
                module.exit_json(changed=False, msg="BA Client already installed after extraction check")
            precheck = utils.verify_system_prereqs()
            if not utils.file_exists(package_source):
                module.fail_json(msg=f"Package source not found on remote host: {package_source}")
            utils.install_ba_client(package_source, install_path, temp_dir)
            verify_result = utils.post_installation_verification(ba_client_version, action)
            module.exit_json(changed=True, msg=f"BA Client {verify_result['ba_client_version']} verification completed", **verify_result)

        elif action == 'upgrade':
            upgrade_result = utils.upgrade_ba_client(package_source, desired_version, install_path, ba_client_version, state, temp_dir)
            module.exit_json(**upgrade_result)

        elif state == 'absent':
            if not installed:
                module.exit_json(changed=False, msg="BA Client not installed, nothing to remove")
            uninstalled = utils.uninstall_ba_client()
            if uninstalled:
                module.exit_json(changed=True, msg="BA Client successfully uninstalled")
            else:
                module.exit_json(changed=False, msg="BA Client was not installed, nothing to uninstall")

        module.exit_json(changed=False, msg="No action taken: BA Client is already at the desired state or no package available")
    except Exception as e:
        module.fail_json(msg=f"Unhandled exception: {str(e)}")

if __name__ == '__main__':
    if is_windows():
        windows_main()
    else:
        linux_main()

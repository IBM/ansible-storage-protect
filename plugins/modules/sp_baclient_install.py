#!/usr/bin/python3
import sys
import json
import platform
import subprocess

# Try to import the real Ansible module (Linux / normal use)
HAS_ANSIBLE = False
try:
    from ansible.module_utils.basic import AnsibleModule
    HAS_ANSIBLE = True
except Exception:
    # On Windows (or no-ansible environment) we'll fall back to a shim
    AnsibleModule = None

# Try to import your existing helper. On Windows you may have to adjust the import path.
try:
    from ..module_utils.ba_client_utils import BAClientHelper
except Exception:
    # If this import style doesn't work on Windows, you can change it to an absolute import
    # or put the helper beside this script and do: from ba_client_utils import BAClientHelper
    # For now we'll re-raise because your actual helper is project-specific.
    raise

DOCUMENTATION = '''
---
Module Name: ibm.storage_protect.sp_baclient_install
Author: Shalu Mishra

Short Description:
  Install, upgrade or remove the IBM Storage Protect Backup-Archive (BA) Client on Linux and Windows hosts.

Description:
  This module provides idempotent management of the BA Client software on target hosts.
  It supports the following high-level operations:
    - state=present: install the BA Client if not installed or if version mismatch or force is specified.
    - state=upgrade: upgrade an existing BA Client installation to a specific version.
    - state=absent: uninstall the BA Client and clean up associated components.

  For Linux hosts, the module uses package operations (tar extraction / rpm install) and checks existing installations via rpm.
  For Windows hosts, the module uses registry and Win32_Product queries for detection and silent installer/uninstaller logic.

Options:
  package_source:
    type: str
    required: false
    description:
      Path to the BA Client installation package (e.g., tar on Linux, .exe/.msi on Windows).

  install_path:
    type: str
    required: false
    default (Linux): /opt/tivoli/tsm/client/ba/bin
    default (Windows): C:\Program Files\IBM\TSM\baclient
    description:
      Target installation directory of BA Client binaries.

  version:
    type: str
    required: false
    description:
      Desired version of BA Client. Required for upgrade operations.

  force:
    type: bool
    required: false
    default: false
    description:
      If true, forces reinstallation even if the desired version is already present.

  start_daemon:
    type: bool
    required: false
    default: true
    description:
      Whether to start the BA Client daemon/service after installation.

Returns:
  changed (bool): whether any change was made.
  msg (str): human-readable message summarizing the operation.
  version (str): the installed BA Client version (if applicable).

Notes:
  * The execution must be run with sufficient privileges (root on Linux, Administrator on Windows).
  * On Windows, if Python interpreter required, use ansible_python_interpreter inventory variable.
  * Ensure disk space and architecture compatibility are met. The module performs pre-checks and will fail if conditions are not satisfied.
'''

EXAMPLES = '''
  - name: Install or upgrade BA Client on Linux
      sp_baclient_install:
        ba_client_version: "{{ ba_client_version }}"
        state: absent
        package_source: "{{ linux_package_source }}"
        install_path: '/opt/tivoli/tsm/client/ba/bin'
      when: ansible_os_family != "Windows"

  - name: Execute Python module on Windows
      win_command: >
        python C:\temp\sp_baclient_install.py
        --state absent
        --ba-client-version {{ ba_client_version }}
        --package-source {{ windows_package_source }}
        --version {{ ba_client_version }}
        --install-path "C:\Program Files\Tivoli\tsm\client\ba\bin"
        --temp-dir C:\temp\baClient
      when: ansible_os_family == "Windows"
'''

def build_windows_like_module():
    """
    Create a minimal Ansible-like module for Windows / no-ansible environments.
    - reads CLI args
    - exposes .params
    - exposes .exit_json() / .fail_json()
    - exposes .log()
    """
    import argparse

    parser = argparse.ArgumentParser(description="BA Client install/upgrade/uninstall (no-ansible mode)")

    parser.add_argument("--state", choices=["present", "absent"], default="present")
    parser.add_argument("--ba-client-version", dest="ba_client_version", required=True)
    parser.add_argument("--package-source", dest="package_source", required=True)
    parser.add_argument("--version", dest="version", required=True)
    parser.add_argument("--install-path", dest="install_path", default="/opt/tivoli/tsm/client/ba/bin")
    parser.add_argument("--force", dest="force", action="store_true", default=False)
    parser.add_argument("--temp-dir", dest="temp_dir", default="/opt/baClient")
    parser.add_argument("--start-daemon", dest="start_daemon", action="store_true", default=True)

    args = parser.parse_args()

    # We make an object that looks just enough like AnsibleModule for the rest of the code.
    class WinModuleShim:
        def __init__(self, args_ns):
            # mimic .params from ansible
            self.params = {
                "state": args_ns.state,
                "ba_client_version": args_ns.ba_client_version,
                "package_source": args_ns.package_source,
                "version": args_ns.version,
                "install_path": args_ns.install_path,
                "force": args_ns.force,
                "temp_dir": args_ns.temp_dir,
                "start_daemon": args_ns.start_daemon,
            }

        def exit_json(self, **kwargs):
            # print JSON and exit 0 — similar to Ansible
            print(json.dumps(kwargs, indent=2))
            sys.exit(0)

        def run_command(self, cmd, use_unsafe_shell=False, check_rc=True):
            """
            Run a system command cross-platform (Windows/Linux).
            Returns: (rc, stdout, stderr)
            """
            try:
                result = subprocess.run(
                    cmd,
                    shell=use_unsafe_shell,
                    capture_output=True,
                    text=True
                )
                rc = result.returncode
                out = result.stdout.strip()
                err = result.stderr.strip()

                if check_rc and rc != 0:
                    print(f"[ERROR] Command failed (rc={rc}): {cmd}\n{err}")

                return rc, out, err

            except Exception as e:
                print(f"[EXCEPTION] Failed to run command: {cmd}\nError: {e}")
                return 1, "", str(e)
            
        def run_cmd(self, cmd, use_unsafe_shell=False, check_rc=True):
            """
            Wrapper for run_command() — same params, same behavior.
            Keeps compatibility with existing Ansible-style utils.
            """
            return self.run_command(cmd, use_unsafe_shell=use_unsafe_shell, check_rc=check_rc)

        def fail_json(self, **kwargs):
            # print JSON and exit non-zero
            kwargs.setdefault("failed", True)
            print(json.dumps(kwargs, indent=2), file=sys.stderr)
            sys.exit(1)

        def log(self, msg):
            # basic log to stderr
            print(f"[ba_client] {msg}", file=sys.stderr)

    return WinModuleShim(args)


def get_module():
    """
    Return an object that has the Ansible-like interface.
    - on Linux/Ansible: real AnsibleModule
    - on Windows/no-ansible: our shim
    """
    if HAS_ANSIBLE and platform.system().lower() != "windows":
        # Original behavior
        argument_spec = dict(
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            ba_client_version=dict(type='str', required=True),
            package_source=dict(type='str', required=True),
            install_path=dict(type='str', default='/opt/tivoli/tsm/client/ba/bin'),
            force=dict(type='bool', default=False),
            temp_dir=dict(type='str', default='/opt/baClient'),
            start_daemon=dict(type='bool', default=True),
        )
        return AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    else:
        # Windows / no ansible
        return build_windows_like_module()


def normalize_version(ver):
    try:
        return [int(x) for x in ver.split('.')]
    except Exception:
        return []


def main():
    module = get_module()
    utils = BAClientHelper(module)

    state = module.params['state']
    ba_client_version = module.params['ba_client_version']
    package_source = module.params['package_source']
    install_path = module.params['install_path']
    force = module.params['force']
    temp_dir = module.params['temp_dir']
    ba_client_start_daemon = module.params.get("start_daemon", True)

    # 1. Check what is installed and what we have
    installed, installed_version = utils.check_installed()
    version_available = utils.file_exists(package_source)

    installed_version_list = normalize_version(installed_version) if installed_version else []
    user_version_list = normalize_version(ba_client_version) if ba_client_version else []

    # 2. Determine action
    if installed_version and user_version_list > installed_version_list and version_available:
        utils.log(f"Upgrade needed: current={installed_version}, desired={ba_client_version}")
        action = "upgrade"
    elif not installed_version and version_available:
        action = "install"
    else:
        action = "none"

    utils.log(f"Determined BA Client action: {action}")

    # 3. Action branches
    if action == 'install':
        # Idempotency recheck
        installed, _ = utils.check_installed()
        if installed and not force:
            if not HAS_ANSIBLE:
                print("BA Client already installed after extraction check")
            else:
                module.exit_json(changed=False, msg="BA Client already installed after extraction check")

        # Pre-checks
        precheck = utils.verify_system_prereqs()
        module.log(f"Precheck completed: {precheck}")

        # Check package
        if not utils.file_exists(package_source):
            module.fail_json(msg=f"Package source not found on host: {package_source}")

        try:
            # Perform install
            utils.install_ba_client(package_source, install_path, temp_dir)

            utils.configure_ba_client()

            # Verify
            verify_result = utils.post_installation_verification(ba_client_version, action)

            # NOTE: If your helper can start service/daemon on Windows, let it handle internally.
            daemon_result = utils.start_baclient_daemon(ba_client_start_daemon)

            module.exit_json(
                changed=True,
                msg=f"BA Client {verify_result.get('ba_client_version', ba_client_version)} verification completed",
                **verify_result,
                **daemon_result
            )

        except Exception as install_error:
            module.log(f"Installation failed: {install_error}")
            rollback_info = utils.rollback(action="install")
            module.exit_json(
                changed=False,
                msg=f"Installation failed and rollback executed: {install_error}. {rollback_info['status']}"
            )

    elif action == 'upgrade':
        try:
            upgrade_result = utils.upgrade_ba_client(
                package_source,
                install_path,
                ba_client_version,
                state,
                temp_dir
            )
            module.exit_json(**upgrade_result)
        except Exception as upgrade_error:
            module.log(f"Upgrade failed: {upgrade_error}")
            utils.rollback(action="upgrade")  # <-- ROLLBACK upgrade
            module.exit_json(changed=False, msg=f"Upgrade failed and rollback executed: {upgrade_error}")

    elif state == 'absent':
        if not installed:
            module.exit_json(changed=False, msg="BA Client not installed, nothing to remove")
        
        try:
            uninstalled = utils.uninstall_ba_client()
            if uninstalled:
                module.exit_json(changed=True, msg="BA Client successfully uninstalled")
            else:
                module.exit_json(changed=False, msg="BA Client was not installed, nothing to uninstall")
        except Exception as uninstall_error:
            module.log(f"Uninstallation failed: {uninstall_error}")
            utils.rollback(action="uninstall")  # <-- ROLLBACK uninstall
            module.exit_json(
                changed=False,
                msg=f"Uninstallation failed and rollback executed: {uninstall_error}"
            )

    # fallback
    module.exit_json(
        changed=False,
        msg="No action taken: BA Client is already at the desired state or no package available"
    )

if __name__ == '__main__':
    main()
#!/usr/bin/python
# coding: utf-8 -*-


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.command_executor import CommandExecutor
from ansible.module_utils.install_ba_client_utils import CompatibilityChecker, SystemInfoCollector, extract_tar, install_rpm_packages_in_sequence, parse_dsm_output
import os

# Module Documentation
DOCUMENTATION = '''
---
module: install_ba_client
author: "Sarthak Kshirsagar"
short_description: Install IBM Storage Protect BA Client on remote machines
description:
    - This Ansible module automates the installation of IBM Storage Protect BA Client on remote Linux machines. It performs system compatibility checks, extracts the provided BA client `.tar` folder, installs RPM packages, and executes the `dsmc` command to ensure the installation is successful.
    - The module ensures that the system meets compatibility requirements before proceeding with the installation, making it suitable for automating the deployment of IBM Storage Protect BA Client on multiple remote hosts.
options:
    install:
        description:
            - A boolean flag that controls whether the BA Client should be installed. Set to true to install the client, false to skip installation.
        required: true
        type: bool
    path:
        description:
            - The path to the BA Client `.tar` folder containing the installation files.
        required: true
        type: str
    dest_folder:
        description:
            - The path to the destination folder where the BA Client should be installed.
        required: true
        type: str
'''

EXAMPLES = '''
---
- name: Copy the module on the remote host
  ansible.builtin.synchronize:
    src: "./8.1.24.0-TIV-TSMBAC-LinuxX86.tar"
    dest: "/tmp/"
    register: copy_result
    
- name: Check the system compatibility
  install_ba_client:
    install: false
    register: compatible_check_result

- name: Install IBM Storage Protect BA Client on remote system
  install_ba_client:
    install: true
    path: /tmp/8.1.24.0-TIV-TSMBAC-LinuxX86.tar
    dest_folder: /opt/baClient
  register: result
'''

from ansible.module_utils.basic import AnsibleModule
import os


def main():
    module_args = dict(
        install=dict(type='bool', required=True),
        path=dict(type='str', required=False),
        dest_folder=dict(type='str', required=False),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)
    result = {}

    if module.params['install']:
        if not module.params['path']:
            module.fail_json(msg="The 'path' parameter is required when 'install' is set to True.")
        if not module.params['dest_folder']:
            module.fail_json(msg="The 'dest_folder' parameter is required when 'install' is set to True.")

    command_executor = CommandExecutor()
    system_info_collector = SystemInfoCollector(command_executor)
    system_info = system_info_collector.collect()
    result.update({'system_info':system_info})
    compatibility_checker = CompatibilityChecker(system_info)
    compatibility = compatibility_checker.check_compatibility()
    system_info['compatibility'] = compatibility
    result.update(system_info)
    changed = False

    if module.params['install']:
        # If system is compatible, proceed with installation
        if result["compatibility"].get('compatible', False):
            try:
                # Extract files and change to destination directory
                extract_result = extract_tar(module, module.params['path'], module.params['dest_folder'])
                os.chdir(module.params['dest_folder'])
            except Exception as e:
                module.fail_json(msg=f"Failed to extract or change directory: {str(e)}")

            # Identify and install RPM packages in sequence
            try:
                install_results = install_rpm_packages_in_sequence(module.params['dest_folder'])
                result.update({"install_results": install_results})
            except Exception as e:
                module.fail_json(msg=f"Installation failed: {str(e)}")

            dsmc_output, rc, err = CommandExecutor.execute('sudo dsmc')
            msg, changed = parse_dsm_output(dsmc_output)
            result.update({'dsmc output': msg})

        else:
            module.fail_json(msg="System compatibility check failed.", result=result)

        module.exit_json(changed=changed, result=result)
    else:
        module.exit_json(msg="No commands executed, 'install' is set to False.", result=result)


if __name__ == '__main__':
    main()


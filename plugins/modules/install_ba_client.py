from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.command_executor import CommandExecutor
from ansible.module_utils.install_ba_client_utils import CompatibilityChecker, SystemInfoCollector, extract_tar, install_rpm_packages_in_sequence, parse_dsm_output
import os

def main():
    module_args = dict(
        run_commands=dict(type='bool', required=True),
        path=dict(type='str', required=True),
        dest_folder=dict(type='str', required=True),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)
    result = {}

    if module.params['run_commands']:
        # Collecting system information and compatibility
        command_executor = CommandExecutor()
        system_info_collector = SystemInfoCollector(command_executor)
        system_info = system_info_collector.collect()
        compatibility_checker = CompatibilityChecker(system_info)
        compatibility = compatibility_checker.check_compatibility()
        system_info['compatibility'] = compatibility
        result.update(system_info)
        changed = False

        # If system is compatible, proceed with installation
        if result["compatibility"].get('compatible', False):
            try:
                # Extract files and change to destination directory
                extract_result = extract_tar(module, module.params['path'], module.params['dest_folder'])
                # result.update({"extract_result": extract_result})
                os.chdir(module.params['dest_folder'])
            except Exception as e:
                module.fail_json(msg=f"Failed to extract or change directory: {str(e)}")

            # Identify and install RPM packages in sequence
            try:
                install_results = install_rpm_packages_in_sequence(module.params['dest_folder'])
                result.update({"install_results": install_results})
            except Exception as e:
                module.fail_json(msg=f"Installation failed: {str(e)}")

            dsmcOutput, rc = CommandExecutor.execute('sudo dsmc')
            msg, changed = parse_dsm_output(dsmcOutput)
            result.update({'dsmc output':msg})


        else:
            module.fail_json(msg="System compatibility check failed.", result=result)

        module.exit_json(changed=changed,result=result)
    else:
        module.exit_json(msg="No commands executed, flag 'run_commands' is set to False.")

if __name__ == '__main__':
    main()



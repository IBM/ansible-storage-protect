from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.command_executor import CommandExecutor
from ansible.module_utils.install_ba_client_utils import CompatibilityChecker, SystemInfoCollector, extract_tar, execute_command, install_rpm_packages, run_dsmc_command
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
        # Collect system information and compatibility
        command_executor = CommandExecutor()
        system_info_collector = SystemInfoCollector(command_executor)
        system_info = system_info_collector.collect()
        compatibility_checker = CompatibilityChecker(system_info)
        compatibility = compatibility_checker.check_compatibility()
        system_info['compatibility'] = compatibility
        result.update(system_info)

        # if system is compatible install the necessary packaages and BA client
        if result["compatibility"].get('compatible', False):
            # Attempt to extract files and change to destination directory
            try:
                extract_result = extract_tar(module, module.params['path'], module.params['dest_folder'])
                result.update({"extract_result": extract_result})
                os.chdir(module.params['dest_folder'])
            except Exception as e:
                module.fail_json(msg=f"Failed to extract or change directory: {str(e)}")

            # Install RPM packages and capture the results
            install_results = install_rpm_packages()
            result.update(install_results)

            # Run the dsmc command and handle output
            dsmc_message = run_dsmc_command()
            result.update({"dsmc_message": dsmc_message})

        else:
            module.fail_json(msg="System compatibility check failed.", result=result)

        module.exit_json(result=result)
    else:
        module.exit_json(msg="No commands executed, flag 'run_commands' is set to False.")


if __name__ == '__main__':
    main()



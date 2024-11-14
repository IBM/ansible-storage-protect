
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.command_executor import CommandExecutor
from ansible.module_utils.install_ba_client_utils import CompatibilityChecker, SystemInfoCollector


def main():
    module_args = dict(
        run_commands=dict(type='bool', required=True),
    )
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=False)
    result = {}

    if module.params['run_commands']:
        command_executor = CommandExecutor()
        system_info_collector = SystemInfoCollector(command_executor)
        system_info = system_info_collector.collect()
        compatibility_checker = CompatibilityChecker(system_info)
        compatibility = compatibility_checker.check_compatibility()
        system_info['compatibility'] = compatibility
        result.update(system_info)
        module.exit_json(result=result)
    else:
        module.exit_json(msg="No commands executed, flag 'run_commands' is set to False.")


if __name__ == '__main__':
    main()
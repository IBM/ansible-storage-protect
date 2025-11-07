from ansible.module_utils.basic import AnsibleModule
from ..module_utils.ba_client_utils import BAClientHelper


def main():
    argument_spec = dict(
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        ba_client_version=dict(type='str', required=True),
        package_source=dict(type='str', required=True),
        version=dict(type='str', required=True),
        install_path=dict(type='str', default='/opt/tivoli/tsm/client/ba/bin'),
        force=dict(type='bool', default=False),
        temp_dir=dict(type='str', default='/opt/baClient'),
        # target_host=dict(type='str', required=False),
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
    ba_client_start_daemon = module.params.get("start_daemon", True)
    # target_host = module.params['target_host']

    # Check if BA Client is already installed
    installed, installed_version = utils.check_installed()
    version_available = utils.file_exists(package_source)

    # Normalize versions to compare
    def normalize(ver):
        try:
            return [int(x) for x in ver.split('.')]
        except Exception:
            return []

    installed_version_list = normalize(installed_version) if installed_version else []
    user_version_list = normalize(desired_version) if desired_version else []
    
    # Step 2. Determine the action dynamically
    if installed_version and user_version_list > installed_version_list and version_available:
        utils.log(f"Upgrade needed: current={installed_version}, desired={desired_version}")
        action = "upgrade"
    elif not installed_version and version_available:
        action = "install"
    else:
        action = "none"

    utils.log(f"Determined BA Client action: {action}")

    if action == 'install':

        # Idempotency recheck
        installed, _ = utils.check_installed()
        if installed and not force:
            module.exit_json(changed=False, msg="BA Client already installed after extraction check")

        # Pre-checks
        precheck = utils.verify_system_prereqs()
        module.log(f"Precheck completed: {precheck}")

        # Check if package exists
        if not utils.file_exists(package_source):
            module.fail_json(msg=f"Package source not found on remote host: {package_source}")

        # Perform installation
        utils.install_ba_client(package_source, install_path, temp_dir)

        # Post-check validation
        verify_result = utils.post_installation_verification(ba_client_version, action)
        
        # Start daemon/service
        # daemon_result = utils.start_baclient_daemon(ba_client_start_daemon)

        utils.module.exit_json(
            changed=True,
            msg=f"BA Client {verify_result['ba_client_version']} verification and daemon steps completed",
            **verify_result,
            # **daemon_result
        )

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

    module.exit_json(
        changed=False,
        msg="No action taken: BA Client is already at the desired state or no package available"
    )

if __name__ == '__main__':
    main()

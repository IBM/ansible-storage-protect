from ansible.module_utils.dsmadmc_adapter import DsmadmcAdapter
from ansible.module_utils.sp_server_facts import DSMParser,SpServerResponseMapper

def main():
    argument_spec = dict(
        server_name=dict(type='str', required=False),
        username=dict(type='str', required=False),
        password=dict(type='str', required=False),
        q_status=dict(type='bool', default=False),
        q_monitorsettings=dict(type='bool', default=False),
        q_db=dict(type='bool', default=False),
        q_dbspace=dict(type='bool', default=False),
        q_log=dict(type='bool', default=False),
        q_domain=dict(type='bool', default=False),
        q_copygroup=dict(type='bool', default=False),
        q_replrule=dict(type='bool', default=False),
        q_devclass=dict(type='bool', default=False),
        q_mgmtclass=dict(type='bool', default=False),
        q_stgpool=dict(type='bool', default=False)
    )

    dsmadmc = DsmadmcAdapter(argument_spec=argument_spec)
    results = {}

    if dsmadmc.params.get('q_status'):
        rc, output, _ = dsmadmc.run_command('q status', auto_exit=False)
        if rc == 0:
            results['q_status'] = DSMParser.parse_q_status(output)

    if dsmadmc.params.get('q_monitorsettings'):
        rc, output, _ = dsmadmc.run_command('q monitorsettings', auto_exit=False)
        if rc == 0:
            results['q_monitorsettings'] = DSMParser.parse_q_monitorsettings(output)

    if dsmadmc.params.get('q_db'):
        rc, output, _ = dsmadmc.run_command('q db', auto_exit=False)
        if rc == 0:
            results['q_db'] = DSMParser.parse_database_info(output)

    if dsmadmc.params.get('q_dbspace'):
        rc, output, _ = dsmadmc.run_command('q dbspace', auto_exit=False)
        if rc == 0:
            results['q_dbspace'] = DSMParser.parse_space_info(output)

    if dsmadmc.params.get('q_log'):
        rc, output, _ = dsmadmc.run_command('q log', auto_exit=False)
        if rc == 0:
            results['q_log'] = DSMParser.parse_space_info(output)

    if dsmadmc.params.get('q_domain'):
        rc, output, _ = dsmadmc.run_command('q domain', auto_exit=False)
        if rc == 0:
            results['q_domain'] = DSMParser.parse_policy_info(output)

    if dsmadmc.params.get('q_copygroup'):
        rc, output, _ = dsmadmc.run_command('q copygroup', auto_exit=False)
        if rc == 0:
            results['q_copygroup'] = DSMParser.parse_policy_settings(output)

    if dsmadmc.params.get('q_replrule'):
        rc, output, _ = dsmadmc.run_command('q replrule', auto_exit=False)
        if rc == 0:
            results['q_replrule'] = DSMParser.parse_replication_rules(output)

    if dsmadmc.params.get('q_devclass'):
        rc, output, _ = dsmadmc.run_command('q devclass', auto_exit=False)
        if rc == 0:
            results['q_devclass'] = DSMParser.parse_device_class(output)

    if dsmadmc.params.get('q_mgmtclass'):
        rc, output, _ = dsmadmc.run_command('q mgmtclass', auto_exit=False)
        if rc == 0:
            results['q_mgmtclass'] = DSMParser.parse_policy_management_class(output)

    if dsmadmc.params.get('q_stgpool'):
        rc, output, _ = dsmadmc.run_command('q stgpool', auto_exit=False)
        if rc == 0:
            results['q_stgpool'] = DSMParser.parse_storage_pool(output)

    mapped_result = SpServerResponseMapper.map_to_developer_friendly(results)

    dsmadmc.exit_json(changed=False, results=mapped_result)


if __name__ == '__main__':
    main()

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule, env_fallback
import subprocess


class StorageProtectModule(AnsibleModule):
    url = None
    AUTH_ARGSPEC = dict(
        server_name=dict(required=False, fallback=(env_fallback, ['STORAGE_PROTECT_SERVERNAME'])),
        username=dict(required=False, fallback=(env_fallback, ['STORAGE_PROTECT_USERNAME'])),
        password=dict(no_log=True, required=False, fallback=(env_fallback, ['STORAGE_PROTECT_PASSWORD'])),
        request_timeout=dict(type='float', required=False, fallback=(env_fallback, ['STORAGE_PROTECT_REQUEST_TIMEOUT'])),
    )
    server_name = 'local'
    username = None
    password = None
    validate_certs = True
    request_timeout = 10
    authenticated = False
    version_checked = False
    error_callback = None
    warn_callback = None

    def __init__(self, argument_spec=None, direct_params=None, error_callback=None, warn_callback=None, **kwargs):
        full_argspec = {}
        full_argspec.update(StorageProtectModule.AUTH_ARGSPEC)
        full_argspec.update(argument_spec)
        kwargs['supports_check_mode'] = True

        self.error_callback = error_callback
        self.warn_callback = warn_callback

        self.json_output = {'changed': False}

        if direct_params is not None:
            self.params = direct_params
        else:
            super().__init__(argument_spec=full_argspec, **kwargs)

        for param, _ in list(StorageProtectModule.AUTH_ARGSPEC.items()):
            setattr(self, param, self.params.get(param))

    def run_command(self, command, auto_exit=True, dataonly=True, exit_on_fail=True):
        command = f'dsmadmc -servername={self.server_name} -id={self.username} -pass={self.password} ' + ('-dataonly=yes ' if dataonly else '') + command
        self.json_output['command'] = command
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if auto_exit and result.returncode == 10:
                self.json_output['changed'] = False
                self.exit_json(**self.json_output)
            if auto_exit and result.returncode == 0:
                self.json_output['changed'] = True
                self.json_output['output'] = result.stdout.decode('utf-8')
                self.exit_json(**self.json_output)
            return result.returncode, result.stdout.decode('utf-8'), None
        except subprocess.CalledProcessError as e:
            if auto_exit and e.returncode == 10:
                self.json_output['changed'] = False
                self.exit_json(**self.json_output)
            if exit_on_fail and e.returncode != 10:
                self.fail_json(msg=e.stdout.decode('utf-8'), rc=e.returncode, **self.json_output)
            return e.returncode, e.stdout.decode('utf-8'), e

    def find_one(self, object_type, name, fail_on_not_found=False):
        command = f"-comma q {object_type} {name} format=detailed"
        rc, out, _ = self.run_command(command, auto_exit=False, exit_on_fail=False)
        exists = rc == 0
        self.json_output['exists'] = exists
        if fail_on_not_found and not exists:
            self.fail_json(msg=f'Could not find {object_type} with name {name}')
        return rc == 0, out

    def perform_action(self, action, object_type, object_identifier, options='', exists=False, existing=None, auto_exit=True):
        if not exists and action in ['remove', 'delete']:
            if auto_exit:
                self.exit_json(**self.json_output)
            return 0
        command = f"{action} {object_type} {object_identifier} {options}"
        rc, output, error = self.run_command(command, auto_exit=False)
        if exists or rc == 10:
            # Check if idempotent
            _, new_object = self.find_one(object_type, object_identifier)
            self.json_output['changed'] = self.json_output['changed'] or existing and existing != new_object or exists and action in ['remove', 'delete']
            if auto_exit:
                self.exit_json(**self.json_output)
            return rc
        self.json_output['changed'] = True
        if auto_exit:
            self.exit_json(**self.json_output)
        return rc

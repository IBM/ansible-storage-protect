from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule, env_fallback
import subprocess


class DsmcAdapter(AnsibleModule):
    url = None
    AUTH_ARGSPEC = dict(
        server_name=dict(required=False, fallback=(env_fallback, ['STORAGE_PROTECT_SERVERNAME'])),
        node_name=dict(required=False, fallback=(env_fallback, ['STORAGE_PROTECT_NODENAME'])),
        password=dict(no_log=True, required=False, fallback=(env_fallback, ['STORAGE_PROTECT_NODE_PASSWORD'])),
        request_timeout=dict(type='float', required=False, fallback=(env_fallback, ['STORAGE_PROTECT_REQUEST_TIMEOUT'])),
    )
    server_name = 'local'
    password = None
    validate_certs = True
    request_timeout = 10
    authenticated = False
    version_checked = False
    error_callback = None
    warn_callback = None

    def __init__(self, argument_spec=None, direct_params=None, error_callback=None, warn_callback=None, **kwargs):
        full_argspec = {}
        full_argspec.update(DsmcAdapter.AUTH_ARGSPEC)
        full_argspec.update(argument_spec)
        kwargs['supports_check_mode'] = True

        self.error_callback = error_callback
        self.warn_callback = warn_callback

        self.json_output = {'changed': False}

        if direct_params is not None:
            self.params = direct_params
        else:
            super().__init__(argument_spec=full_argspec, **kwargs)

        for param, _ in list(DsmcAdapter.AUTH_ARGSPEC.items()):
            setattr(self, param, self.params.get(param))

    def run_command(self, command):
        command = f'dsmc {command} -se={self.server_name} -virtualnode={self.node_name} -pass={self.password} '
        self.json_output['command'] = command
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.json_output['changed'] = True
            self.json_output['output'] = result.stdout.decode('utf-8')
            self.exit_json(**self.json_output)
            return result.returncode, result.stdout.decode('utf-8'), None
        except subprocess.CalledProcessError as e:
            self.json_output['changed'] = False
            self.fail_json(msg=e.stdout.decode('utf-8') + e.stderr.decode('utf-8'), rc=e.returncode, **self.json_output)
            return e.returncode, e.stdout.decode('utf-8'), e

    def perform_action(self, action, object, options=''):
        command = f"{action} {object} {options}"
        rc, output, error = self.run_command(command)
        if rc == 0:
            self.json_output['changed'] = True
        self.exit_json(**self.json_output)
        return rc, output, error

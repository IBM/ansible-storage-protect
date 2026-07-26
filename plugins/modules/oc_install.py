#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule, env_fallback

from ..module_utils.oc_install_utils import (
    DEFAULT_INSTALL_DEST,
    GSAAccessError,
    OCInstallManager,
    detect_platform,
    get_installed_version,
    validate_ssl_password,
)

DOCUMENTATION = r'''
---
module: oc_install
author:
  - Shalu Mishra
short_description: Install IBM Storage Protect Operations Center across platforms
description:
  - Detects the target platform (Linux, RHEL-family, AIX, or Windows).
  - Downloads the appropriate Operations Center (OC) installer from a GSA artifact location.
  - Extracts the installer payload and performs a silent Installation Manager install.
  - Optionally applies basic OC configuration (admin session security via C(dsmadmc)).
  - Validates installation using IMCL package detection and a best-effort service check.
  - The module is idempotent: if the required OC package version is already installed, install is skipped.
options:
  state:
    description:
      - Desired lifecycle state for Operations Center.
      - C(absent) is reserved for future use and currently fails.
    type: str
    choices:
      - present
      - upgrade
      - absent
    default: present
  oc_version:
    description:
      - Target Operations Center version to install or upgrade to.
      - Used to select the matching artifact from GSA or a local staging directory.
    type: str
    required: false
  gsa_base_url:
    description:
      - Base HTTP URL of the GSA / central artifact repository for NextGenUI installers.
      - If not set, defaults to the IBM TUC GSA NextGenUI path for 8.2.2.000.
    type: str
  gsa_username:
    description:
      - Username for HTTP Basic authentication to the GSA artifact repository.
      - Can also be supplied via the OC_GSA_USERNAME environment variable.
    type: str
    required: false
  gsa_password:
    description:
      - Password for HTTP Basic authentication to the GSA artifact repository.
      - Can also be supplied via the OC_GSA_PASSWORD environment variable.
    type: str
    required: false
  gsa_validate_certs:
    description:
      - Whether to validate the TLS certificate when C(gsa_base_url) uses HTTPS.
      - Set to C(false) on hosts without the IBM/internal CA bundle (common on AIX).
      - Can also be supplied via the OC_GSA_VALIDATE_CERTS environment variable.
    type: bool
    default: true
  artifact_path:
    description:
      - Optional local path to a pre-staged installer binary on the target host.
      - When provided, GSA download is skipped.
    type: str
    required: false
  oc_install_dest:
    description:
      - Working directory on the target host for downloaded and extracted installer files.
      - Defaults to C(/opt/oc_binary) on Linux and C(/tmp/oc_binary) on AIX.
    type: str
    default: "/opt/oc_binary"
  install_location_tsm:
    description:
      - Target IBM Storage Protect installation directory passed to Installation Manager.
      - Defaults to C(/opt/tivoli/tsm) on Linux and C(/usr/tivoli/tsm) on AIX.
    type: str
    default: "/opt/tivoli/tsm"
  install_location_im:
    description:
      - IBM Installation Manager root directory on the target host.
      - On AIX, probes C(/usr/IBM/InstallationManager) then C(/opt/IBM/InstallationManager).
    type: str
    default: "/opt/IBM/InstallationManager"
  profile_id:
    description:
      - Installation Manager package group profile for Operations Center.
      - Must match the profile used by an existing SP Server install at the same path
        (typically C(IBM Storage Protect) on SP 8.2 hosts).
    type: str
    default: "IBM Storage Protect"
  secure_port:
    description:
      - HTTPS port for Operations Center.
    type: str
    default: "9443"
  ssl_password:
    description:
      - SSL password for the Operations Center HTTPS endpoint.
      - Can also be supplied via the OC_SSL_PASSWORD environment variable.
    type: str
    required: false
  configure:
    description:
      - Whether to run basic post-install configuration after a successful install.
    type: bool
    default: true
  admin_name:
    description:
      - Hub server admin user for OC session security configuration.
      - Required when C(configure=true).
    type: str
    required: false
  force:
    description:
      - Force reinstall even when the requested version is already installed.
    type: bool
    default: false
  download_timeout:
    description:
      - HTTP timeout in seconds for GSA artifact download and directory listing.
    type: int
    default: 120
  log_level:
    description:
      - Internal orchestration log level.
    type: str
    default: "INFO"
extends_documentation_fragment:
  - ibm.storage_protect.auth
'''

EXAMPLES = r'''
- name: Install Operations Center from GSA on Linux
  ibm.storage_protect.oc_install:
    oc_version: "8.2.1.000"
    gsa_username: "{{ gsa_username }}"
    gsa_password: "{{ gsa_password }}"
    ssl_password: "{{ vault_oc_ssl_password }}"
    admin_name: tsmuser1
    gsa_base_url: ""
  environment:
    STORAGE_PROTECT_SERVERNAME: "{{ sp_server_name }}"
    STORAGE_PROTECT_USERNAME: "{{ sp_admin_user }}"
    STORAGE_PROTECT_PASSWORD: "{{ sp_admin_password }}"

- name: Install Operations Center from a pre-staged binary on Windows
  ibm.storage_protect.oc_install:
    artifact_path: "C:\\temp\\8.2.2.000-IBM-NextGenUI-WindowsX64.exe"
    ssl_password: "{{ vault_oc_ssl_password }}"
    configure: false

- name: Install Operations Center on AIX from GSA
  ibm.storage_protect.oc_install:
    oc_version: "8.2.2.000"
    gsa_base_url: ""
    gsa_username: "{{ gsa_username }}"
    gsa_password: "{{ gsa_password }}"
    ssl_password: "{{ vault_oc_ssl_password }}"
    install_location_tsm: "/usr/tivoli/tsm"
    install_location_im: "/usr/IBM/InstallationManager"
    oc_install_dest: "/tmp/oc_binary"
    profile_id: "IBM Storage Protect"
    configure: false

'''

RETURN = r'''
platform:
  description: Detected platform key (linux, rhel, aix, windows).
  type: str
  returned: always
msg:
  description: Human-readable install or skip status message.
  type: str
  returned: always
success:
  description: True when Operations Center is installed at the required version.
  type: bool
  returned: on success
installed_version:
  description: Installed Operations Center package version reported by IMCL.
  type: str
  returned: on success
oc_url:
  description: HTTPS URL path for the Operations Center web UI (replace host with target hostname).
  type: str
  returned: when installation succeeds
validation:
  description: Post-install validation details.
  type: dict
  returned: on success
'''


def main():
    argument_spec = dict(
        state=dict(type='str', default='present', choices=['present', 'upgrade', 'absent']),
        oc_version=dict(type='str', required=False),
        gsa_base_url=dict(type='str', required=False),
        gsa_username=dict(
            type='str',
            required=False,
            fallback=(env_fallback, ['OC_GSA_USERNAME']),
        ),
        gsa_password=dict(
            type='str',
            required=False,
            no_log=True,
            fallback=(env_fallback, ['OC_GSA_PASSWORD']),
        ),
        gsa_validate_certs=dict(
            type='bool',
            default=True,
            fallback=(env_fallback, ['OC_GSA_VALIDATE_CERTS']),
        ),
        artifact_path=dict(type='str', required=False),
        oc_install_dest=dict(type='str', default=DEFAULT_INSTALL_DEST),
        install_location_tsm=dict(type='str', default='/opt/tivoli/tsm'),
        install_location_im=dict(type='str', default='/opt/IBM/InstallationManager'),
        profile_id=dict(type='str', default='IBM Storage Protect'),
        secure_port=dict(type='str', default='9443'),
        ssl_password=dict(
            type='str',
            required=False,
            no_log=True,
            fallback=(env_fallback, ['OC_SSL_PASSWORD']),
        ),
        configure=dict(type='bool', default=True),
        admin_name=dict(type='str', required=False),
        force=dict(type='bool', default=False),
        download_timeout=dict(type='int', default=120),
        log_level=dict(type='str', default='INFO'),
        server_name=dict(required=False, fallback=(env_fallback, ['STORAGE_PROTECT_SERVERNAME'])),
        username=dict(required=False, fallback=(env_fallback, ['STORAGE_PROTECT_USERNAME'])),
        password=dict(no_log=True, required=False, fallback=(env_fallback, ['STORAGE_PROTECT_PASSWORD'])),
        request_timeout=dict(type='float', required=False, fallback=(env_fallback, ['STORAGE_PROTECT_REQUEST_TIMEOUT'])),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ('configure', True, ('admin_name',)),
        ],
    )

    if module.params['state'] in ('present', 'upgrade'):
        ssl_error = validate_ssl_password(module.params.get('ssl_password'))
        if ssl_error:
            module.fail_json(msg=ssl_error)

    if module.check_mode:
        manager = OCInstallManager(module)
        oskey = detect_platform(manager.context)
        installed_version = get_installed_version(manager.context, oskey)
        module.exit_json(
            changed=installed_version is None,
            platform=oskey,
            installed_version=installed_version,
            msg="check mode: no changes applied",
        )

    try:
        result = OCInstallManager(module).run()
    except GSAAccessError as exc:
        hint = (
            "Set gsa_username/gsa_password (or OC_GSA_USERNAME/OC_GSA_PASSWORD), "
            "set gsa_validate_certs=false for HTTPS certificate issues on AIX, "
            "use an http:// GSA URL, or stage the installer locally with artifact_path."
        )
        module.fail_json(
            msg=str(exc),
            gsa_base_url=module.params.get('gsa_base_url'),
            gsa_validate_certs=module.params.get('gsa_validate_certs'),
            hint=hint,
        )
    module.exit_json(**result)


if __name__ == '__main__':
    main()

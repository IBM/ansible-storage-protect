# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Tom page <tpage@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


class ModuleDocFragment(object):

    # IBM Storage Protect documentation fragment
    DOCUMENTATION = r'''
options:
  server_name:
    description:
    - SERVERNAME your IBM Storage Protect instance as specified in the dsm.sys.
    - If value not set, will try environment variable C(STORAGE_PROTECT_SERVERNAME)
    - If value not specified by any means, the value of C(local) will be used
    type: str
  username:
    description:
    - Username for your IBM Storage Protect instance.
    - If value not set, will try environment variable C(STORAGE_PROTECT_USERNAME)
    type: str
  password:
    description:
    - Password for your IBM Storage Protect instance.
    - If value not set, will try environment variable C(STORAGE_PROTECT_PASSWORD)
    type: str
  request_timeout:
    description:
    - Specify the timeout Ansible should use in requests to the IBM Storage Protect host.
    - Defaults to 10s, but this is handled by the shared module_utils code
    - If value not set, will try environment variable C(STORAGE_PROTECT_REQUEST_TIMEOUT)
    type: float
'''

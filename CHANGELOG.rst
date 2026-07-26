============================================
ibm.storage_protect Release Notes
============================================

.. contents:: Topics



v1.1.0
======

Major Changes
-------------

- Added PPC64LE (IBM Power Architecture) support to SP Server orchestration playbooks
- Added PLAY 3 in playbooks/sp_server/playbook.yml for PPC64LE platform
- Updated playbooks/sp_server/playbook_configure.yml to include sp_server_ppc64le host group
- Created comprehensive documentation in playbooks/sp_server/README.md

Minor Changes
-------------

- Enhanced platform support documentation in CHANGES_SUMMARY.md
- Added inventory configuration examples for PPC64LE hosts
- Documented PPC64LE-specific requirements and binary naming conventions

v1.0.0
======

Major Changes
-------------

- Added dsm_sysfile module to allow creation of dsm.sys file
- Added node module to create node
- Added nodes role to wrap around node module
- Added schedule module to create schedules
- Added schedules role to wrap around schedule module

Minor Changes
-------------

- Add ability to associate a schedule to a node in node module
- Add global_vars role as a 'meta dependency' role for including vars to the other roles.

Bugfixes
--------


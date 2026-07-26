## PR summary
Added comprehensive design documentation and user guides for IBM Storage Protect components including BA Client, Operations Center, Petascale, SP Server, and Storage Agent. Enhanced playbook structure with platform-specific implementations and added new modules for server installation and configuration.

**Fixes:** <!-- link to issue if applicable -->

## PR Checklist
Please make sure that your PR fulfills the following requirements:  
- [x] The commit message follows the Commit Message Guidelines in the CONTRIBUTING.md.
- [x] Tests for the changes have been added (for bug fixes / features)
- [x] Docs have been added / updated (for bug fixes / features)

## PR Type  
<!-- Please check the one that applies to this PR using "x". -->
- [ ] Bugfix
- [x] Feature
- [ ] Code style update (formatting, local variables)
- [ ] Refactoring (no functional changes, no api changes)
- [ ] New tests
- [ ] Build/CI related changes
- [x] Documentation content changes
- [ ] Other (please describe)

## What is the current behavior?  
The collection lacked comprehensive design documentation and user guides for various Storage Protect components. BA client installation playbooks were not organized by platform, and server installation/configuration modules were missing.

## What is the new behavior?  
**Documentation Added:**
- Design documents for BA Client, Operations Center, Petascale, SP Server, Storage Agent, and Blueprint Configuration Solution
- User guides for lifecycle management, data protection (DB2, SAP), security management, and operations

**New Features:**
- Platform-specific BA client playbooks (Linux/Windows) with proper organization
- Petascale deployment and monitoring playbooks with inventory examples
- SP Server installation and configuration modules (`sp_server.py`, `sp_server_configure.py`)
- BA Client installation module (`sp_baclient_install.py`)
- Orchestration module for BA server installation
- Python version installation role for compatibility with older systems
- Enhanced module utilities for BA client and SP server operations

**Playbook Enhancements:**
- Reorganized BA client playbooks under platform-specific directories
- Added server configuration playbook with Jinja2 templates
- Added petascale deployment with large-scale configuration variables

## Does this PR introduce a breaking change?    
- [ ] Yes
- [x] No

<!-- If this PR contains a breaking change, please describe the impact and migration path for existing applications below. -->

## Other information
- Total changes: 54 files modified, 21,786+ lines added
- All new modules follow the collection's naming conventions (CONVENTIONS.md)
- Documentation follows IBM Storage Protect 8.1.24 standards
- Tested against Ansible >=2.15.0 and Python 3.9+
- Includes comprehensive examples and variable templates for different deployment sizes (xsmall, small, medium, large)

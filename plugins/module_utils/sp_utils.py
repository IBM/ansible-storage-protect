"""
 Utilities for IBM Storage Protect Ansible modules.
"""
from ansible.module_utils.basic import AnsibleModule

class StorageProtectUtils:
    """
    Encapsulates common system checks for IBM Storage Protect modules.
    """
    def __init__(self, module: AnsibleModule):
        """
        Initializes the utility with an AnsibleModule instance.
        :param module: The AnsibleModule object executing the task.
        """
        self.module = module

    def server_component_check(self, imcl_path: str, package_prefix: str):
        """
        Verifies that the IBM Storage Protect Server component is installed via Installation Manager.

        :param imcl_path: Path to the IMCL executable (Installation Manager).
        :param package_prefix: Prefix used by IMCL to identify the Storage Agent package.
        """
        cmd = f"{imcl_path} listinstalledpackages"
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg=f"Failed to query IMCL packages: {err.strip() or out.strip()}")
        if package_prefix.lower() not in out.lower():
            self.module.fail_json(msg=f"Storage Agent package with prefix '{package_prefix}' not found.")

    def rpm_package_check(self, package_name: str):
        """
        Verifies that the specified RPM package is installed on the system.

        :param package_name: Name of the RPM package to verify (e.g., 'TIVsm-BA').
        """
        cmd = f"rpm -q {package_name}"
        rc, out, err = self.module.run_command(cmd)
        if rc != 0:
            self.module.fail_json(msg=f"BA client package '{package_name}' is not installed.")

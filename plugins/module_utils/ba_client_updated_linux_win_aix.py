# ba_client_utils.py
# -*- coding: utf-8 -*-
"""
IBM Storage Protect BA Client Utility Module
Supports Windows, Linux, and AIX
"""

import os
import platform
import shutil
from distutils.version import LooseVersion


class BAClientHelper:
    def __init__(self, module):
        self.module = module

    # -------------------------
    # Generic helpers
    # -------------------------
    def run_cmd(self, cmd, use_unsafe_shell=False, check_rc=True):
        rc, out, err = self.module.run_command(cmd, use_unsafe_shell=use_unsafe_shell)
        if check_rc and rc != 0:
            self.module.fail_json(msg=f"Command failed: {cmd}\nError: {err}")
        return rc, out, err

    def log(self, msg):
        if hasattr(self.module, "log"):
            try:
                self.module.log(msg)
                return
            except Exception:
                pass
        if hasattr(self.module, "warn"):
            self.module.warn(msg)
        else:
            print(f"LOG: {msg}")

    def file_exists(self, path):
        return os.path.exists(path)

    # -------------------------
    # OS detection
    # -------------------------
    def is_windows(self):
        return platform.system().lower().startswith("win")

    def is_aix(self):
        return platform.system().upper() == "AIX"

    def is_linux(self):
        return platform.system().lower() == "linux"

    # -------------------------
    # Version helpers
    # -------------------------
    def is_newer_version(self, target, current):
        try:
            return LooseVersion(target) > LooseVersion(current)
        except Exception:
            return target != current

    # -------------------------
    # Installed check
    # -------------------------
    def check_installed(self):
        if self.is_windows():
            cmd = 'reg query "HKLM\\SOFTWARE\\IBM\\ADSM\\CurrentVersion" /v PTF'
            rc, out, _ = self.run_cmd(cmd, check_rc=False)
            if rc == 0 and "PTF" in out:
                return True, out.strip().split()[-1]
            return False, None

        if self.is_aix():
            rc, _, _ = self.run_cmd(
                "lslpp -L tivoli.tsm.client.ba.64bit.base",
                check_rc=False
            )
            if rc == 0:
                return True, None
            return False, None

        # Linux
        rc, out, _ = self.run_cmd("rpm -q TIVsm-BA", check_rc=False)
        if rc == 0:
            ver = out.strip().replace("TIVsm-BA-", "").split(".x86_64")[0]
            return True, ver.replace("-", ".")
        return False, None

    # -------------------------
    # System prereqs
    # -------------------------
    def verify_system_prereqs(self):
        min_disk_mb = 1500

        if not self.is_windows():
            try:
                if os.geteuid() != 0:
                    self.module.fail_json(
                        msg="Root privileges required to install BA Client on Unix systems"
                    )
            except AttributeError:
                pass

        if self.is_windows():
            rc, _, _ = self.run_cmd(
                'whoami /groups | find "Administrators"', check_rc=False
            )
            if rc != 0:
                self.module.fail_json(
                    msg="Admin privileges required to install BA Client on Windows"
                )

        if self.is_aix():
            rc, out, _ = self.run_cmd("uname -p", check_rc=False)
            aix_arch = out.strip().lower() if rc == 0 else ""
            if "power" not in aix_arch:
                self.module.fail_json(
                    msg=f"Incompatible AIX architecture: {aix_arch}. POWER required."
                )
        elif self.is_linux():
            if platform.machine() != "x86_64":
                self.module.fail_json(
                    msg=f"Incompatible Linux architecture: {platform.machine()}"
                )

        check_path = "/usr" if self.is_aix() else "/"

        try:
            free_mb = shutil.disk_usage(check_path).free // (1024 * 1024)
        except Exception as e:
            self.module.fail_json(
                msg=f"Unable to determine disk space for {check_path}: {str(e)}"
            )

        if free_mb < min_disk_mb:
            self.module.fail_json(
                msg=(
                    f"Insufficient disk space on {check_path}. "
                    f"Required {min_disk_mb} MB, available {free_mb} MB"
                )
            )

    # -------------------------
    # Extraction
    # -------------------------
    def extract_package(self, src, dest):
        if not os.path.exists(src):
            self.module.fail_json(msg=f"Package source not found: {src}")

        os.makedirs(dest, exist_ok=True)

        if self.is_aix():
            cmd = f'cd "{dest}" && tar -xf "{src}"'
        else:
            cmd = f'tar -xf "{src}" -C "{dest}"'

        rc, _, err = self.run_cmd(cmd, use_unsafe_shell=True, check_rc=False)
        if rc != 0:
            self.module.fail_json(msg=f"Extraction failed: {err}")

        return dest

    # -------------------------
    # Install
    # -------------------------
    def install_ba_client(self, package_source, install_path, temp_dir):
        if self.is_windows():
            if package_source.lower().endswith(".msi"):
                cmd = f'msiexec.exe /i "{package_source}" /qn'
            else:
                cmd = f'"{package_source}" /S'
            self.run_cmd(cmd, use_unsafe_shell=True)
            return True

        if self.is_aix():
            extract_dir = "/usr/tsm_ba_aix_extract"
            self.extract_package(package_source, extract_dir)
            cmd = f'installp -acXYgd "{extract_dir}" all'
            self.run_cmd(cmd, use_unsafe_shell=True)
            self.module.warn("BA Client installed successfully on AIX")
            return True

        extract_dir = temp_dir
        rpm_dir = self.extract_package(package_source, extract_dir)
        cmd = f'cd "{rpm_dir}" && rpm -ivh --force --nodeps *.rpm'
        self.run_cmd(cmd, use_unsafe_shell=True)
        self.module.warn("BA Client installed successfully on Linux")
        return True

    # -------------------------
    # Verification
    # -------------------------
    def post_installation_verification(self, ba_client_version, state):
        installed, _ = self.check_installed()
        if not installed:
            self.module.fail_json(msg="BA Client installation verification failed")
        return {
            "is_installation_successful": True,
            "ba_client_version": ba_client_version
        }

    # -------------------------
    # Uninstall
    # -------------------------
    def uninstall_ba_client(self):
        if self.is_windows():
            self.run_cmd(
                'wmic product where "Name like \'%%Tivoli%%\'" call uninstall /nointeractive',
                check_rc=False
            )
            return True

        if self.is_aix():
            self.run_cmd(
                "installp -u "
                "tivoli.tsm.client.webgui "
                "tivoli.tsm.client.ba.64bit.image "
                "tivoli.tsm.client.ba.64bit.common "
                "tivoli.tsm.client.ba.64bit.base "
                "tivoli.tsm.client.api.64bit",
                check_rc=False
            )
            self.run_cmd(
                "installp -u tivoli.tsm.filepath.rte",
                check_rc=False
            )
            return True

        self.run_cmd("rpm -e TIVsm-BA", check_rc=False)
        return True

    # -------------------------
    # Upgrade
    # -------------------------
    def upgrade_ba_client(
        self,
        package_source,
        desired_version,
        install_path,
        ba_client_version,
        state,
        temp_dir,
    ):
        installed, installed_version = self.check_installed()
        if not installed:
            self.module.fail_json(msg="BA Client not installed; cannot upgrade")

        self.log(f"Upgrading BA Client from {installed_version} to {desired_version}")
        self.uninstall_ba_client()
        self.install_ba_client(package_source, install_path, temp_dir)
        return {"changed": True, "msg": "BA Client upgraded successfully"}
